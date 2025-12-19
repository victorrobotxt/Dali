-- GLASHAUS REFERENCE SCHEMA (Synced with Production)
-- Includes logic from migrations 001 (workflow), 002 (currency), and 003 (area precision)

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TYPE report_status AS ENUM ('PENDING', 'PROCESSING', 'VERIFIED', 'MANUAL_REVIEW', 'REJECTED');

CREATE TABLE buildings (
    id SERIAL PRIMARY KEY,
    cadastre_id VARCHAR(50) UNIQUE NOT NULL,
    address_full VARCHAR(255),
    latitude FLOAT,
    longitude FLOAT,
    construction_year INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    source_url TEXT UNIQUE NOT NULL,
    content_hash VARCHAR(64), -- Idempotency check
    price_bgn NUMERIC(12, 2), -- Financial Precision
    advertised_area_sqm NUMERIC(10, 2), -- Area Precision
    description_raw TEXT,
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_listings_content_hash ON listings(content_hash);

CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    listing_id INT REFERENCES listings(id) ON DELETE CASCADE,
    building_id INT REFERENCES buildings(id),
    status report_status DEFAULT 'PENDING',
    risk_score INT,
    ai_confidence_score INT DEFAULT 0,
    legal_brief TEXT,
    discrepancy_details JSONB,
    image_archive_urls JSONB,
    cost_to_generate NUMERIC(10, 4), -- API Usage Cost
    manual_review_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    listing_id INT REFERENCES listings(id),
    price_bgn NUMERIC(12, 2),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
