"""Tests ensuring Danbi varies responses and never emits repeated replies or banned clichés."""

import tempfile
from pathlib import Path
from src.knowledge.repository import KnowledgeRepository
from src.memory.long_term import LongTermMemoryManager
from src.dialogue.manager import DialogueManager
from src.dialogue.variations import extract_opener, pick_greeting


def _isolated_dm(tmp: Path) -> DialogueManager:
    repo = KnowledgeRepository()
    mem = LongTermMemoryManager(local_db_path=tmp / "mem.db")
    return DialogueManager(repo, memory_manager=mem, checkpoints_db_path=tmp / "ckpt.db")


def test_court_or_folk_no_longer_uses_cliche_and_varies_across_sessions():
    """Follow-up answers must never repeat or emit the old 'bridged both worlds' cliché."""
    with tempfile.TemporaryDirectory() as tmp:
        dm = _isolated_dm(Path(tmp))
        try:
            follow_ups = []
            origins = []
            for idx in range(4):
                sid = f"var_sess_{idx}"
                r1 = dm.process_message(sid, "Where did the janggu originate?", user_id=f"u_{idx}")
                r2 = dm.process_message(sid, "yes", user_id=f"u_{idx}")
                assert "bridged both worlds" not in r2["reply"].lower()
                assert r2["status"] == "answered"
                origins.append(r1["reply"])
                follow_ups.append(r2["reply"])

            assert len(set(origins)) == 4
            assert len(set(follow_ups)) == 4
            assert len({extract_opener(r) for r in follow_ups}) >= 3
        finally:
            dm.close()


def test_repeated_queries_never_repeat_within_or_across_categories():
    """Asking the same prompt repeatedly across turns produces unique non-repeating replies."""
    prompts = [
        "hello",
        "Tell me about Paulownia wood construction of the ullimtong",
        "How do you play the janggu in court vs folk?",
        "Why are janggu overtones inharmonic?",
        "What are the jangdan rhythmic cycles?",
        "How much does a wooden janggu weigh in kilograms?",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        dm = _isolated_dm(Path(tmp))
        try:
            for p_idx, prompt in enumerate(prompts):
                replies = []
                for turn in range(4):
                    res = dm.process_message(f"rep_{p_idx}_{turn}", prompt, user_id="u_rep")
                    replies.append(res["reply"])
                assert len(set(replies)) == 4, f"Duplicate reply detected for prompt: {prompt}"
        finally:
            dm.close()


def test_intra_session_repeated_question_and_source_citations_vary():
    """Repeating questions and source queries inside one thread avoids identical phrasing."""
    with tempfile.TemporaryDirectory() as tmp:
        dm = _isolated_dm(Path(tmp))
        try:
            r1 = dm.process_message("same_thread", "What sticks play the janggu?", user_id="u_same")
            r2 = dm.process_message("same_thread", "What sticks play the janggu?", user_id="u_same")
            assert r1["reply"] != r2["reply"]
            assert extract_opener(r1["reply"]) != extract_opener(r2["reply"])

            s1 = dm.process_message("same_thread", "How do you know that?", user_id="u_same")
            s2 = dm.process_message("same_thread", "What are your sources?", user_id="u_same")
            assert s1["reply"] != s2["reply"]
            assert "verified" in s1["reply"].lower() and "verified" in s2["reply"].lower()

            g1 = pick_greeting("Danbi")
            g2 = pick_greeting("Danbi")
            g3 = pick_greeting("Danbi")
            assert len({g1, g2, g3}) == 3
            assert all("Hi, I'm Danbi" in g for g in (g1, g2, g3))
        finally:
            dm.close()
