-- Track when a document was first ingested vs last re-scraped
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS first_scraped_at TIMESTAMPTZ;

UPDATE documents
SET first_scraped_at = scraped_at
WHERE first_scraped_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_documents_first_scraped ON documents (first_scraped_at DESC);
