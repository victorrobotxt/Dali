-- 1. Create the Workflow Status Enum
-- This supports the PENDING -> VERIFIED -> MANUAL_REVIEW flow
DO $$ BEGIN
    CREATE TYPE report_status AS ENUM ('PENDING', 'PROCESSING', 'VERIFIED', 'MANUAL_REVIEW', 'REJECTED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- 2. Update 'reports' table
ALTER TABLE reports 
ADD COLUMN IF NOT EXISTS status report_status DEFAULT 'PENDING',
ADD COLUMN IF NOT EXISTS ai_confidence_score INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS manual_review_notes TEXT;

-- 3. Update 'listings' table for Idempotency
-- We hash the file/content to prevent duplicate processing of the same upload
ALTER TABLE listings
ADD COLUMN IF NOT EXISTS content_hash VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_listings_content_hash ON listings(content_hash);

-- 4. Create the Manual Review Queue View
-- This allows the Admin Panel to easily select tasks needing human eyes
CREATE OR REPLACE VIEW view_manual_review_queue AS
SELECT 
    r.id as report_id,
    l.source_url,
    r.ai_confidence_score,
    r.risk_score,
    r.created_at
FROM reports r
JOIN listings l ON r.listing_id = l.id
WHERE r.status = 'MANUAL_REVIEW'
ORDER BY r.risk_score DESC;
