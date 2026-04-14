CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    role VARCHAR(200) NOT NULL DEFAULT '',
    experience VARCHAR(100) NOT NULL DEFAULT '',
    location VARCHAR(200) NOT NULL DEFAULT '',
    skills TEXT NOT NULL DEFAULT '',
    resume_text TEXT NOT NULL DEFAULT '',
    alerts_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id BIGSERIAL PRIMARY KEY,
    title VARCHAR(250) NOT NULL,
    company VARCHAR(200) NOT NULL,
    location VARCHAR(200) NOT NULL DEFAULT '',
    experience VARCHAR(100) NOT NULL DEFAULT '',
    link TEXT NOT NULL UNIQUE,
    source VARCHAR(100) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    signals_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_id BIGINT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs (company);
CREATE INDEX IF NOT EXISTS idx_users_alerts_enabled ON users (alerts_enabled);
