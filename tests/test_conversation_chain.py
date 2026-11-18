"""Tests verifying multi-turn conversational follow-up chains."""

from src.knowledge.repository import KnowledgeRepository
from src.dialogue.manager import DialogueManager


def test_origin_to_technique_followup_chain():
    """Verify natural multi-turn conversational follow-up chain."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_chain_user"

    # Turn 1: Origins
    res1 = manager.process_message(session_id, "who created it")
    assert res1["status"] == "answered"
    assert "idakka" in res1["reply"].lower() or "silla" in res1["reply"].lower()
    assert "court" in res1["reply"].lower() and "village" in res1["reply"].lower()

    # Turn 2: Affirmation ("yes")
    res2 = manager.process_message(session_id, "yes")
    assert res2["status"] == "answered"
    assert "jeongak" in res2["reply"].lower() or "court" in res2["reply"].lower()
    assert "nongak" in res2["reply"].lower() or "village" in res2["reply"].lower()
    assert "playing technique" in res2["reply"].lower()

    # Turn 3: User follows up with "tell me about the playing technique"
    res3 = manager.process_message(session_id, "tell me about the playing technique")
    assert res3["status"] == "answered"
    assert "jwa-sik" in res3["reply"].lower() or "cross-legged" in res3["reply"].lower()
    assert "ip-sik" in res3["reply"].lower() or "standing" in res3["reply"].lower()

    # Turn 4: User follows up with "yes" for sticks / strokes
    res4 = manager.process_message(session_id, "yes")
    assert res4["status"] == "answered"
    assert "yeolchae" in res4["reply"].lower()
    assert "gungchae" in res4["reply"].lower()

    # Turn 5: User asks for source explanation
    res5 = manager.process_message(session_id, "How do you know that?")
    assert res5["status"] == "answered"
    assert "verified" in res5["reply"].lower()
    assert "National Gugak Center" in res5["reply"] or "The Met" in res5["reply"]


def test_folk_choice_branch():
    """Verify selecting 'village' directly from the court or village offer."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_village_branch"

    res1 = manager.process_message(session_id, "Where does the janggu come from?")
    assert res1["status"] == "answered"

    res2 = manager.process_message(session_id, "village")
    assert res2["status"] == "answered"
    assert "nongak" in res2["reply"].lower()
    assert "harvest" in res2["reply"].lower() or "farmers" in res2["reply"].lower()
