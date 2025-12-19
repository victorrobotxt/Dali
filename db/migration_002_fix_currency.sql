-- Fix Financial Precision for Listings and Reports
-- RUN THIS MANUALLY OR VIA ALEMBIC

ALTER TABLE listings 
ALTER COLUMN price_bgn TYPE NUMERIC(12, 2) 
USING price_bgn::numeric;

ALTER TABLE reports
ALTER COLUMN cost_to_generate TYPE NUMERIC(10, 4)
USING cost_to_generate::numeric;

ALTER TABLE price_history
ALTER COLUMN price_bgn TYPE NUMERIC(12, 2)
USING price_bgn::numeric;
