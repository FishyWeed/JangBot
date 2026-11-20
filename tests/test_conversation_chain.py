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


def test_conversational_ping_pong_fragments_and_followups():
    """Verify greetings, half-sentences, single words, ordinals and direct follow-ups never break."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    sid = "test_pingpong_fragments"

    turns = [
        ("Hey Danbi!", "social", ("hi, i'm danbi",)),
        ("Doing pretty well, I am curious where the janggu even came from originally", "answered", ("idakka", "goryeosa")),
        ("royal court first!", "answered", ("jeongak", "jongmyo")),
        ("yes", "answered", ("nongak", "village")),
        ("how are the hides tanned?", "answered", ("collagen", "micron")),
        ("dog skin?!", "answered", ("doghide", "chaepyeon")),
        ("wait what about the other side?", "answered", ("gungpyeon", "cowhide")),
        ("museum conservation?", "answered", ("sr-μct", "p-xrf")),
        ("Met Museum?", "answered", ("metropolitan museum", "19th-century")),
        ("and Jungjungmori?", "answered", ("jungjungmori", "12-beat")),
        ("and Jongmyo Jeryeak?", "answered", ("jongmyo jeryeak", "jeongak")),
        ("no thanks, let's check out Daechwita", "answered", ("daechwita", "yonggo")),
        ("whoa really? what about modern ROKA bands?", "answered", ("roka", "jajinmori")),
        ("what about weddings?", "fallback", ("don't have verified information",)),
        ("awesome, thanks for all the stories Danbi!", "answered", ("janggu",)),
    ]

    seen_replies = set()
    for msg, expected_status, expected_terms in turns:
        res = manager.process_message(sid, msg)
        reply_low = res["reply"].lower()
        assert res["status"] == expected_status, f"Turn {msg!r}: expected {expected_status}, got {res['status']} -> {res['reply']!r}"
        assert any(t in reply_low for t in expected_terms), f"Turn {msg!r}: missing {expected_terms} in {res['reply']!r}"
        assert reply_low not in seen_replies, f"Duplicate reply on {msg!r}"
        seen_replies.add(reply_low)
