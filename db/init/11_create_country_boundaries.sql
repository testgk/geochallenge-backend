-- Create country_boundaries table for storing GeoJSON polygon data
-- Used for point-in-polygon checking to validate clicks are within country borders

CREATE TABLE IF NOT EXISTS country_boundaries (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(3) NOT NULL UNIQUE,  -- ISO 3166-1 alpha-3 code
    country_name VARCHAR(100) NOT NULL,
    geometry JSONB NOT NULL,  -- GeoJSON geometry (Polygon or MultiPolygon)
    bbox JSONB,  -- Bounding box [minLng, minLat, maxLng, maxLat] for quick filtering
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_country_boundaries_name ON country_boundaries(country_name);
CREATE INDEX IF NOT EXISTS idx_country_boundaries_code ON country_boundaries(country_code);
CREATE INDEX IF NOT EXISTS idx_country_boundaries_geometry ON country_boundaries USING GIN(geometry);
