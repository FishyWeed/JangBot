"""Load verified seed facts and citations into the Janggu SQLite database."""

import csv
import sqlite3
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "knowledge-base" / "janggu.db"
FACTS_CSV_PATH = BASE_DIR / "knowledge-base" / "seed_facts.csv"


def load_facts():
    """Load facts and citations from CSV into the database."""
    if not FACTS_CSV_PATH.exists():
        print(f"File not found: {FACTS_CSV_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    with open(FACTS_CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Insert fact
            year_exact = int(row["year_exact"]) if row["year_exact"] else None
            year_start = int(row["year_range_start"]) if row["year_range_start"] else None
            year_end = int(row["year_range_end"]) if row["year_range_end"] else None

            cursor.execute(
                """
                INSERT INTO facts (
                    id, category, statement, year_exact,
                    year_range_start, year_range_end, period,
                    status, dispute_note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    category = excluded.category,
                    statement = excluded.statement,
                    year_exact = excluded.year_exact,
                    year_range_start = excluded.year_range_start,
                    year_range_end = excluded.year_range_end,
                    period = excluded.period,
                    status = excluded.status,
                    dispute_note = excluded.dispute_note
                """,
                (
                    row["id"],
                    row["category"],
                    row["statement"],
                    year_exact,
                    year_start,
                    year_end,
                    row["period"] or None,
                    row["status"],
                    row["dispute_note"] or None,
                ),
            )

            # Insert citation
            if row.get("source_id"):
                cursor.execute(
                    """
                    INSERT INTO citations (fact_id, source_id, citation_detail)
                    VALUES (?, ?, ?)
                    ON CONFLICT(fact_id, source_id) DO UPDATE SET
                        citation_detail = excluded.citation_detail
                    """,
                    (row["id"], row["source_id"], row.get("citation_detail")),
                )

    conn.commit()
    conn.close()
    print("Seed facts and citations loaded successfully.")


if __name__ == "__main__":
    load_facts()
