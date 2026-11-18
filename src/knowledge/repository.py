"""Knowledge repository for Janggu facts and sources."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
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
