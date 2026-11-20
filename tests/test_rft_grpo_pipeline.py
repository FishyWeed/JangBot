"""Unit and end-to-end tests for Trajectory Logging, RFT Generation and Local LoRA + GRPO."""

import json
from pathlib import Path
import pytest

from src.agent.llm import HybridLLMClient
from src.dialogue.manager import DialogueManager
from src.knowledge.repository import KnowledgeRepository
from src.knowledge.semantic_network import SemanticNetwork
from src.memory.trajectory import TrajectoryLogger, detect_feedback_signal
from src.settings import config
from src.training.local_lora import LocalLoRARuntime, detect_hardware_backend, strip_think_tags
from src.training.rewards import (
    expert_kb_accuracy_reward,
    mem0_adherence_reward,
    reasoning_structure_reward,
    verify_candidate,
)
from scripts.generate_rft_data import run_rft_generation
from scripts.train_grpo import run_lora_sft_and_grpo


def test_feedback_signal_detection():
    assert detect_feedback_signal("No, actually that's wrong, I meant the bamboo stick.") == -1.0
    assert detect_feedback_signal("That's incorrect, try again.") == -1.0
    assert detect_feedback_signal("Spot on, that makes sense!") == 1.0
    assert detect_feedback_signal("What wood is the janggu body made from?") is None


def test_trajectory_logger_integration_and_next_turn_correction():
    dialogue_manager = DialogueManager(KnowledgeRepository())
    traj_path = Path(config["training"]["trajectory_log"])
    session_id = "traj_test_session"
    user_id = "traj_test_user"

    try:
        # Turn 1: ask a verified janggu question (sets Mem0 + logs trajectory)
        r1 = dialogue_manager.process_message(
            session_id,
            "I am a beginner practicing gutgeori and my wrist gets tense. What wood is the janggu body made of?",
            user_id=user_id,
        )
        assert r1["status"] == "answered"

        # Turn 2: user corrects Turn 1 -> should back-patch Turn 1 feedback_score to -1.0
        dialogue_manager.process_message(
            session_id,
            "No, actually that's wrong — tell me about the bamboo yeolchae instead.",
            user_id=user_id,
        )

        # Turn 3: user confirms Turn 2 -> should back-patch Turn 2 feedback_score to +1.0
        dialogue_manager.process_message(
            session_id,
            "Spot on, great explanation!",
            user_id=user_id,
        )

        # Flush async logger worker before asserting disk contents
        dialogue_manager.agent.nodes.trajectory_logger.flush(timeout=5.0)
    finally:
        dialogue_manager.close()

    assert traj_path.exists()

    lines = [json.loads(ln) for ln in traj_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    session_recs = [r for r in lines if r.get("session_id") == session_id]
    assert len(session_recs) == 3

    turn1, turn2, turn3 = session_recs
    for rec in session_recs:
        assert "system_prompt" in rec and rec["system_prompt"]
        assert "mem0_retrieved_context" in rec and isinstance(rec["mem0_retrieved_context"], list)
        assert "user_query" in rec and rec["user_query"]
        assert "assistant_response" in rec and rec["assistant_response"]
        assert "tool_calls" in rec and isinstance(rec["tool_calls"], list)

    assert len(turn1["tool_calls"]) >= 1
    assert turn1["feedback_score"] == -1.0
    assert "wrong" in (turn1.get("feedback_note") or "").lower()
    assert turn2["feedback_score"] == 1.0
    assert turn3["feedback_score"] is None


def test_deterministic_rewards_and_verifier():
    repo = KnowledgeRepository()
    sn = SemanticNetwork(repo)
    facts = repo.get_facts_by_ids(["F03"])

    good_candidate = (
        "<think>\n"
        "Intent & Topic: ask_construction; entities=[ullimtong, paulownia_wood].\n"
        "Nuance & Sentiment: direct question from a learner noting wrist tension.\n"
        "Mem0 Constraints: User mentioned wrist tension when playing fast.\n"
        "Expert KB Rules: Ground strictly in verified fact [F03] using storyteller prose.\n"
        "</think>\n"
        "Inside the craftsperson's workshop, the hourglass body of the janggu—called the ullimtong—is carved "
        "from aged Paulownia wood, prized for its light weight and warm acoustic resonance. "
        "Keeping your wrist tension in mind, let the bamboo stick rebound lightly without stiffening your forearm. "
        "Would you like to explore how the narrow waist shapes the drum's tone next?"
    )
    verdict = verify_candidate(
        good_candidate,
        user_query="What wood is the janggu body made from?",
        mem0_context=["User mentioned wrist tension when playing fast."],
        expected_facts=facts,
        semantic_network=sn,
    )
    assert verdict["passed"] is True
    assert verdict["rewards"]["reasoning_structure"] >= 0.85
    assert verdict["rewards"]["mem0_adherence"] >= 0.90
    assert verdict["rewards"]["expert_kb_accuracy"] >= 0.60

    # Missing <think> block must fail reasoning_structure_reward
    no_think = "The janggu body is made from Paulownia wood."
    assert reasoning_structure_reward(no_think) == 0.0

    # Contradicting Mem0 wrist-tension constraint must score 0.0
    bad_mem0 = "<think>Intent: technique. Mem0: wrist tension. Rules: F03.</think>\nJust grip tightly and lock your wrist to play faster."
    assert mem0_adherence_reward(bad_mem0, ["User mentioned wrist tension."]) == 0.0

    # Banned cliché or raw bullet dump must fail expert_kb_accuracy_reward
    cliche_cand = "<think>Intent: construction.</think>\nThe janggu bridged both worlds and its ullimtong is carved from Paulownia wood."
    assert expert_kb_accuracy_reward(cliche_cand, facts) == 0.0
    bullet_cand = "<think>Intent: construction.</think>\n- Paulownia wood body.\n- Hourglass ullimtong shell."
    assert expert_kb_accuracy_reward(bullet_cand, facts) <= 0.2


def test_rft_generation_and_local_lora_grpo_hotswap(tmp_path: Path):
    # 1. Seed a tiny trajectory JSONL with one corrected turn
    traj_file = tmp_path / "trajectories.jsonl"
    logger = TrajectoryLogger(log_path=traj_file, enabled=True)
    tid = logger.log_turn(
        session_id="s1",
        user_id="u1",
        turn=1,
        system_prompt="You are Danbi, a Korean janggu tutor.",
        mem0_retrieved_context=["User is practicing gutgeori and mentioned wrist tension."],
        user_query="What wood makes up the body that creates the acoustic choke?",
        assistant_response="Old draft",
        tool_calls=[{"tool": "answer_relational_query", "args": {}, "fact_ids": ["F03", "F37"]}],
        fact_ids=["F03", "F37"],
    )
    logger.record_feedback(tid, -1.0, correction_text="No, actually give me more detail.")
    logger.flush(timeout=5.0)

    # 2. Run RFT generation (N=5, temperature=0.8)
    rft_file = tmp_path / "rft_verified.jsonl"
    rft_stats = run_rft_generation(
        trajectories_path=traj_file,
        output_path=rft_file,
        num_candidates=5,
        temperature=0.8,
        min_score=0.70,
        seed_from_kb=True,
        max_queries=6,
        max_per_query=2,
        seed=7,
    )
    assert rft_stats["queries_processed"] == 6
    assert rft_stats["candidates_generated"] == 30
    assert rft_stats["records_exported"] >= 6
    exported = [json.loads(ln) for ln in rft_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    for rec in exported:
        think_body, final_ans = strip_think_tags(rec["completion"])
        assert think_body and final_ans
        assert rec["total_reward"] >= 0.70

    # 3. Run miniature Local LoRA SFT (r=8, 30% replay buffer) + critic-free GRPO
    adapter_v1 = tmp_path / "adapter_v1"
    metrics = run_lora_sft_and_grpo(
        rft_data_path=rft_file,
        output_dir=adapter_v1,
        lora_rank=8,
        lora_alpha=16.0,
        replay_ratio=0.30,
        base_warmup_epochs=1,
        sft_epochs=1,
        grpo_steps=2,
        group_size=3,
        temperature=0.8,
        max_new_tokens=24,
        d_model=64,
        n_heads=4,
        n_layers=2,
        d_ff=128,
        max_seq_len=192,
        seed=7,
    )
    assert metrics["lora_rank"] == 8
    assert metrics["base_weight_max_drift"] == 0.0
    assert 0.20 <= metrics["actual_replay_fraction"] <= 0.40
    assert len(metrics["grpo_history"]) == 2
    for fname in ("adapter.pt", "base_model.pt", "tokenizer.json", "adapter_config.json", "training_metrics.json"):
        assert (adapter_v1 / fname).exists()

    # 4. Verify hardware detection and hot-swapping inside HybridLLMClient (zero Ollama, zero HF)
    hw = detect_hardware_backend()
    assert hw["backend"] in {"pytorch", "mlx"}

    client = HybridLLMClient()
    assert client.load_lora_adapter(adapter_v1) is True
    assert client.has_local_lora is True

    scores = client.score_candidates_with_lora(
        system_prompt="You are Danbi.",
        mem0_context=["User is a beginner."],
        user_query="What wood is the janggu made of?",
        candidates=[exported[0]["completion"], "Random unrelated noise"],
    )
    assert len(scores) == 2

    # Hot-swap a second adapter checkpoint into the live client
    adapter_v2 = tmp_path / "adapter_v2"
    run_lora_sft_and_grpo(
        rft_data_path=rft_file,
        output_dir=adapter_v2,
        lora_rank=8,
        lora_alpha=16.0,
        replay_ratio=0.30,
        base_warmup_epochs=0,
        sft_epochs=1,
        grpo_steps=1,
        group_size=2,
        max_new_tokens=16,
        base_checkpoint_dir=adapter_v1,
        seed=11,
    )
    assert client.hotswap_lora_adapter(adapter_v2) is True
    assert client.has_local_lora is True
    assert client.lora_adapter_path == adapter_v2
