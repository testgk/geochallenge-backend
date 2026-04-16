-- Table storing pre-computed neighbor relationships between countries.
-- Populated by scripts/generate_neighbor_hints.py.

CREATE TABLE IF NOT EXISTS country_neighbors (
    id              SERIAL PRIMARY KEY,
    country_id      VARCHAR(100) NOT NULL REFERENCES country_challenges( id ) ON DELETE CASCADE,
    neighbor_name   VARCHAR(100) NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ( country_id, neighbor_name )
);

CREATE INDEX IF NOT EXISTS idx_country_neighbors_country_id ON country_neighbors( country_id );
