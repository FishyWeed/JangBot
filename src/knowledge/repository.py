"""Knowledge repository for Janggu facts and sources."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from src.settings import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / config["paths"]["database"]


class KnowledgeRepository:
    """Read-only interface to the janggu SQLite database."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH

    def _get_read_connection(self) -> sqlite3.Connection:
        """Open a read-only SQLite database connection."""
        uri = f"file:{self.db_path.resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_write_connection(self) -> sqlite3.Connection:
        """Open a read-write SQLite connection for logging."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def get_verified_facts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch verified facts, optionally filtered by category."""
        conn = self._get_read_connection()
        cursor = conn.cursor()
        
        if category:
            cursor.execute(
                """
                SELECT id, category, statement, year_exact,
                       year_range_start, year_range_end, period, status
                FROM facts
                WHERE status = 'Verified' AND category = ?
                ORDER BY year_exact ASC, id ASC
                """,
                (category,),
            )
        else:
            cursor.execute(
                """
                SELECT id, category, statement, year_exact,
                       year_range_start, year_range_end, period, status
                FROM facts
                WHERE status = 'Verified'
                ORDER BY year_exact ASC, id ASC
                """
            )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_disputed_facts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch disputed facts (e.g., historiographical/nomenclature debates)."""
        conn = self._get_read_connection()
        cursor = conn.cursor()
        if category:
            cursor.execute(
                """
                SELECT id, category, statement, year_exact,
                       year_range_start, year_range_end, period, status, dispute_note
                FROM facts
                WHERE status = 'Disputed' AND category = ?
                ORDER BY id ASC
                """,
                (category,),
            )
        else:
            cursor.execute(
                """
                SELECT id, category, statement, year_exact,
                       year_range_start, year_range_end, period, status, dispute_note
                FROM facts
                WHERE status = 'Disputed'
                ORDER BY id ASC
                """
            )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_citations_for_fact(self, fact_id: str) -> List[Dict[str, Any]]:
        """Fetch citations and source metadata for a fact."""
        conn = self._get_read_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.citation_detail, c.page_number,
                   s.id AS source_id, s.title, s.publisher, s.tier, s.url
            FROM citations c
            JOIN sources s ON c.source_id = s.id
            WHERE c.fact_id = ?
            """,
            (fact_id,),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def log_query(
        self,
        query_text: str,
        matched_intent: Optional[str],
        confidence_score: float,
        status: str,
    ) -> None:
        """Log a user query to query_logs for analysis."""
        conn = self._get_write_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO query_logs (query_text, matched_intent, confidence_score, status)
                VALUES (?, ?, ?, ?)
                """,
                (query_text, matched_intent, confidence_score, status),
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------ Semantic Network Read API

    def has_semantic_network(self) -> bool:
        """Return True if concept_nodes and semantic_relations tables exist and are populated."""
        conn = self._get_read_connection()
        try:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('concept_nodes', 'semantic_relations')"
                ).fetchall()
            }
            if tables != {"concept_nodes", "semantic_relations"}:
                return False
            count = conn.execute("SELECT COUNT(*) AS cnt FROM semantic_relations").fetchone()["cnt"]
            return count > 0
        finally:
            conn.close()

    @staticmethod
    def _hydrate_node(row: sqlite3.Row) -> Dict[str, Any]:
        node = dict(row)
        raw_aliases = node.get("aliases")
        if isinstance(raw_aliases, str):
            try:
                node["aliases"] = json.loads(raw_aliases)
            except Exception:
                node["aliases"] = []
        elif raw_aliases is None:
            node["aliases"] = []
        return node

    def get_all_concept_nodes(self, node_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all concept nodes, optionally filtered by node_type."""
        conn = self._get_read_connection()
        try:
            if node_type:
                rows = conn.execute(
                    """
                    SELECT id, label, korean_name, node_type, category, summary, aliases
                    FROM concept_nodes
                    WHERE node_type = ?
                    ORDER BY node_type ASC, id ASC
                    """,
                    (node_type,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, label, korean_name, node_type, category, summary, aliases
                    FROM concept_nodes
                    ORDER BY node_type ASC, id ASC
                    """
                ).fetchall()
            return [self._hydrate_node(r) for r in rows]
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()

    def get_concept_node(self, concept_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single concept node by canonical ID."""
        conn = self._get_read_connection()
        try:
            row = conn.execute(
                """
                SELECT id, label, korean_name, node_type, category, summary, aliases
                FROM concept_nodes
                WHERE id = ?
                """,
                (concept_id,),
            ).fetchone()
            return self._hydrate_node(row) if row else None
        except sqlite3.OperationalError:
            return None
        finally:
            conn.close()

    def get_semantic_relations(
        self,
        subject_id: Optional[str] = None,
        object_id: Optional[str] = None,
        predicate: Optional[str] = None,
        fact_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch verified directed triples joined with verified fact statements."""
        conn = self._get_read_connection()
        try:
            clauses = ["f.status = 'Verified'"]
            params: List[Any] = []
            if subject_id:
                clauses.append("r.subject_id = ?")
                params.append(subject_id)
            if object_id:
                clauses.append("r.object_id = ?")
                params.append(object_id)
            if predicate:
                clauses.append("r.predicate = ?")
                params.append(predicate)
            if fact_id:
                clauses.append("r.fact_id = ?")
                params.append(fact_id)

            where_sql = " AND ".join(clauses)
            rows = conn.execute(
                f"""
                SELECT r.id, r.subject_id, r.predicate, r.object_id, r.fact_id, r.qualifier,
                       f.statement AS fact_statement, f.category AS fact_category, f.status AS fact_status
                FROM semantic_relations r
                JOIN facts f ON r.fact_id = f.id
                WHERE {where_sql}
                ORDER BY r.id ASC
                """,
                tuple(params),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            return []
        finally:
            conn.close()

    def get_facts_by_ids(self, fact_ids: Sequence[str]) -> List[Dict[str, Any]]:
        """Fetch verified facts preserving the order of requested fact_ids."""
        ordered_ids = list(dict.fromkeys(fact_ids))
        if not ordered_ids:
            return []
        conn = self._get_read_connection()
        try:
            placeholders = ",".join("?" for _ in ordered_ids)
            rows = conn.execute(
                f"""
                SELECT id, category, statement, year_exact,
                       year_range_start, year_range_end, period, status
                FROM facts
                WHERE status = 'Verified' AND id IN ({placeholders})
                """,
                tuple(ordered_ids),
            ).fetchall()
            by_id = {r["id"]: dict(r) for r in rows}
            return [by_id[fid] for fid in ordered_ids if fid in by_id]
        finally:
            conn.close()

    def validate_semantic_network(self) -> Dict[str, Any]:
        """Audit semantic network tables ensuring every edge links to a verified, cited fact."""
        conn = self._get_read_connection()
        try:
            tables = {
                row["name"]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('concept_nodes', 'semantic_relations')"
                ).fetchall()
            }
            if tables != {"concept_nodes", "semantic_relations"}:
                return {"ok": False, "node_count": 0, "edge_count": 0, "invalid_edges": ["Missing semantic network tables"]}

            node_count = conn.execute("SELECT COUNT(*) AS cnt FROM concept_nodes").fetchone()["cnt"]
            edge_count = conn.execute("SELECT COUNT(*) AS cnt FROM semantic_relations").fetchone()["cnt"]
            bad_rows = conn.execute(
                """
                SELECT r.id, r.subject_id, r.predicate, r.object_id, r.fact_id, f.status
                FROM semantic_relations r
                LEFT JOIN facts f ON r.fact_id = f.id
                LEFT JOIN (SELECT DISTINCT fact_id FROM citations) c ON r.fact_id = c.fact_id
                LEFT JOIN concept_nodes sn ON r.subject_id = sn.id
                LEFT JOIN concept_nodes onode ON r.object_id = onode.id
                WHERE f.id IS NULL OR f.status != 'Verified' OR c.fact_id IS NULL
                   OR sn.id IS NULL OR onode.id IS NULL
                """
            ).fetchall()
            invalid_edges = [dict(r) for r in bad_rows]
            return {
                "ok": node_count > 0 and edge_count > 0 and len(invalid_edges) == 0,
                "node_count": node_count,
                "edge_count": edge_count,
                "invalid_edges": invalid_edges,
            }
        finally:
            conn.close()
