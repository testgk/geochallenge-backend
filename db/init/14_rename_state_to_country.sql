-- Migration: rename challenge_type value 'state' to 'country'
UPDATE challenges SET challenge_type = 'country' WHERE challenge_type = 'state';
