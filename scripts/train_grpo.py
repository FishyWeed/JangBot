"""Local LoRA SFT + Self-Play GRPO trainer for JangBot (Danbi).

Executes a two-stage, 100% local training pipeline on laptop hardware (auto-detecting Apple
Silicon MLX vs PyTorch CUDA/MPS/CPU) with zero external APIs, zero Ollama and zero
HuggingFace downloads:

1. **LoRA SFT with 30% Expert Replay Buffer:**
   Mixes verified ``<think>...</think>`` + answer pairs from ``data/rft_verified.jsonl`` with
   a 30% replay buffer constructed directly from ``knowledge-base/janggu.db`` and
   ``tools/eval/golden_questions.yaml`` to prevent catastrophic forgetting. Base Transformer
   weights are frozen; only low-rank LoRA ``A``/``B`` matrices (``r=8`` or ``r=16``) train.

2. **Self-Play GRPO (Group Relative Policy Optimization, No Critic Model):**
   Samples groups of ``G`` completions per prompt at ``temperature=0.8``, scores each rollout
   with three deterministic Python reward functions (``reasoning_structure_reward``,
   ``mem0_adherence_reward``, ``expert_kb_accuracy_reward``), computes group-relative
   normalized advantages ``A_i = (r_i - mean(r)) / (std(r) + 1e-8)``, and optimizes the
   clipped GRPO surrogate objective with unbiased KL penalty against the frozen SFT reference
   adapter.

Outputs a hot-swappable adapter bundle under ``--output-dir`` (default ``models/danbi-lora``).
"""

import argparse
import copy
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import torch
import torch.nn.functional as F

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.knowledge.repository import KnowledgeRepository
from src.knowledge.semantic_network import SemanticNetwork
from src.settings import config
from src.training.local_lora import (
    LocalReasoningLM,
    LocalWordTokenizer,
    detect_hardware_backend,
)
from src.training.rewards import (
    expert_kb_accuracy_reward,
    mem0_adherence_reward,
    reasoning_structure_reward,
    resolve_expected_facts_for_query,
)

DEFAULT_SYSTEM_PROMPT = (
    "You are Danbi (he/him), a warm Korean janggu tutor and traditional storyteller. "
    "Reason explicitly inside <think>...</think> tags before giving a verified storyteller reply."
)


def _format_prompt(system_prompt: str, mem0_context: Sequence[str], user_query: str) -> str:
    mem_text = "; ".join(mem0_context) if mem0_context else "None"
    return (
        f"<system> {system_prompt}\n"
        f"<mem0> {mem_text}\n"
        f"<user> {user_query}\n"
        f"<assistant> "
    )


def load_rft_records(rft_path: Path) -> List[Dict[str, Any]]:
    """Load verified RFT `<think>` + answer training records from JSONL."""
    if not rft_path.exists():
        raise FileNotFoundError(
            f"Verified RFT dataset not found at {rft_path}. Run scripts/generate_rft_data.py first."
        )
    records: List[Dict[str, Any]] = []
    for raw_line in rft_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("user_query") and rec.get("completion"):
            records.append(rec)
    if not records:
        raise ValueError(f"No valid training pairs found in {rft_path}.")
    return records


def build_expert_replay_buffer(
    repository: KnowledgeRepository,
    semantic_network: SemanticNetwork,
    target_count: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """Create a local expert Q&A replay buffer directly from janggu.db verified facts."""
    verified_facts = repository.get_verified_facts()
    replay_pool: List[Dict[str, Any]] = []

    category_prompts = {
        "origin": "Where did the Korean janggu originate historically?",
        "history": "What do verified Korean historical records say about the janggu?",
        "construction": "How is the Korean janggu constructed from wood and hide?",
        "acoustics": "How do the shell cavity and drumheads shape janggu acoustics?",
        "technique": "How are the sticks and strokes played on the janggu?",
        "rhythm": "How do traditional Korean jangdan rhythms work on the janggu?",
        "cultural_use": "Where is the janggu played in Korean court and folk traditions?",
        "evolution": "How has the janggu evolved from ancient times to modern research?",
    }

    for fact in verified_facts:
        cat = fact.get("category") or "general"
        fid = fact["id"]
        stmt = fact["statement"].strip()
        q = category_prompts.get(cat, f"Tell me a verified fact about the janggu ({cat}).")
        concepts = semantic_network.extract_concepts_from_text(stmt)
        if concepts:
            q = f"What do verified records say about {concepts[0].replace('_', ' ')} on the janggu?"
        think = (
            "<think>\n"
            f"Intent & Topic: expert_replay ({cat}); concepts=[{', '.join(concepts[:3]) or 'janggu'}].\n"
            "Nuance & Sentiment: direct factual question.\n"
            "Mem0 Constraints: None recorded yet (no prior learner constraints).\n"
            f"Expert KB Rules: Ground strictly in verified fact [{fid}] with warm storyteller prose.\n"
            "</think>"
        )
        completion = (
            f"{think}\n"
            f"According to verified Korean janggu archives, {stmt} "
            "Would you like to explore a connected thread from this tradition next?"
        )
        replay_pool.append(
            {
                "source": "replay_buffer",
                "system_prompt": DEFAULT_SYSTEM_PROMPT,
                "mem0_retrieved_context": [],
                "user_query": q,
                "resolved_query": q,
                "expected_fact_ids": [fid],
                "completion": completion,
            }
        )

    rng.shuffle(replay_pool)
    if target_count <= 0:
        return []
    if len(replay_pool) >= target_count:
        return replay_pool[:target_count]
    out = list(replay_pool)
    while len(out) < target_count and replay_pool:
        out.append(rng.choice(replay_pool))
    return out[:target_count]


def mix_with_replay_buffer(
    rft_records: Sequence[Dict[str, Any]],
    replay_buffer: Sequence[Dict[str, Any]],
    replay_ratio: float,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """Combine RFT records with replay_buffer at the target replay fraction (e.g., 0.30)."""
    ratio = max(0.0, min(0.8, float(replay_ratio)))
    rft_list = list(rft_records)
    if ratio <= 0.0 or not replay_buffer:
        rng.shuffle(rft_list)
        return rft_list
    desired_replay = max(1, int(round(len(rft_list) * (ratio / (1.0 - ratio)))))
    rep_list = list(replay_buffer)
    chosen_replay: List[Dict[str, Any]] = []
    while len(chosen_replay) < desired_replay:
        rng.shuffle(rep_list)
        chosen_replay.extend(rep_list)
    mixed = rft_list + chosen_replay[:desired_replay]
    rng.shuffle(mixed)
    return mixed


def _completion_token_logprobs(
    model: LocalReasoningLM,
    prompt_ids: List[int],
    completion_ids: List[int],
    device: torch.device,
) -> torch.Tensor:
    """Return differentiable per-token log-probabilities over completion_ids."""
    max_len = model.cfg["max_seq_len"]
    full = (prompt_ids + completion_ids)[-max_len:]
    comp_len = min(len(completion_ids), len(full) - 1)
    if comp_len <= 0:
        return torch.zeros(1, device=device)
    inp = torch.tensor([full[:-1]], dtype=torch.long, device=device)
    tgt = torch.tensor([full[1:]], dtype=torch.long, device=device)
    logits = model(inp)
    log_probs = F.log_softmax(logits, dim=-1)
    return log_probs.gather(-1, tgt.unsqueeze(-1)).squeeze(-1)[0, -comp_len:]


def _sft_loss_for_pair(
    model: LocalReasoningLM,
    prompt_ids: List[int],
    completion_ids: List[int],
    device: torch.device,
) -> Optional[torch.Tensor]:
    """Compute causal LM cross-entropy loss strictly on completion tokens."""
    if not completion_ids:
        return None
    tok_lp = _completion_token_logprobs(model, prompt_ids, completion_ids, device)
    return -tok_lp.mean()


def _compute_grpo_reward(
    candidate: str,
    *,
    user_query: str,
    mem0_context: Sequence[str],
    expected_facts: Sequence[Dict[str, Any]],
    semantic_network: SemanticNetwork,
) -> Tuple[float, Dict[str, float]]:
    """Compute weighted deterministic GRPO reward from the 3 rule-based Python reward functions."""
    r_struct = reasoning_structure_reward(candidate)
    r_mem0 = mem0_adherence_reward(candidate, mem0_context, user_query=user_query)
    r_kb = expert_kb_accuracy_reward(
        candidate,
        expected_facts,
        user_query=user_query,
        semantic_network=semantic_network,
    )
    total = (0.30 * r_struct) + (0.25 * r_mem0) + (0.45 * r_kb)
    return float(total), {
        "reasoning_structure": r_struct,
        "mem0_adherence": r_mem0,
        "expert_kb_accuracy": r_kb,
    }


def run_lora_sft_and_grpo(
    *,
    rft_data_path: Path,
    output_dir: Path,
    lora_rank: int = 8,
    lora_alpha: float = 16.0,
    replay_ratio: float = 0.30,
    base_warmup_epochs: int = 1,
    sft_epochs: int = 3,
    grpo_steps: int = 6,
    group_size: int = 4,
    temperature: float = 0.8,
    lr: float = 2e-3,
    kl_beta: float = 0.05,
    clip_eps: float = 0.2,
    max_new_tokens: int = 96,
    d_model: int = 128,
    n_heads: int = 4,
    n_layers: int = 3,
    d_ff: int = 384,
    max_seq_len: int = 384,
    base_checkpoint_dir: Optional[Path] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """Run local LoRA SFT (with replay buffer) followed by critic-free self-play GRPO."""
    random.seed(seed)
    torch.manual_seed(seed)
    rng = random.Random(seed)

    hw = detect_hardware_backend()
    device = torch.device(hw["device"] if hw["backend"] == "pytorch" else "cpu")

    repository = KnowledgeRepository()
    semantic_network = SemanticNetwork(repository)
    rft_records = load_rft_records(rft_data_path)

    est_replay_size = max(10, int(round(len(rft_records) * (replay_ratio / max(1.0 - replay_ratio, 0.1)))))
    replay_buffer = build_expert_replay_buffer(repository, semantic_network, est_replay_size, rng)
    mixed_dataset = mix_with_replay_buffer(rft_records, replay_buffer, replay_ratio, rng)

    # Fit or load tokenizer on combined corpus
    if base_checkpoint_dir and (Path(base_checkpoint_dir) / "tokenizer.json").exists():
        tokenizer = LocalWordTokenizer.load(Path(base_checkpoint_dir) / "tokenizer.json")
    else:
        tokenizer = LocalWordTokenizer()
        corpus_texts = [
            _format_prompt(rec.get("system_prompt") or DEFAULT_SYSTEM_PROMPT, rec.get("mem0_retrieved_context") or [], rec["user_query"])
            + rec["completion"]
            for rec in mixed_dataset
        ]
        tokenizer.fit(corpus_texts, max_vocab=6000)

    # Initialize or load base local reasoning Transformer
    if base_checkpoint_dir and (Path(base_checkpoint_dir) / "adapter_config.json").exists():
        loaded_cfg = json.loads((Path(base_checkpoint_dir) / "adapter_config.json").read_text(encoding="utf-8"))
        mcfg = dict(loaded_cfg["model_config"])
        mcfg["lora_r"] = int(lora_rank)
        mcfg["lora_alpha"] = float(lora_alpha)
        model = LocalReasoningLM(**mcfg).to(device)
        base_pt = Path(base_checkpoint_dir) / "base_model.pt"
        if base_pt.exists():
            model.load_state_dict(torch.load(base_pt, map_location=device, weights_only=True), strict=False)
        run_warmup = False
    else:
        model = LocalReasoningLM(
            vocab_size=tokenizer.vocab_size,
            d_model=d_model,
            n_heads=n_heads,
            n_layers=n_layers,
            d_ff=d_ff,
            max_seq_len=max_seq_len,
            lora_r=lora_rank,
            lora_alpha=lora_alpha,
        ).to(device)
        run_warmup = base_warmup_epochs > 0

    # Pre-tokenize SFT dataset
    encoded_pairs: List[Tuple[List[int], List[int], Dict[str, Any]]] = []
    for rec in mixed_dataset:
        prompt_str = _format_prompt(
            rec.get("system_prompt") or DEFAULT_SYSTEM_PROMPT,
            rec.get("mem0_retrieved_context") or [],
            rec["user_query"],
        )
        p_ids = tokenizer.encode(prompt_str, add_bos=True)
        c_ids = tokenizer.encode(rec["completion"], add_eos=True)
        encoded_pairs.append((p_ids, c_ids, rec))

    # Optional short base warmup when bootstrapping a fresh local checkpoint from scratch
    warmup_losses: List[float] = []
    if run_warmup:
        model.unfreeze_all_for_base_warmup()
        model.train()
        base_opt = torch.optim.AdamW(model.parameters(), lr=lr * 1.5, weight_decay=0.01)
        for _ in range(base_warmup_epochs):
            rng.shuffle(encoded_pairs)
            ep_loss = 0.0
            n_steps = 0
            for p_ids, c_ids, _ in encoded_pairs:
                loss = _sft_loss_for_pair(model, p_ids, c_ids, device)
                if loss is None:
                    continue
                base_opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                base_opt.step()
                ep_loss += float(loss.item())
                n_steps += 1
            warmup_losses.append(round(ep_loss / max(n_steps, 1), 4))

    # Snapshot frozen base weights (excluding LoRA A/B) before LoRA-only fine-tuning
    frozen_base_state = {
        k: v.detach().cpu().clone()
        for k, v in model.state_dict().items()
        if "lora_A" not in k and "lora_B" not in k
    }

    # Stage 1: Freeze base weights, train ONLY LoRA adapters via SFT on RFT + 30% replay buffer
    trainable_params, total_params = model.freeze_base_enable_lora()
    lora_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(lora_params, lr=lr, weight_decay=0.01)

    sft_epoch_losses: List[float] = []
    model.train()
    for _ in range(max(1, sft_epochs)):
        rng.shuffle(encoded_pairs)
        ep_loss = 0.0
        n_steps = 0
        for p_ids, c_ids, _ in encoded_pairs:
            loss = _sft_loss_for_pair(model, p_ids, c_ids, device)
            if loss is None:
                continue
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(lora_params, 1.0)
            optimizer.step()
            ep_loss += float(loss.item())
            n_steps += 1
        sft_epoch_losses.append(round(ep_loss / max(n_steps, 1), 4))

    # Snapshot frozen post-SFT reference model (same base + SFT LoRA) for GRPO KL regularization
    ref_model = copy.deepcopy(model).to(device)
    ref_model.eval()
    for p in ref_model.parameters():
        p.requires_grad = False

    # Stage 2: Critic-free Self-Play GRPO over prompts from RFT + replay
    grpo_optimizer = torch.optim.AdamW(lora_params, lr=lr * 0.5, weight_decay=0.0)
    grpo_history: List[Dict[str, float]] = []

    for step_idx in range(max(0, grpo_steps)):
        rec = rng.choice(rft_records)
        sys_prompt = rec.get("system_prompt") or DEFAULT_SYSTEM_PROMPT
        mem0_ctx = list(rec.get("mem0_retrieved_context") or [])
        user_q = rec["user_query"]
        resolved_q = rec.get("resolved_query") or user_q
        expected_facts = resolve_expected_facts_for_query(
            resolved_q,
            rec.get("expected_fact_ids"),
            repository,
            semantic_network=semantic_network,
        )
        prompt_ids = tokenizer.encode(_format_prompt(sys_prompt, mem0_ctx, user_q), add_bos=True)

        # Sample G group completions at temperature=0.8 under current policy (eval mode for sampling)
        model.eval()
        group_comp_ids: List[List[int]] = []
        group_rewards: List[float] = []
        old_mean_lps: List[float] = []
        ref_mean_lps: List[float] = []

        for g_idx in range(max(2, group_size)):
            if g_idx == 0:
                # Anchor 1 rollout in the group to the verified RFT completion so group variance stays informative
                comp_ids = tokenizer.encode(rec["completion"], add_eos=True)
                cand_text = rec["completion"]
            else:
                comp_ids = model.generate(
                    prompt_ids,
                    eos_id=tokenizer.eos_id,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    device=device,
                )
                if not comp_ids:
                    comp_ids = [tokenizer.eos_id]
                cand_text = tokenizer.decode(comp_ids, skip_special=False)

            reward_val, _ = _compute_grpo_reward(
                cand_text,
                user_query=resolved_q,
                mem0_context=mem0_ctx,
                expected_facts=expected_facts,
                semantic_network=semantic_network,
            )
            with torch.no_grad():
                old_lp = float(_completion_token_logprobs(model, prompt_ids, comp_ids, device).mean().item())
                ref_lp = float(_completion_token_logprobs(ref_model, prompt_ids, comp_ids, device).mean().item())

            group_comp_ids.append(comp_ids)
            group_rewards.append(reward_val)
            old_mean_lps.append(old_lp)
            ref_mean_lps.append(ref_lp)

        # Group-relative advantage normalization (critic-free)
        r_tensor = torch.tensor(group_rewards, dtype=torch.float32, device=device)
        mean_r = r_tensor.mean()
        std_r = r_tensor.std(unbiased=False)
        advantages = (r_tensor - mean_r) / (std_r + 1e-8)

        # Policy update with clipped GRPO objective + Schulman unbiased KL penalty
        model.train()
        grpo_optimizer.zero_grad()
        step_losses: List[torch.Tensor] = []
        step_kls: List[float] = []

        for comp_ids, adv, old_lp, ref_lp in zip(group_comp_ids, advantages, old_mean_lps, ref_mean_lps):
            cur_lp = _completion_token_logprobs(model, prompt_ids, comp_ids, device).mean()
            log_ratio = torch.clamp(cur_lp - old_lp, min=-5.0, max=5.0)
            ratio = torch.exp(log_ratio)
            unclipped = ratio * adv
            clipped = torch.clamp(ratio, 1.0 - clip_eps, 1.0 + clip_eps) * adv
            surrogate = torch.minimum(unclipped, clipped)

            ref_diff = torch.clamp(ref_lp - cur_lp, min=-5.0, max=5.0)
            kl_est = torch.exp(ref_diff) - ref_diff - 1.0
            step_kls.append(float(kl_est.detach().item()))
            step_losses.append(-(surrogate - (kl_beta * kl_est)))

        batch_loss = torch.stack(step_losses).mean()
        batch_loss.backward()
        torch.nn.utils.clip_grad_norm_(lora_params, 1.0)
        grpo_optimizer.step()

        grpo_history.append(
            {
                "step": step_idx + 1,
                "loss": round(float(batch_loss.item()), 5),
                "mean_reward": round(float(mean_r.item()), 4),
                "max_reward": round(float(r_tensor.max().item()), 4),
                "mean_kl": round(sum(step_kls) / max(len(step_kls), 1), 5),
            }
        )

    # Verify frozen base weights did NOT drift during LoRA SFT + GRPO
    base_drift = 0.0
    cur_state = model.state_dict()
    for k, orig_t in frozen_base_state.items():
        diff = float((cur_state[k].detach().cpu() - orig_t).abs().max().item())
        if diff > base_drift:
            base_drift = diff

    # Persist adapter bundle cleanly
    output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer.save(output_dir / "tokenizer.json")
    torch.save(frozen_base_state, output_dir / "base_model.pt")
    torch.save(model.lora_state_dict(), output_dir / "adapter.pt")

    adapter_cfg = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hardware": hw,
        "lora_rank": int(lora_rank),
        "lora_alpha": float(lora_alpha),
        "replay_ratio": float(replay_ratio),
        "rft_records": len(rft_records),
        "replay_records": len(mixed_dataset) - len(rft_records),
        "trainable_params": trainable_params,
        "total_params": total_params,
        "trainable_pct": round(100.0 * trainable_params / max(total_params, 1), 2),
        "base_weight_max_drift": round(base_drift, 8),
        "model_config": model.cfg,
    }
    (output_dir / "adapter_config.json").write_text(json.dumps(adapter_cfg, indent=2), encoding="utf-8")

    metrics = {
        "hardware": hw,
        "output_dir": str(output_dir),
        "lora_rank": int(lora_rank),
        "trainable_params": trainable_params,
        "total_params": total_params,
        "trainable_pct": adapter_cfg["trainable_pct"],
        "base_weight_max_drift": adapter_cfg["base_weight_max_drift"],
        "rft_count": len(rft_records),
        "replay_count": len(mixed_dataset) - len(rft_records),
        "actual_replay_fraction": round((len(mixed_dataset) - len(rft_records)) / max(len(mixed_dataset), 1), 3),
        "base_warmup_losses": warmup_losses,
        "sft_epoch_losses": sft_epoch_losses,
        "grpo_history": grpo_history,
    }
    (output_dir / "training_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    train_cfg = config.get("training", {})
    parser = argparse.ArgumentParser(
        description="Local LoRA SFT (with 30% expert replay buffer) + critic-free Self-Play GRPO trainer."
    )
    parser.add_argument(
        "--rft-data",
        type=Path,
        default=BASE_DIR / train_cfg.get("rft_output", "data/rft_verified.jsonl"),
        help="Input verified RFT JSONL file (default: data/rft_verified.jsonl).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BASE_DIR / train_cfg.get("lora_adapter_path", "models/danbi-lora"),
        help="Directory to write LoRA adapter bundle (default: models/danbi-lora).",
    )
    parser.add_argument(
        "--lora-rank",
        type=int,
        default=int(train_cfg.get("lora_rank", 8)),
        choices=[4, 8, 16],
        help="Low-rank LoRA rank r (recommended: 8 or 16; default: 8).",
    )
    parser.add_argument("--lora-alpha", type=float, default=16.0, help="LoRA scaling alpha (default: 16.0).")
    parser.add_argument(
        "--replay-ratio",
        type=float,
        default=float(train_cfg.get("replay_ratio", 0.30)),
        help="Fraction of original expert KB replay buffer mixed into SFT (default: 0.30).",
    )
    parser.add_argument("--base-warmup-epochs", type=int, default=1, help="Base warmup epochs when training from scratch (default: 1).")
    parser.add_argument("--sft-epochs", type=int, default=3, help="LoRA SFT epochs (default: 3).")
    parser.add_argument("--grpo-steps", type=int, default=6, help="Self-play GRPO optimization steps (default: 6).")
    parser.add_argument("--group-size", type=int, default=4, help="Completions sampled per prompt in GRPO (default: 4).")
    parser.add_argument("--temperature", type=float, default=0.8, help="Rollout sampling temperature (default: 0.8).")
    parser.add_argument("--lr", type=float, default=2e-3, help="AdamW learning rate for LoRA parameters (default: 2e-3).")
    parser.add_argument("--kl-beta", type=float, default=0.05, help="KL regularization penalty weight vs SFT reference (default: 0.05).")
    parser.add_argument("--clip-eps", type=float, default=0.2, help="GRPO policy ratio clip epsilon (default: 0.2).")
    parser.add_argument("--max-new-tokens", type=int, default=96, help="Max tokens generated per GRPO rollout (default: 96).")
    parser.add_argument("--base-checkpoint", type=Path, default=None, help="Optional existing local base checkpoint directory.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42).")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    metrics = run_lora_sft_and_grpo(
        rft_data_path=args.rft_data,
        output_dir=args.output_dir,
        lora_rank=args.lora_rank,
        lora_alpha=args.lora_alpha,
        replay_ratio=args.replay_ratio,
        base_warmup_epochs=args.base_warmup_epochs,
        sft_epochs=args.sft_epochs,
        grpo_steps=args.grpo_steps,
        group_size=args.group_size,
        temperature=args.temperature,
        lr=args.lr,
        kl_beta=args.kl_beta,
        clip_eps=args.clip_eps,
        max_new_tokens=args.max_new_tokens,
        base_checkpoint_dir=args.base_checkpoint,
        seed=args.seed,
    )
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
