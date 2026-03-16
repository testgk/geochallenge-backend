-- Create challenges table for storing geographic challenges

CREATE TYPE difficulty_level AS ENUM ('easy', 'medium', 'hard', 'expert');

CREATE TABLE IF NOT EXISTS challenges (
    id VARCHAR(100) PRIMARY KEY,  -- e.g., 'paris_france'
    location_name VARCHAR(100) NOT NULL,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    country VARCHAR(100) NOT NULL,
    continent VARCHAR(50) NOT NULL,
    difficulty difficulty_level NOT NULL,
    max_distance_km INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create challenge_hints table for storing hints (one-to-many)
CREATE TABLE IF NOT EXISTS challenge_hints (
    id SERIAL PRIMARY KEY,
    challenge_id VARCHAR(100) NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    hint_text VARCHAR(255) NOT NULL,
    hint_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_challenges_difficulty ON challenges(difficulty);
CREATE INDEX IF NOT EXISTS idx_challenges_continent ON challenges(continent);
CREATE INDEX IF NOT EXISTS idx_challenges_country ON challenges(country);
CREATE INDEX IF NOT EXISTS idx_challenge_hints_challenge_id ON challenge_hints(challenge_id);
