# Job Brain Bot

Production-ready Telegram bot for fresher and early-career job discovery with multi-source public web aggregation, AI-style weighted matching, and scheduled alerts.

## Features

### Core Features
- Telegram commands: `/start`, `/setprofile`, `/jobs`, `/alerts`, `/recommend`
- **Time-based job filtering**: `/jobs time=24h/48h/7d` for recent postings
- Optional resume upload: `/resume` (PDF/DOCX/TXT) for improved matching
- Multi-source aggregation via Google queries + public job pages
- Async scraping pipeline with `httpx` + concurrency controls
- BeautifulSoup parsing with Playwright fallback for JS-heavy pages
- Google anti-rate-limit guardrails (query caps + cooldown when blocked)
- PostgreSQL persistence for users, jobs, alerts
- 6-hour scheduler for ingestion, matching, and notification

### 🤖 AI Intelligence Layer
- **`/analyze [job#]`** - AI analysis of job requirements (skills, experience, certifications)
- **`/skills [job#]`** - Skill gap analysis with learning paths and certification suggestions
- **`/network [job#] [name]`** - Generate personalized cold outreach messages
- **`/referral [job#] [name]`** - Generate referral request templates

### Matching Algorithm
- Role-aware resume ontology (cybersecurity/backend/frontend/devops/data)
- Fresher-first filtering and weighted relevance score:
  - Skills match: 35%
  - Experience match: 25%
  - Location match: 20%
  - **Recency**: 20% (new!)
  - Keyword relevance: 10%
- Job posting timestamp extraction and filtering

### Safe & Ethical Scraping
- Respects robots.txt
- No login bypass or private data scraping
- URL safety checks
- Rate limiting and user-agent rotation

## Project structure

`src/job_brain_bot/` contains modular layers:

- `telegram/` command handlers and message formatting
- `scraping/` query generation, safety checks, parsers
- `matching/` scoring and fresher filters
- `signals/` hiring signal extraction
- `db/` models, sessions, repositories
- `scheduler/` periodic ingestion and alert delivery

## Prerequisites

- Python 3.12
- Poetry
- PostgreSQL 14+
- Telegram Bot token from BotFather

## Local setup

1. Install dependencies:

```bash
poetry install
```

2. Install Playwright Chromium:

```bash
poetry run python -m playwright install chromium
```

3. Create env file:

```bash
copy .env.example .env
```

4. Update `.env`:
- `TELEGRAM_BOT_TOKEN`
- `DATABASE_URL`
- `APPLY_MIGRATIONS_ON_STARTUP=true` (default; safe and idempotent)
- Optional throttling controls:
  - `MAX_ROLES_PER_SEARCH=3`
  - `MAX_GOOGLE_QUERIES_PER_ROLE=4`
  - `GOOGLE_BLOCK_COOLDOWN_SECONDS=900`

5. Run DB migration SQL:

```bash
psql "$DATABASE_URL" -f src/job_brain_bot/migrations/001_init.sql
psql "$DATABASE_URL" -f src/job_brain_bot/migrations/002_add_posted_date.sql
psql "$DATABASE_URL" -f src/job_brain_bot/migrations/003_add_user_job_views.sql
psql "$DATABASE_URL" -f src/job_brain_bot/migrations/004_expand_user_profile_fields.sql
```

6. Start bot:

```bash
poetry run job-brain-bot
```

7. Run tests:

```bash
poetry run pytest
```

## Telegram Usage

### Core Commands
- `/start` -> Register user and see all commands
- `/setprofile role|experience|location|skills` -> Set your profile
  - Example: `/setprofile Cybersecurity Analyst,Backend Engineer|Fresher|Hyderabad|Python,SIEM,Network Security`
  - Multiple roles are supported (comma-separated in the role field)
- `/jobs [time=24h/48h/7d]` -> Fetch and rank jobs (default: 7 days)
  - Example: `/jobs time=24h` for jobs posted in last 24 hours
- `/recommend` -> Get top job recommendations
- `/alerts on/off` -> Enable/disable daily job alerts
- `/resume` -> Upload resume (PDF/DOCX/TXT) with caption `/resume`

### 🤖 AI Intelligence Commands
- `/analyze [job_number]` -> AI analysis of job requirements
  - Shows required/preferred skills, experience level, certifications
- `/skills [job_number]` -> Skill gap analysis vs your profile
  - Shows missing skills, learning resources, certifications needed
  - Estimates preparation time
- `/network [job_number] [contact_name]` -> Generate cold outreach message
  - Creates LinkedIn connection request or email template
- `/referral [job_number] [contact_name]` -> Generate referral request
  - Polite referral request for former colleagues/alumni

**Note:** For `[job_number]`, use the number shown in `/jobs` output (1, 2, 3, etc.)

Output format includes:
- job title + company
- location
- experience
- apply link
- match score
- suggested LinkedIn recruiter search query and search URL

## Safe scraping constraints

- The bot does not bypass login systems
- The bot does not scrape private user data
- The bot does not automate recruiter messaging
- The bot checks robots.txt where possible
- URL safety checks skip login/auth paths

## Deployment

### Render

1. Push code to GitHub.
2. Create Worker service from `render.yaml`.
3. Add managed PostgreSQL and set `DATABASE_URL`.
4. Set `TELEGRAM_BOT_TOKEN`.
5. Deploy.

### Railway

1. Create a new project and add PostgreSQL plugin.
2. Deploy from repo using Dockerfile.
3. Set env vars from `.env.example`.
   - Set `APPLY_MIGRATIONS_ON_STARTUP=true`
   - Set `AUTO_CREATE_TABLES=false`
   - Set `ADMIN_USER_IDS=<your_telegram_user_id>`
4. Ensure worker stays always-on.

## CI

- GitHub Actions workflow: `.github/workflows/ci.yml`
- Runs lightweight quality gates:
  - `ruff check .`
  - `ruff format --check .`
  - `pytest -q`

## Validation Checklist

- `/start` creates user row and shows command list.
- `/setprofile` persists role, experience, location, skills.
- `/jobs` returns structured jobs with links, scores, and posting time.
- `/jobs time=24h` filters to recent jobs only.
- Fresher profile excludes roles above 3 years.
- `/recommend` returns ranked subset.
- `/analyze` extracts skills and requirements from job.
- `/skills` shows gap analysis with learning paths.
- `/network` generates personalized message.
- Scheduler sends non-duplicate alerts.
- Job timestamps are extracted and displayed.

## Version

**Current Version:** 0.2.0  
**Changelog:** See `TIME_FILTER_IMPLEMENTATION.md` and `AI_INTELLIGENCE_IMPLEMENTATION.md` for feature details.
