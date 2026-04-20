-- Migration: Persist per-user latest shown jobs for command consistency.

CREATE TABLE IF NOT EXISTS user_job_views (
    view_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    rank INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, rank)
);

CREATE INDEX IF NOT EXISTS idx_user_job_views_user_id ON user_job_views(user_id);
CREATE INDEX IF NOT EXISTS idx_user_job_views_job_id ON user_job_views(job_id);
CREATE INDEX IF NOT EXISTS idx_user_job_views_created_at ON user_job_views(created_at DESC);
