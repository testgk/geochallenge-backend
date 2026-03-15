-- Create scores table for leaderboard

CREATE TABLE IF NOT EXISTS scores (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    game_session_id INTEGER REFERENCES game_sessions(id) ON DELETE SET NULL,
    score_type VARCHAR(50) NOT NULL DEFAULT 'game_score',
    points INTEGER NOT NULL DEFAULT 0,
    game_mode VARCHAR(50) NOT NULL DEFAULT 'classic',
    difficulty VARCHAR(20) DEFAULT 'medium',
    accuracy FLOAT DEFAULT 0.0,
    avg_time_per_round FLOAT DEFAULT 0.0,
    rank INTEGER,
    achieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for scores
CREATE INDEX IF NOT EXISTS idx_scores_user_id ON scores(user_id);
CREATE INDEX IF NOT EXISTS idx_scores_points ON scores(points DESC);
CREATE INDEX IF NOT EXISTS idx_scores_game_mode ON scores(game_mode);
CREATE INDEX IF NOT EXISTS idx_scores_score_type ON scores(score_type);
CREATE INDEX IF NOT EXISTS idx_scores_achieved_at ON scores(achieved_at DESC);

-- Composite index for leaderboard queries
CREATE INDEX IF NOT EXISTS idx_scores_leaderboard ON scores(game_mode, difficulty, points DESC);

-- Add constraint for valid score types
ALTER TABLE scores 
ADD CONSTRAINT chk_score_type 
CHECK (score_type IN ('game_score', 'daily_best', 'weekly_best', 'all_time'));
