"""Tests for persistent Mem0 / local long-term user memory extraction and updates."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from src.knowledge.repository import KnowledgeRepository
from src.memory.long_term import LongTermMemoryManager
from src.dialogue.manager import DialogueManager


def test_cross_session_memory_persistence_and_personalization():
    """User facts extracted in session A should personalize replies in session B."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        mem_db = tmp_dir / "memories.db"
        ckpt_db = tmp_dir / "checkpoints.db"
        repo = KnowledgeRepository()

        # Session A: user shares skill level, instrument, jangdan and wrist tension
        dm1 = DialogueManager(
            repo,
            memory_manager=LongTermMemoryManager(local_db_path=mem_db),
            checkpoints_db_path=ckpt_db,
        )
        r1 = dm1.process_message(
            "session_a",
            "I'm a beginner, I own a wooden janggu, practicing Gutgeori, and my wrist has tension.",
            user_id="mina",
        )
        assert r1["status"] == "answered"
        saved = dm1.get_user_memories("mina")
        texts = " ".join(m["memory"].lower() for m in saved)
        assert "beginner" in texts
        assert "paulownia" in texts or "wooden" in texts
        assert "gutgeori" in texts
        assert "wrist tension" in texts
        dm1.close()

        # Session B (completely new thread_id + fresh DialogueManager instance)
        dm2 = DialogueManager(
            repo,
            memory_manager=LongTermMemoryManager(local_db_path=mem_db),
            checkpoints_db_path=ckpt_db,
        )
        try:
            r2 = dm2.process_message(
                "session_b",
                "How do I play the janggu?",
                user_id="mina",
            )
            assert r2["status"] == "answered"
            assert any("wrist tension" in m.lower() for m in r2["memories_used"])
            assert "wrist tension" in r2["reply"].lower()

            # Separate user_id should not inherit Mina's memories
            assert dm2.get_user_memories("other_student") == []
        finally:
            dm2.close()


def test_memory_deduplication_and_update():
    """Newer skill level updates/replaces earlier conflicting skill level fact."""
    with tempfile.TemporaryDirectory() as tmp:
        mem = LongTermMemoryManager(local_db_path=Path(tmp) / "memories.db")
        mem.add([{"role": "user", "content": "I am a beginner learning janggu"}], user_id="jun")
        mem.add([{"role": "user", "content": "I have played for a year and feel intermediate now"}], user_id="jun")

        all_mems = mem.get_all("jun")
        skill_mems = [m["memory"] for m in all_mems if m.get("slot") == "skill_level"]
        assert len(skill_mems) == 1
        assert "intermediate" in skill_mems[0].lower()


def test_mem0_client_delegation_signature():
    """Verify live Mem0 bridge calls search(filters=...) and add(..., user_id=...)."""
    with tempfile.TemporaryDirectory() as tmp:
        mem = LongTermMemoryManager(local_db_path=Path(tmp) / "memories.db")
        mock_mem0 = MagicMock()
        mock_mem0.search.return_value = {"results": [{"id": "m1", "memory": "Practicing Hwimori"}]}
        mock_mem0.add.return_value = {"results": [{"id": "m2", "memory": "Owns wooden janggu"}]}
        mem._mem0 = mock_mem0

        found = mem.search("how to play faster", user_id="user_42")
        mock_mem0.search.assert_called_once_with("how to play faster", top_k=mem.top_k, filters={"user_id": "user_42"})
        assert any(item["memory"] == "Practicing Hwimori" for item in found)

        added = mem.add([{"role": "user", "content": "Hello"}], user_id="user_42")
        mock_mem0.add.assert_called_once()
        assert mock_mem0.add.call_args.kwargs["user_id"] == "user_42"
        assert any(item["memory"] == "Owns wooden janggu" for item in added)
