# Time-Based Job Filtering Implementation

## Overview
This implementation adds time-based job filtering to the JobIntelBot Telegram bot, allowing users to fetch jobs posted within specific time ranges (24h, 48h, 7d).

## Files Modified/Created

### 1. Database Schema (`src/job_brain_bot/db/models.py`)
- Added `posted_date` column (nullable TIMESTAMP with timezone) to `Job` table
- This stores the original job posting date extracted from job pages

### 2. Time Parser Module (`src/job_brain_bot/scraping/time_parser.py`) [NEW]
Helper functions for time parsing and filtering:
- `parse_relative_time()` - Parses strings like "2 days ago", "5 hours ago"
- `parse_absolute_date()` - Parses ISO and common date formats
- `extract_posted_date_from_html()` - Extracts dates from HTML/JSON-LD
- `is_within_time_range()` - Filters jobs by time range
- `format_time_ago()` - Formats dates as human-readable strings
- `calculate_recency_score()` - Calculates recency scores for ranking
- `normalize_time_range()` - Normalizes user input (24h, 48h, 7d)
- `TIME_RANGES` - Constants for time range filtering

### 3. Types (`src/job_brain_bot/types.py`)
- Added `posted_date: datetime | None` field to `JobRecord` dataclass

### 4. Google Search (`src/job_brain_bot/scraping/google_search.py`)
- Updated `build_search_queries()` to accept `time_range` parameter
- Generates time-specific search queries like:
  - "cybersecurity fresher jobs posted in last 24 hours today"
  - "site:indeed.com role experience jobs location posted in last 24 hours"

### 5. Job Page Parser (`src/job_brain_bot/scraping/job_page_parser.py`)
- Imports `extract_posted_date_from_html()` from time_parser
- Extracts and stores `posted_date` when parsing job pages
- Uses JSON-LD structured data, meta tags, and text patterns

### 6. Repository (`src/job_brain_bot/db/repo.py`)
- Updated `upsert_jobs()` to handle `posted_date` field
- Stores extracted posting dates in the database

### 7. Collector (`src/job_brain_bot/scraping/collector.py`)
- Updated `collect_jobs_async()` to accept `time_range` parameter
- Passes time range to search query builder
- Updated `collect_jobs_for_profiles_async()` with time range support

### 8. Scoring (`src/job_brain_bot/matching/scoring.py`)
Updated scoring weights to match requirements:
- Skills match: 35% (was 40%)
- Experience match: 25% (was 30%)
- Location match: 20% (unchanged)
- Recency: 20% (NEW)
- Keywords: 10% (unchanged)

Added `recency_score` field to `ScoredJob` dataclass.
Updated `_recency_score()` to use `posted_date` (falls back to `created_at`).

### 9. Services (`src/job_brain_bot/services.py`)
- Updated `fetch_and_rank_jobs_for_user_async()` to accept `time_range` parameter
- Applies time-based filtering to jobs after collection
- Filters jobs where `posted_date >= cutoff` based on selected time range

### 10. Telegram Bot (`src/job_brain_bot/telegram/bot.py`)
- Added `_parse_time_arg()` helper to extract `time=` parameter from command args
- Updated `/jobs` command to accept time parameter
- Usage: `/jobs time=24h` or `/jobs time=48h` or `/jobs time=7d`
- Shows time range in response header
- Suggests expanding time range if no jobs found

### 11. Formatters (`src/job_brain_bot/telegram/formatters.py`)
- Updated `format_job_message()` to display posting time
- Shows "⏱ Posted: X hours/days ago" in job listings
- Updated score breakdown to show Recency score

### 12. Database Migration (`src/job_brain_bot/migrations/002_add_posted_date.sql`) [NEW]
SQL migration to add the new column:
```sql
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS posted_date TIMESTAMP WITH TIME ZONE;
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date);
CREATE INDEX IF NOT EXISTS idx_jobs_recent ON jobs(posted_date DESC) WHERE posted_date IS NOT NULL;
```

### 13. Tests (`tests/test_time_parser.py`) [NEW]
Comprehensive test suite for time parsing:
- 14 test cases covering all time parsing functions
- Tests for relative time, absolute dates, filtering, formatting, and scoring

### 14. Updated Tests (`tests/test_ranking_logic.py`)
- Added `posted_date` to existing Job objects
- Added new `test_recency_affects_ranking()` test case

## Usage

### Command Syntax
```
/jobs time=24h          # Jobs from last 24 hours
/jobs time=48h          # Jobs from last 48 hours  
/jobs time=7d           # Jobs from last 7 days (default)
```

### Example Output
```
🎯 Here are your top personalized job matches (last 24 hours):

🔹 SOC Analyst - XYZ Company
✅ Good Match
📍 Hyderabad
💼 0-2 years
⏱ Posted: 12 hours ago
🔗 Apply Link: https://example.com/jobs/123
⭐ Match Score: 89/100
🧠 Score Breakdown: Skills 35.0, Exp 25.0, Location 20.0, Recency 20.0
```

## Recency Scoring
- < 24 hours: 1.0 (max score)
- < 48 hours: 0.8
- < 7 days: 0.6
- 1-2 weeks: 0.4
- > 2 weeks: 0.2
- Unknown date: 0.3 (lower priority but not discarded)

## Error Handling
- If no jobs found in selected range, suggests expanding to 7 days
- Falls back to 7 days for invalid time range inputs
- Jobs without timestamps get lower priority but are not discarded

## Performance
- Database indexes on `posted_date` for efficient filtering
- Cached search results avoid re-scraping same jobs
- Async scraping for concurrent job page fetching
