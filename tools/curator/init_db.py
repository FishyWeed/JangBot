"""Initialize the Janggu SQLite database and import seed sources."""

import csv
import io
import os
import sqlite3
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "knowledge-base" / "janggu.db"
SCHEMA_PATH = BASE_DIR / "knowledge-base" / "schema.sql"
SOURCES_CSV_PATH = BASE_DIR / "knowledge-base" / "seed_sources.csv"


def initialize_database():
    """Apply database schema and populate seed sources."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Apply schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        cursor.executescript(f.read())
        
    # Populate sources from CSV
    if SOURCES_CSV_PATH.exists():
        with open(SOURCES_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute(
                    """
                    INSERT INTO sources (id, title, publisher, tier, url, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        publisher = excluded.publisher,
                        tier = excluded.tier,
                        url = excluded.url,
                        status = excluded.status
                    """,
                    (
                        row["id"],
                        row["title"],
                        row["publisher"],
                        int(row["tier"]),
                        row["url"] or None,
                        row["status"],
                    ),
                )
                
    conn.commit()
    conn.close()
    print(f"Database initialized successfully at {DB_PATH}")


if __name__ == "__main__":
    initialize_database()
