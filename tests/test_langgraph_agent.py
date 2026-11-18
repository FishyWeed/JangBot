"""Tests for LangGraph multi-turn orchestration, checkpointing and guardrails."""

import tempfile
from pathlib import Path
from src.settings import config
from src.knowledge.repository import KnowledgeRepository
from src.memory.long_term import LongTermMemoryManager
from src.dialogue.manager import DialogueManager


def _build_isolated_manager(tmp_dir: Path) -> DialogueManager:
    """Create DialogueManager backed by isolated temporary SQLite stores."""
    repo = KnowledgeRepository()
    mem = LongTermMemoryManager(local_db_path=tmp_dir / "mem.db")
    return DialogueManager(
        repo,
        memory_manager=mem,
        checkpoints_db_path=tmp_dir / "checkpoints.db",
    )


def test_pronoun_resolution_after_jangdan():
    """Resolve 'that' after discussing Gutgeori jangdan into tempo guidance."""
    with tempfile.TemporaryDirectory() as tmp:
        dm = _build_isolated_manager(Path(tmp))
        try:
            r1 = dm.process_message("sess_lg_1", "Tell me about Gutgeori jangdan", user_id="u_lg_1")
            assert r1["status"] == "answered"
            assert "gutgeori" in r1["reply"].lower()

            r2 = dm.process_message("sess_lg_1", "how do I play that faster?", user_id="u_lg_1")
            assert r2["status"] == "answered"
            assert "gutgeori" in r2["resolved_query"].lower()
            assert "deong" in r2["reply"].lower() or "yeolchae" in r2["reply"].lower()
        finally:
            dm.close()


def test_complementary_head_and_pronoun_resolution():
    """Resolve 'the other side' after discussing bukpyeon/gungpyeon."""
    with tempfile.TemporaryDirectory() as tmp:
        dm = _build_isolated_manager(Path(tmp))
        try:
            r1 = dm.process_message("sess_lg_2", "Tell me about the bukpyeon head", user_id="u_lg_2")
            assert r1["status"] == "answered"
            assert "cowhide" in r1["reply"].lower()

            r2 = dm.process_message("sess_lg_2", "what about the other side?", user_id="u_lg_2")
            assert r2["status"] == "answered"
            assert "chaepyeon" in r2["resolved_query"].lower()
            assert "horsehide" in r2["reply"].lower() or "chaepyeon" in r2["reply"].lower()
        finally:
            dm.close()


def test_sqlite_checkpoint_persists_across_restarts():
    """Verify LangGraph SqliteSaver restores prior turn state across fresh instances."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        dm1 = _build_isolated_manager(tmp_dir)
        r1 = dm1.process_message("persist_thread_1", "who created the janggu?", user_id="u_ckpt")
        assert r1["status"] == "answered"
        assert "royal court" in r1["reply"].lower()
        dm1.close()

        # Re-open a brand new DialogueManager pointing to the same SQLite checkpoints file
        dm2 = _build_isolated_manager(tmp_dir)
        try:
            r2 = dm2.process_message("persist_thread_1", "yes", user_id="u_ckpt")
            assert r2["status"] == "answered"
            assert "jeongak" in r2["reply"].lower()
            assert "nongak" in r2["reply"].lower()
        finally:
            dm2.close()


def test_mid_conversation_off_topic_guardrail():
    """Ensure unrelated questions mid-conversation still trigger strict off-topic refusal."""
    with tempfile.TemporaryDirectory() as tmp:
        dm = _build_isolated_manager(Path(tmp))
        try:
            r1 = dm.process_message("sess_guard", "Tell me about the ullimtong", user_id="u_guard")
            assert r1["status"] == "answered"

            r2 = dm.process_message("sess_guard", "What is the weather in Tokyo?", user_id="u_guard")
            assert r2["status"] == "off_topic"
            assert r2["reply"] == config["bot"]["off_topic_message"]
        finally:
            dm.close()


def test_war_and_unverified_topic_not_hijacked_by_origin():
    """Specific unverified questions (war/battle) after origin must not dump Silk Road origin."""
    with tempfile.TemporaryDirectory() as tmp:
        dm = _build_isolated_manager(Path(tmp))
        try:
            r1 = dm.process_message("sess_war", "who created the janggu?", user_id="u_war")
            assert r1["status"] == "answered"

            r2 = dm.process_message(
                "sess_war",
                "I wanna know if it was used in war and now it might have affected to tide of battle",
                user_id="u_war",
            )
            assert r2["status"] == "answered"
            assert "idakka" not in r2["reply"].lower()
            assert "jajinmori" in r2["reply"].lower()
            assert "F24" in r2["fact_ids"]
            assert "F12" not in r2["fact_ids"]
        finally:
            dm.close()


def test_completely_uncovered_domain_detail_returns_honest_fallback():
    """Questions about an uncovered janggu attribute should report the knowledge gap honestly."""
    with tempfile.TemporaryDirectory() as tmp:
        dm = _build_isolated_manager(Path(tmp))
        try:
            r = dm.process_message("sess_gap", "How much does a wooden janggu weigh in kilograms?", user_id="u_gap")
            assert r["status"] == "fallback"
            assert config["bot"]["fallback_message"].lower() in r["reply"].lower()
        finally:
            dm.close()
