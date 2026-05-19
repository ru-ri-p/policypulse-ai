-- Phase 4: LLM compliance digests + cache key
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS digest_what_changed TEXT,
    ADD COLUMN IF NOT EXISTS digest_who_affected TEXT,
    ADD COLUMN IF NOT EXISTS digest_what_to_do TEXT,
    ADD COLUMN IF NOT EXISTS digest_urgency TEXT,
    ADD COLUMN IF NOT EXISTS digest_key_deadline TEXT,
    ADD COLUMN IF NOT EXISTS digest_content_hash TEXT,
    ADD COLUMN IF NOT EXISTS digest_generated_at TIMESTAMPTZ;
