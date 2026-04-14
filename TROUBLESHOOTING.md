# Job Brain Bot - Troubleshooting Guide

## Common Deployment Issues

### 1. `ModuleNotFoundError: No module named 'psycopg2'`

**Root Cause:** The `psycopg2` Python package is not installed in the container.

**Solutions:**

#### Option A: Use the updated pyproject.toml (Recommended)
We've added `psycopg2-binary` to the dependencies. Make sure you're using the latest `pyproject.toml`:

```bash
# Rebuild your Docker image
docker build --no-cache -t job-brain-bot .
```

#### Option B: Use requirements.txt directly
If Poetry continues to fail, use pip with requirements.txt:

```dockerfile
# In Dockerfile, replace Poetry install with:
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium
```

#### Option C: Update DATABASE_URL format
Make sure your `DATABASE_URL` uses the correct driver:

```env
# For psycopg2 (recommended for compatibility)
DATABASE_URL=postgresql+psycopg2://postgres:postgre@localhost:5432/job_brain

# For psycopg3 (newer, but requires explicit driver specification)
DATABASE_URL=postgresql+psycopg://postgres:postgre@localhost:5432/job_brain
```

### 2. Database Connection Failed

**Checklist:**
1. Is PostgreSQL running? 
2. Does the database `job_brain` exist?
3. Are credentials correct?
4. Is the host accessible from the container?

**Quick Test:**
```bash
# Test database connection
docker run -it --rm postgres:15-alpine psql "your_database_url" -c "SELECT 1;"
```

### 3. Docker Build Fails

**Common Causes:**

**a) Missing system dependencies for psycopg2**
The Dockerfile now includes:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*
```

**b) Poetry lock file out of sync**
```bash
# Regenerate poetry.lock
poetry lock --no-update
```

**c) Platform-specific binary not available**
If deploying to ARM (e.g., Apple Silicon), psycopg2-binary may not have pre-built wheels:
```dockerfile
# Use this instead of psycopg2-binary for ARM builds:
RUN apt-get install -y libpq-dev gcc \
    && pip install psycopg2 --no-binary :all:
```

### 4. Render.com Specific Issues

**Build fails with "Poetry not found"**
- Render uses Docker build context
- Make sure `Dockerfile` is at project root
- Check that `pyproject.toml` is copied

**Container crashes immediately**
Check logs for:
1. Missing environment variables
2. Database URL format issues
3. Telegram token invalid

**Health check fails**
The `/health` command checks database connectivity. If this fails:
1. Check `DATABASE_URL` is set in Render dashboard
2. Verify PostgreSQL instance is running
3. Check network connectivity (Render internal URL vs external)

### 5. Playwright/Chromium Issues

**Error: "Chromium not found"**
```bash
# In Dockerfile, ensure this runs after poetry install:
RUN python -m playwright install chromium
```

**Error: "Cannot launch browser" in container**
Some platforms restrict browser execution. If scraping fails:
1. Disable Playwright fallback in `.env`:
   ```env
   PLAYWRIGHT_ENABLED=false
   ```
2. Or use a non-slim Python base image with more libraries

### 6. Environment Variable Issues

**Required Variables:**
```env
TELEGRAM_BOT_TOKEN=your_token_here
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
```

**Important:** Never commit `.env` file. Use Render/Railway dashboard for production secrets.

### 7. Migration Issues

**Error: "table already exists"**
```bash
# Safe migration - only creates if not exists
psql "$DATABASE_URL" -f src/job_brain_bot/migrations/001_init.sql
```

**Error: "column does not exist" (posted_date)**
Run migration 002:
```bash
psql "$DATABASE_URL" -f src/job_brain_bot/migrations/002_add_posted_date.sql
```

## Quick Fixes

### Reset Everything
```bash
# Stop containers
docker-compose down

# Remove volumes (deletes data!)
docker-compose down -v

# Rebuild
docker-compose up --build
```

### Test Database Locally
```bash
# Start PostgreSQL in Docker
docker run -d \
  --name job-brain-db \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgre \
  -e POSTGRES_DB=job_brain \
  postgres:15

# Test connection
psql postgresql://postgres:postgre@localhost:5432/job_brain -c "SELECT 1;"
```

### Debug Mode
```env
# Enable debug logging
LOG_LEVEL=DEBUG
```

## Getting Help

1. **Check logs first:** `docker logs <container_id>`
2. **Test locally:** Verify the bot works locally before deploying
3. **Isolate variables:** Test database, then Telegram, then scraping separately
4. **Use `/health` command:** In Telegram, send `/health` to check system status

## Prevention Checklist

Before deploying:
- [ ] Run `poetry install` locally to verify pyproject.toml is valid
- [ ] Run `pytest` to ensure tests pass
- [ ] Verify `DATABASE_URL` format matches your SQL driver
- [ ] Test database connection locally
- [ ] Check that all env vars are set in deployment dashboard
- [ ] Ensure `requirements.txt` is up to date
