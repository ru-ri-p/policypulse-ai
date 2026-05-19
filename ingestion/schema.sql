CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    jurisdiction TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source_id INT REFERENCES sources(id),
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    content TEXT,
    doc_type TEXT,
    jurisdiction TEXT,
    published_at TIMESTAMPTZ,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    content_hash TEXT,
    embedding vector(384),
    doc_type_classified TEXT,
    risk_level TEXT,
    classification_score FLOAT,
    summary TEXT,
    change_percent FLOAT,
    is_major_change BOOLEAN DEFAULT FALSE,
    change_summary TEXT,
    ml_processed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS document_versions (
    id SERIAL PRIMARY KEY,
    document_id INT REFERENCES documents(id),
    content TEXT,
    content_hash TEXT,
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_url ON documents(url);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_id);

