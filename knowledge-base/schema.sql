-- Database schema for Janggu Knowledge Base

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT,
    publisher TEXT NOT NULL,
    tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3)),
    language TEXT DEFAULT 'en',
    snapshot_path TEXT,
    content_hash TEXT,
    status TEXT NOT NULL CHECK (status IN ('checked', 'lead', 'archived')) DEFAULT 'lead',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL CHECK (category IN ('origin', 'etymology', 'chronology', 'construction', 'playing_technique', 'cultural_use', 'evolution')),
    statement TEXT NOT NULL,
    year_exact INTEGER,
    year_range_start INTEGER,
    year_range_end INTEGER,
    period TEXT,
    status TEXT NOT NULL CHECK (status IN ('Verified', 'Disputed', 'Pending', 'Rejected')) DEFAULT 'Pending',
    dispute_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS citations (
    fact_id TEXT NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    citation_detail TEXT,
    page_number TEXT,
    PRIMARY KEY (fact_id, source_id)
);

CREATE TABLE IF NOT EXISTS query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    matched_intent TEXT,
    confidence_score REAL,
    status TEXT NOT NULL CHECK (status IN ('answered', 'clarification', 'fallback', 'off_topic')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
