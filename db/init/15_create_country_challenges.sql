-- Create country_challenges table, seeded from the countries + country_boundaries tables.
-- Lat/lng are computed as the centre of the bounding box stored in country_boundaries.bbox
-- (format: [minLng, minLat, maxLng, maxLat]).

CREATE TABLE IF NOT EXISTS country_challenges (
    id              VARCHAR(100) PRIMARY KEY,   -- e.g. 'france', 'united_states'
    location_name   VARCHAR(100) NOT NULL,
    country         VARCHAR(100) NOT NULL,
    continent       VARCHAR(50)  NOT NULL DEFAULT 'Unknown',
    difficulty      VARCHAR(20)  NOT NULL DEFAULT 'medium',
    state_code      VARCHAR(20)  DEFAULT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS country_challenge_hints (
    id           SERIAL PRIMARY KEY,
    challenge_id VARCHAR(100) NOT NULL REFERENCES country_challenges( id ) ON DELETE CASCADE,
    hint_text    VARCHAR(255) NOT NULL,
    hint_order   INTEGER      NOT NULL DEFAULT 0,
    created_at   TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_country_challenges_difficulty ON country_challenges( difficulty );
CREATE INDEX IF NOT EXISTS idx_country_challenges_continent  ON country_challenges( continent );
CREATE INDEX IF NOT EXISTS idx_country_challenge_hints_id    ON country_challenge_hints( challenge_id );

-- Seed from countries table.
INSERT INTO country_challenges ( id, location_name, country, continent, difficulty )
SELECT
    LOWER( REGEXP_REPLACE( c.name, '\s+', '_', 'g' ) )  AS id,
    c.name                                                 AS location_name,
    c.name                                                 AS country,
    COALESCE( c.continent, 'Unknown' )                    AS continent,
    CASE
        WHEN c.area_km2 <    10000 THEN 'expert'
        WHEN c.area_km2 <   100000 THEN 'hard'
        WHEN c.area_km2 < 1000000  THEN 'medium'
        ELSE                            'easy'
    END                                                    AS difficulty
FROM countries c
ON CONFLICT ( id ) DO NOTHING;
