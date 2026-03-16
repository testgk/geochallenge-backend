-- Create countries table for storing country areas used in scoring threshold calculation

CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    area_km2 FLOAT NOT NULL,
    continent VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for fast lookups by name
CREATE INDEX IF NOT EXISTS idx_countries_name ON countries(name);
CREATE INDEX IF NOT EXISTS idx_countries_continent ON countries(continent);
