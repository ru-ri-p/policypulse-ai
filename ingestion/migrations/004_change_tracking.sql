-- Week 6: change alerts and ML processing timestamp
ALTER TABLE documents
    ADD COLUMN IF NOT EXISTS change_percent FLOAT,
    ADD COLUMN IF NOT EXISTS is_major_change BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS change_summary TEXT,
    ADD COLUMN IF NOT EXISTS ml_processed_at TIMESTAMPTZ;
