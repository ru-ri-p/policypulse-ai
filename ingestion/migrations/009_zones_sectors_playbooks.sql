-- Layer 2: zone/sector tags and playbook impact metadata

ALTER TABLE documents ADD COLUMN IF NOT EXISTS zones TEXT[] DEFAULT '{}';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS sectors TEXT[] DEFAULT '{}';
ALTER TABLE documents ADD COLUMN IF NOT EXISTS playbook_impacts JSONB DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_documents_zones ON documents USING GIN (zones);
CREATE INDEX IF NOT EXISTS idx_documents_sectors ON documents USING GIN (sectors);
