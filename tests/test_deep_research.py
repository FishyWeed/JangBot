"""Unit tests for newly imported deep research facts."""

from src.knowledge.repository import KnowledgeRepository
from src.dialogue.manager import DialogueManager


def test_ullimtong_wood():
    """Verify Paulownia coreana body facts."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_dr_1"

    res = manager.process_message(session_id, "What wood is the ullimtong made of?")
    assert res["status"] == "answered"
    assert "paulownia" in res["reply"].lower()


def test_strokes_taxonomy():
    """Verify stroke taxonomy facts."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_dr_2"

    res = manager.process_message(session_id, "What are the strokes of the janggu?")
    assert res["status"] == "answered"
    assert "deong" in res["reply"].lower()
    assert "gideok" in res["reply"].lower() or "gi-deok" in res["reply"].lower()


def test_jangdan_rhythms():
    """Verify rhythmic cycles facts."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_dr_3"

    res = manager.process_message(session_id, "Tell me about the jangdan rhythmic cycles")
    assert res["status"] == "answered"
    assert "jinyangjo" in res["reply"].lower()
    assert "hwimori" in res["reply"].lower()


def test_chuimsae_vocal_cries():
    """Verify chuimsae facts."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_dr_4"

    res = manager.process_message(session_id, "What are chuimsae vocal cries?")
    assert res["status"] == "answered"
    assert "eolssigu" in res["reply"].lower() or "jota" in res["reply"].lower()


def test_historical_treatises():
    """Verify Akhak Gwebeom and Goryeosa facts."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)
    session_id = "test_dr_5"

    res = manager.process_message(session_id, "What is recorded in the Akhak Gwebeom?")
    assert res["status"] == "answered"
    assert "1493" in res["reply"]
    assert "galgo" in res["reply"].lower()


def test_etymology_and_archaeology():
    """Verify newly imported etymology and Three Kingdoms archaeology facts."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)

    r_etym = manager.process_message("test_dr_6", "What does the name seyogo mean?")
    assert r_etym["status"] == "answered"
    assert "slim waist" in r_etym["reply"].lower()

    r_arch = manager.process_message("test_dr_7", "What do Goguryeo tomb murals and the Baekje incense burner show?")
    assert r_arch["status"] == "answered"
    assert "deokheung-ri" in r_arch["reply"].lower() or "geumdong daehyangno" in r_arch["reply"].lower()


def test_military_daechwita_and_digital_evolution():
    """Verify war/Daechwita exclusion, bokpan/byeonjuk and Umulsai/iJanggu facts."""
    repo = KnowledgeRepository()
    manager = DialogueManager(repo)

    r_mil = manager.process_message("test_dr_8", "Was the janggu used in war or Daechwita military bands?")
    assert r_mil["status"] == "answered"
    assert "yonggo" in r_mil["reply"].lower()
    assert "excluded" in r_mil["reply"].lower()

    r_dig = manager.process_message("test_dr_9", "Tell me about Umulsai OMR and the iJanggu.")
    assert r_dig["status"] == "answered"
    assert "kaist" in r_dig["reply"].lower() or "piezo" in r_dig["reply"].lower()

    r_zone = manager.process_message("test_dr_10", "What is the difference between bokpan and byeonjuk?")
    assert r_zone["status"] == "answered"
    assert "bokpan" in r_zone["reply"].lower() and "byeonjuk" in r_zone["reply"].lower()
