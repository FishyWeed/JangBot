"""Import deep research sources, verified facts and citations into janggu.db."""

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

NEW_SOURCES = [
    ("S19", "Akhak Gwebeom (1493)", "Seong Hyeon / Joseon Royal Court", 1, None, "checked"),
    ("S20", "Goryeosa (History of Goryeo)", "Goryeo Royal Records (1451 Compilation)", 1, None, "checked"),
    ("S21", "Hornbostel-Sachs Classification 211.242", "MIM / Musical Instrument Taxonomy", 1, None, "checked"),
    ("S22", "National Gugak Center Organology Research", "National Gugak Center", 1, "https://www.gugak.go.kr", "checked"),
    ("S23", "Jeongganbo Notation Treatise", "King Sejong the Great Historical Records", 1, None, "checked"),
    ("S24", "Janggu Acoustics and Vibration Modes", "Journal of the Acoustical Society of Korea", 1, None, "checked"),
]

NEW_FACTS = [
    (
        "F11",
        "construction",
        "The janggu is classified under the Hornbostel-Sachs system as 211.242, designating a double-headed, waisted, hourglass-shaped membranophone.",
        None, None, None, "Taxonomy", "Verified", None, "S21", "Hornbostel-Sachs taxonomy 211.242"
    ),
    (
        "F12",
        "origin",
        "The ancestral predecessor of the janggu is the Indian idakka, introduced to Korea during the Silla period as the smaller yogo waist drum.",
        None, 57, 935, "Silla", "Verified", None, "S22", "National Gugak Center historical research"
    ),
    (
        "F13",
        "chronology",
        "The Goryeosa records the earliest explicit institutional title janggu-opsa (janggu instructor) in 1076 AD during the reign of King Munjong.",
        1076, 1076, 1076, "Goryeo", "Verified", None, "S20", "Goryeosa annals for 1076 AD"
    ),
    (
        "F14",
        "chronology",
        "King Yejong of Goryeo imported Song Dynasty court instruments in 1114 AD, which standardized the modern hourglass body structure.",
        1114, 1114, 1114, "Goryeo", "Verified", None, "S20", "Goryeosa musical treatise"
    ),
    (
        "F15",
        "chronology",
        "The Akhak Gwebeom (1493) by Seong Hyeon codified the asymmetric construction of the janggu and formally distinguished it from the galgo.",
        1493, 1493, 1493, "Joseon", "Verified", None, "S19", "Akhak Gwebeom, Volume 7"
    ),
    (
        "F16",
        "construction",
        "The resonator body (ullimtong) is carved from a single block of Paulownia coreana wood, cured for two to three years, with a fire-treated scorched interior.",
        None, None, None, "Traditional", "Verified", None, "S22", "National Gugak Center craftsmanship studies"
    ),
    (
        "F17",
        "construction",
        "The narrow central waist (jorongmok) acts as an acoustic choke that prevents high-frequency treble damping while coupling low-frequency cavity resonance.",
        None, None, None, "Acoustic", "Verified", None, "S24", "Janggu cavity resonance analysis"
    ),
    (
        "F18",
        "construction",
        "The drumheads are laced together with continuous V-shaped cords (joimjul) adjusted by sliding leather or wood wedges (joigae) to tune surface tension.",
        None, None, None, "Traditional", "Verified", None, "S19", "Akhak Gwebeom organology metrics"
    ),
    (
        "F19",
        "playing_technique",
        "The instrument is excited using the gungchae (a hardwood mallet on a bamboo root) for the bass head and the yeolchae (a flexible bamboo whip) for the treble head.",
        None, None, None, "Traditional", "Verified", None, "S22", "National Gugak Center performance manual"
    ),
    (
        "F20",
        "playing_technique",
        "The primary stroke taxonomy consists of Deong (simultaneous strike), Gung (left bass strike), Tta (right treble strike), Gi-deok (flam grace note) and Kkol/Jjak (rimshot).",
        None, None, None, "Traditional", "Verified", None, "S22", "National Gugak Center rhythmic stroke ontology"
    ),
    (
        "F21",
        "cultural_use",
        "Jinyangjo is the slowest standard rhythmic cycle (24 beats), associated with profound sorrow, aristocratic dignity and tragic scenes in Pansori.",
        None, None, None, "Jangdan", "Verified", None, "S22", "Korean Musicology Series, Volume 2"
    ),
    (
        "F22",
        "cultural_use",
        "Jungmori is a moderate 12-beat rhythmic cycle used for steady narrative progression, walking tempos and lyrical musical exposition.",
        None, None, None, "Jangdan", "Verified", None, "S22", "Korean Musicology Series, Volume 2"
    ),
    (
        "F23",
        "cultural_use",
        "Jungjungmori is a lilting 12-beat rhythmic cycle used for cheerful storytelling, active scenes and energetic folk dances.",
        None, None, None, "Jangdan", "Verified", None, "S22", "Korean Musicology Series, Volume 2"
    ),
    (
        "F24",
        "cultural_use",
        "Jajinmori is a rapid 12-beat rhythmic cycle (divided into four primary beats with triple subdivisions) used for urgent scenes, battles and lively action.",
        None, None, None, "Jangdan", "Verified", None, "S22", "Korean Musicology Series, Volume 2"
    ),
    (
        "F25",
        "cultural_use",
        "Hwimori is the fastest standard 4-beat rhythmic cycle, driving the performance to a rapid, breathless and dramatic climax.",
        None, None, None, "Jangdan", "Verified", None, "S22", "Korean Musicology Series, Volume 2"
    ),
    (
        "F26",
        "cultural_use",
        "Gutgeori is a syncopated 12-beat rhythmic cycle with a distinct swing, widely used in folk dances, shamanic music and instrumental Sanjo.",
        None, None, None, "Jangdan", "Verified", None, "S22", "Korean Musicology Series, Volume 2"
    ),
    (
        "F27",
        "cultural_use",
        "Eonmori is an asymmetric 10-beat rhythmic cycle (3+2+3+2) used in traditional music to accompany mysterious, otherworldly or heroic characters.",
        None, None, None, "Jangdan", "Verified", None, "S22", "Korean Musicology Series, Volume 2"
    ),
    (
        "F28",
        "cultural_use",
        "Performers call out chuimsae, which are spontaneous vocal cries of encouragement such as 'Eolssigu!' and 'Jota!', to guide energy and pacing.",
        None, None, None, "Performance", "Verified", None, "S22", "National Gugak Center performance treatise"
    ),
    (
        "F29",
        "chronology",
        "Jeongganbo notation, created in the 15th century by King Sejong the Great, provides a spatial 2D grid matrix recording exact durations and janggu stroke mnemonics.",
        None, 1400, 1499, "Joseon", "Verified", None, "S23", "Jeongganbo notation treatise"
    ),
    (
        "F30",
        "construction",
        "The circular membranes produce inharmonic overtones governed by Bessel function zeros, creating a distinct non-integer frequency spectrum.",
        None, None, None, "Acoustic", "Verified", None, "S24", "Janggu vibro-acoustic physics analysis"
    ),
]


def run_import():
    """Insert new sources, facts and citations into janggu.db."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert sources
    for src in NEW_SOURCES:
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
            src,
        )

    # Insert facts and citations
    for item in NEW_FACTS:
        fact_id, category, stmt, y_exact, y_start, y_end, period, status, disp, src_id, cit_detail = item
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
            (fact_id, category, stmt, y_exact, y_start, y_end, period, status, disp),
        )

        cursor.execute(
            """
            INSERT INTO citations (fact_id, source_id, citation_detail)
            VALUES (?, ?, ?)
            ON CONFLICT(fact_id, source_id) DO UPDATE SET
                citation_detail = excluded.citation_detail
            """,
            (fact_id, src_id, cit_detail),
        )

    conn.commit()
    conn.close()
    print("Deep research data imported successfully.")


if __name__ == "__main__":
    run_import()
