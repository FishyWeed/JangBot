"""Unit tests for casual human language, shorthand and follow-ups."""

from src.knowledge.repository import KnowledgeRepository
from src.dialogue.manager import DialogueManager
from src.nlp.preprocessor import NLPPreprocessor


def test_short_form_expansion():
    """Verify short-form expansion in preprocessor."""
    preprocessor = NLPPreprocessor()
    expanded = preprocessor.clean_text("wat mats r used for the lh side")
    assert "what is" in expanded
    assert "materials" in expanded
    assert "left head" in expanded


def test_casual_playing_question():
    """Verify casual phrasing for playing technique."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_casual_1"

    res = manager.process_message(session_id, "how do u play it")
    assert res["status"] == "answered"
    assert "yeolchae" in res["reply"].lower() or "stick" in res["reply"].lower()


def test_casual_construction_with_short_forms():
    """Verify casual materials query."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_casual_2"

    res = manager.process_message(session_id, "wat mats r used for the left side")
    assert res["status"] == "answered"
    assert "cowhide" in res["reply"].lower() or "gungpyeon" in res["reply"].lower()


def test_conversational_follow_up():
    """Verify context-aware short follow-up."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_casual_3"

    res1 = manager.process_message(session_id, "Tell me about the construction of the drum")
    assert res1["status"] == "answered"

    res2 = manager.process_message(session_id, "and the right side?")
    assert res2["status"] == "answered"
    assert "horsehide" in res2["reply"].lower() or "chaepyeon" in res2["reply"].lower()
