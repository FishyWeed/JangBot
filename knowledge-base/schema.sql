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

CREATE TABLE IF NOT EXISTS concept_nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    korean_name TEXT,
    node_type TEXT NOT NULL CHECK (node_type IN (
        'instrument', 'component', 'material', 'implement',
        'technique_stroke', 'rhythm', 'genre_tradition',
        'acoustic_concept', 'historical_record', 'person_institution_tech'
    )),
    category TEXT,
    summary TEXT NOT NULL,
    aliases TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS semantic_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id TEXT NOT NULL REFERENCES concept_nodes(id) ON DELETE CASCADE,
    predicate TEXT NOT NULL CHECK (predicate IN (
        'has_part', 'made_of', 'tuned_by', 'finished_with', 'classified_as',
        'produces', 'acts_as', 'prevents', 'measured_or_modeled_by',
        'played_with', 'strikes', 'uses_rhythm', 'used_in', 'excluded_from', 'leads_or_directs',
        'evolved_into', 'standardized_by', 'documented_in', 'created_by',
        'preserved_at', 'distinguished_from', 'depicted_in', 'digitized_by'
    )),
    object_id TEXT NOT NULL REFERENCES concept_nodes(id) ON DELETE CASCADE,
    fact_id TEXT NOT NULL REFERENCES facts(id) ON DELETE CASCADE,
    qualifier TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(subject_id, predicate, object_id, fact_id)
);

CREATE INDEX IF NOT EXISTS idx_semrel_subject ON semantic_relations(subject_id, predicate);
CREATE INDEX IF NOT EXISTS idx_semrel_object ON semantic_relations(object_id, predicate);
CREATE INDEX IF NOT EXISTS idx_semrel_fact ON semantic_relations(fact_id);
