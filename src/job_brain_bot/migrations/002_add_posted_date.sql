-- Migration: Add posted_date column to jobs table
-- Description: Adds a timestamp column to store when job was originally posted

-- Add the new column (nullable to handle existing data safely)
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS posted_date TIMESTAMP WITH TIME ZONE;

-- Create index for efficient time-based filtering
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date);

-- Create a partial index for recent jobs (helps with common queries)
CREATE INDEX IF NOT EXISTS idx_jobs_recent ON jobs(posted_date DESC) WHERE posted_date IS NOT NULL;

-- Add a comment explaining the column
COMMENT ON COLUMN jobs.posted_date IS 'Original job posting date extracted from job page (can be NULL if not found)';
