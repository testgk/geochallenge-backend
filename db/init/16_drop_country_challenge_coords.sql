-- Remove coordinate/distance columns from country_challenges —
-- country challenges are scored by boundary check only, not by distance.
ALTER TABLE country_challenges
    DROP COLUMN IF EXISTS latitude,
    DROP COLUMN IF EXISTS longitude,
    DROP COLUMN IF EXISTS max_distance_km;
