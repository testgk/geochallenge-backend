-- Columns latitude, longitude, max_distance_km were removed from
-- country_challenges in script 15. This script is kept as a no-op
-- for databases migrated before that change.
ALTER TABLE country_challenges
    DROP COLUMN IF EXISTS latitude,
    DROP COLUMN IF EXISTS longitude,
    DROP COLUMN IF EXISTS max_distance_km;
