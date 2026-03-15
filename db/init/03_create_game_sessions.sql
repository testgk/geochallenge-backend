-- Create game_sessions table

CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_mode VARCHAR(50) NOT NULL DEFAULT 'classic',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    score INTEGER DEFAULT 0,
    rounds_played INTEGER DEFAULT 0,
    total_rounds INTEGER DEFAULT 5,
    total_distance_error FLOAT DEFAULT 0.0,
    avg_response_time FLOAT DEFAULT 0.0,
    difficulty VARCHAR(20) DEFAULT 'medium',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for game_sessions
CREATE INDEX IF NOT EXISTS idx_game_sessions_user_id ON game_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_game_sessions_status ON game_sessions(status);
CREATE INDEX IF NOT EXISTS idx_game_sessions_game_mode ON game_sessions(game_mode);
CREATE INDEX IF NOT EXISTS idx_game_sessions_score ON game_sessions(score DESC);

-- Add constraint for valid status values
ALTER TABLE game_sessions 
ADD CONSTRAINT chk_game_status 
CHECK (status IN ('pending', 'in_progress', 'completed', 'abandoned'));

-- Add constraint for valid game modes
ALTER TABLE game_sessions 
ADD CONSTRAINT chk_game_mode 
CHECK (game_mode IN ('classic', 'time_attack', 'challenge', 'multiplayer'));
