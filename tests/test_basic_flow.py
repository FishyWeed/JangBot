"""Unit tests for JangBot dialogue and inference engine."""

from src.knowledge.repository import KnowledgeRepository
from src.dialogue.manager import DialogueManager


def test_greeting_and_social_flow():
    """Verify greeting and social exchange."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_session_1"

    res1 = manager.process_message(session_id, "hello")
    assert "Hi, I'm Danbi" in res1["reply"]

    res2 = manager.process_message(session_id, "I am doing well")
    assert "glad to hear that" in res2["reply"].lower()


def test_construction_query():
    """Verify construction facts query."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_session_2"

    res = manager.process_message(session_id, "What materials are used to make the janggu?")
    assert res["status"] == "answered"
    assert "hourglass" in res["reply"].lower() or "cowhide" in res["reply"].lower()


def test_typo_correction():
    """Verify typo correction handling."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_session_3"

    res = manager.process_message(session_id, "How do you play the jangu?")
    assert res["status"] == "answered"
    assert "stick" in res["reply"].lower() or "yeolchae" in res["reply"].lower()


def test_off_topic_deflection():
    """Verify off-topic question rejection."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_session_4"

    res = manager.process_message(session_id, "What is the weather in London today?")
    assert res["status"] == "off_topic"


def test_source_explanation():
    """Verify source citation flow."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_session_5"

    manager.process_message(session_id, "What sticks are used to play the drum?")
    res = manager.process_message(session_id, "How do you know that?")
    assert res["status"] == "answered"
    assert "National Gugak Center" in res["reply"] or "The Met" in res["reply"]
