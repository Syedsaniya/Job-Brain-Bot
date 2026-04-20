-- Migration: Expand user profile field sizes for multi-role profiles.
-- Description: Avoid truncation errors when users provide many roles/skills.

ALTER TABLE users
    ALTER COLUMN role TYPE TEXT,
    ALTER COLUMN skills TYPE TEXT,
    ALTER COLUMN location TYPE TEXT;
