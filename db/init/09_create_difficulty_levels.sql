-- Create difficulty_levels table for game configuration
-- This replaces hardcoded DIFFICULTY_MULTIPLIERS in challenges_service.py

CREATE TABLE IF NOT EXISTS difficulty_levels (
    id VARCHAR(20) PRIMARY KEY,
    display_name VARCHAR(50) NOT NULL,
    threshold_multiplier DECIMAL(4,2) NOT NULL,
    max_distance_km INTEGER NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for ordering
CREATE INDEX IF NOT EXISTS idx_difficulty_levels_order ON difficulty_levels(display_order);
