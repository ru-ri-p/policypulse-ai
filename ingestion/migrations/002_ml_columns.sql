-- Week 4: classification and summarisation columns
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS doc_type_classified TEXT,
    ADD COLUMN IF NOT EXISTS risk_level TEXT,
    ADD COLUMN IF NOT EXISTS classification_score FLOAT,
    ADD COLUMN IF NOT EXISTS summary TEXT;
