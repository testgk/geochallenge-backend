-- One row per country, up to 6 neighbors as columns.
-- Populated by scripts/generate_neighbor_hints.py.

DROP TABLE IF EXISTS country_neighbors;

CREATE TABLE IF NOT EXISTS country_neighbors (
    country_id  VARCHAR(100) PRIMARY KEY REFERENCES country_challenges( id ) ON DELETE CASCADE,
    neighbor_1  VARCHAR(100),
    neighbor_2  VARCHAR(100),
    neighbor_3  VARCHAR(100),
    neighbor_4  VARCHAR(100),
    neighbor_5  VARCHAR(100),
    neighbor_6  VARCHAR(100)
);
