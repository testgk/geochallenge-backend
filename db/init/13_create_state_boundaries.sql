-- Create state_boundaries table for storing GeoJSON polygon data for states/provinces
-- Used for point-in-polygon checking for state challenges

CREATE TABLE IF NOT EXISTS state_boundaries (
    id SERIAL PRIMARY KEY,
    state_code VARCHAR(10) NOT NULL UNIQUE,  -- ISO 3166-2 code, e.g. 'US-CA'
    state_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(3) NOT NULL,        -- ISO 3166-1 alpha-2, e.g. 'US'
    geometry JSONB NOT NULL,                 -- GeoJSON geometry (Polygon or MultiPolygon)
    bbox JSONB,                              -- Bounding box [minLng, minLat, maxLng, maxLat]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_state_boundaries_code    ON state_boundaries( state_code );
CREATE INDEX IF NOT EXISTS idx_state_boundaries_country ON state_boundaries( country_code );
CREATE INDEX IF NOT EXISTS idx_state_boundaries_geometry ON state_boundaries USING GIN( geometry );
