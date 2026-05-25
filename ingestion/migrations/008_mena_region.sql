-- Phase 8: MENA region support
-- Adds a 'region' column for high-level geographic grouping (MENA, EU, US, UK, OECD)
-- and an index on jurisdiction for faster filtered queries.

ALTER TABLE documents ADD COLUMN IF NOT EXISTS region TEXT;
ALTER TABLE sources ADD COLUMN IF NOT EXISTS region TEXT;

CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON documents(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_documents_region ON documents(region);

-- Backfill region based on existing jurisdiction values
UPDATE documents SET region = CASE
    WHEN jurisdiction IN ('UAE', 'SA', 'QA', 'BH', 'KW', 'OM', 'EG', 'GCC') THEN 'MENA'
    WHEN jurisdiction IN ('EU', 'OECD') THEN 'EU'
    WHEN jurisdiction = 'US' THEN 'US'
    WHEN jurisdiction = 'UK' THEN 'UK'
    ELSE 'OTHER'
END
WHERE region IS NULL;

UPDATE sources SET region = CASE
    WHEN jurisdiction IN ('UAE', 'SA', 'QA', 'BH', 'KW', 'OM', 'EG', 'GCC') THEN 'MENA'
    WHEN jurisdiction IN ('EU', 'OECD') THEN 'EU'
    WHEN jurisdiction = 'US' THEN 'US'
    WHEN jurisdiction = 'UK' THEN 'UK'
    ELSE 'OTHER'
END
WHERE region IS NULL;
