-- Widen country_boundaries.country_code to accommodate name-based fallback codes
-- for countries whose ISO_A3 is -99 (disputed territories, etc.)
ALTER TABLE country_boundaries ALTER COLUMN country_code TYPE VARCHAR(20);
