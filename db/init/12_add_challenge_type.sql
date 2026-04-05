-- Migration: add challenge_type and state_code columns to challenges table

ALTER TABLE challenges
    ADD COLUMN IF NOT EXISTS challenge_type VARCHAR(20) NOT NULL DEFAULT 'city',
    ADD COLUMN IF NOT EXISTS state_code VARCHAR(20) DEFAULT NULL;

-- Backfill existing rows as city challenges
UPDATE challenges SET challenge_type = 'city' WHERE challenge_type IS NULL;

-- Index for filtering by challenge type
CREATE INDEX IF NOT EXISTS idx_challenges_type ON challenges(challenge_type);