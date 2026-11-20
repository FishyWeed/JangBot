"""Tests for the verified Semantic Network layer, multi-hop reasoning and graph API."""

import shutil
import sqlite3
from fastapi.testclient import TestClient

from src.dialogue.manager import DialogueManager
from src.interface.api import app
from src.knowledge.repository import KnowledgeRepository
from src.knowledge.semantic_network import SemanticNetwork
from tools.curator.build_semantic_network import build_semantic_network


def test_semantic_network_zero_unverified_or_uncited_edges():
    """Every edge in semantic_relations must reference a Verified, cited fact."""
    repo = KnowledgeRepository()
    audit = repo.validate_semantic_network()
    assert audit["ok"] is True
    assert audit["node_count"] >= 90
    assert audit["edge_count"] >= 120
    assert audit["invalid_edges"] == []


def test_curator_migration_idempotent_and_rejects_disputed_edges(tmp_path):
    """Curator script is idempotent and repository validation catches any non-Verified edge."""
    src_db = KnowledgeRepository().db_path
    temp_db = tmp_path / "test_janggu.db"
    shutil.copyfile(src_db, temp_db)

    stats1 = build_semantic_network(temp_db)
    stats2 = build_semantic_network(temp_db)
    assert stats1 == stats2
    assert stats1["covered_verified_facts"] == stats1["total_verified_facts"]

    # Inject a disputed fact edge (F40) and verify validation detects it
    conn = sqlite3.connect(str(temp_db))
    try:
        conn.execute(
            """
            INSERT INTO semantic_relations (subject_id, predicate, object_id, fact_id, qualifier)
            VALUES ('nongak_pungmul', 'documented_in', 'unesco_nongak', 'F40', 'disputed test edge')
            """
        )
        conn.commit()
    finally:
        conn.close()

    temp_repo = KnowledgeRepository(db_path=temp_db)
    audit = temp_repo.validate_semantic_network()
    assert audit["ok"] is False
    assert any(row["fact_id"] == "F40" for row in audit["invalid_edges"])


def test_concept_resolution_and_neighbors():
    """Verify canonical ID, alias and Korean-name resolution plus incoming/outgoing neighbors."""
    sn = SemanticNetwork()
    assert sn.resolve_concept("ullimtong") == "ullimtong"
    assert sn.resolve_concept("울림통") == "ullimtong"
    assert sn.resolve_concept("조롱목") == "jorongmok"
    assert sn.resolve_concept("acoustic choke") == "acoustic_choke"
    assert sn.resolve_concept("정간보") == "jeongganbo"

    out_edges = sn.get_neighbors("ullimtong", direction="outgoing", predicate="made_of")
    assert any(e["neighbor_id"] == "paulownia_coreana" and e["fact_id"] in {"F16", "F43"} for e in out_edges)
    assert all(len(e["citations"]) >= 1 for e in out_edges)

    in_edges = sn.get_neighbors("acoustic_choke", direction="incoming")
    assert any(e["neighbor_id"] == "jorongmok" and e["predicate"] == "acts_as" and e["fact_id"] == "F17" for e in in_edges)


def test_multihop_shortest_path_and_citation_traceability():
    """Verify 2-to-4 hop shortest paths return exact ordered hops, verified fact IDs and citations."""
    sn = SemanticNetwork()

    p1 = sn.find_shortest_path("acoustic_choke", "paulownia_coreana", max_hops=4)
    assert p1["found"] is True
    assert p1["hop_count"] == 3
    assert set(p1["fact_ids"]) >= {"F17", "F03", "F16"} or set(p1["fact_ids"]) >= {"F17", "F52", "F16"}
    assert len(p1["citations"]) >= 2

    p2 = sn.find_shortest_path("idakka", "unesco_nongak", max_hops=5)
    assert p2["found"] is True
    assert p2["hop_count"] == 4
    assert {"F12", "F06", "F07"}.issubset(set(p2["fact_ids"]))
    assert len(p2["citations"]) >= 3

    p3 = sn.find_shortest_path("king_sejong", "jeongganbo_ebnf", max_hops=4)
    assert p3["found"] is True
    assert p3["hop_count"] == 3
    assert {"F29", "F47"}.issubset(set(p3["fact_ids"]))


def test_dialogue_manager_multihop_relational_reasoning_and_citations():
    """Danbi answers chained multi-hop questions in storyteller prose and explains verified sources."""
    repo = KnowledgeRepository()
    dm = DialogueManager(repo)
    sid = "test_semnet_multihop"

    res = dm.process_message(sid, "What wood makes up the body that creates the acoustic choke?")
    assert res["status"] == "answered"
    low = res["reply"].lower()
    assert "paulownia" in low
    assert "jorongmok" in low
    assert "\n- " not in res["reply"]
    assert "F16" in res["fact_ids"]
    assert "F17" in res["fact_ids"]

    cite_res = dm.process_message(sid, "How do you know that?")
    assert cite_res["status"] == "answered"
    assert "F16" in cite_res["reply"] or "F17" in cite_res["reply"]

    # Dynamic neighbor follow-ups suggest connected verified concepts
    followups = dm.agent.toolchain.suggest_graph_followups_sync(["ullimtong"], limit=3)
    assert len(followups) == 3
    assert all(f["id"] != "ullimtong" and f["fact_id"].startswith("F") for f in followups)


def test_graph_api_endpoints():
    """Verify read-only FastAPI semantic graph endpoints return nodes, edges, paths and 404s cleanly."""
    client = TestClient(app)

    r_all = client.get("/api/graph")
    assert r_all.status_code == 200
    body = r_all.json()
    assert body["stats"]["total_nodes"] >= 90
    assert body["stats"]["total_edges"] >= 120
    assert len(body["nodes"]) == body["stats"]["node_count"]

    r_mat = client.get("/api/graph", params={"node_type": "material"})
    assert r_mat.status_code == 200
    assert all(n["node_type"] == "material" for n in r_mat.json()["nodes"])

    r_node = client.get("/api/graph/node/울림통")
    assert r_node.status_code == 200
    node_data = r_node.json()
    assert node_data["node"]["id"] == "ullimtong"
    assert len(node_data["outgoing"]) >= 1
    assert len(node_data["citations"]) >= 1
    assert len(node_data["suggested_followups"]) >= 1

    r_path = client.get("/api/graph/path", params={"from": "idakka", "to": "unesco_nongak", "max_hops": 5})
    assert r_path.status_code == 200
    path_data = r_path.json()
    assert path_data["found"] is True
    assert path_data["hop_count"] == 4
    assert {"F12", "F06", "F07"}.issubset(set(path_data["fact_ids"]))

    r_missing = client.get("/api/graph/node/nonexistent_concept_xyz")
    assert r_missing.status_code == 404
