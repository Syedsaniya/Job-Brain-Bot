from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
import httpx

from job_brain_bot.config import Settings
from job_brain_bot.db import repo
from job_brain_bot.matching.filters import filter_jobs_for_profile
from job_brain_bot.matching.scoring import ScoredJob, rank_jobs_for_user
from job_brain_bot.scraping.collector import collect_jobs_async
from job_brain_bot.scraping.time_parser import TIME_RANGES, is_within_time_range, normalize_time_range
from job_brain_bot.signals.hiring_signals import enrich_jobs_with_signals


async def fetch_and_rank_jobs_for_user_async(
    session: Session,
    settings: Settings,
    http_client: httpx.AsyncClient,
    user_id: int,
    max_results: int = 10,
    time_range: str = "7d",
) -> list[ScoredJob]:
    user = repo.get_user(session, user_id)
    if not user:
        return []

    time_range = normalize_time_range(time_range)
    skills = [s.strip() for s in user.skills.split(",") if s.strip()]

    scraped_jobs = await collect_jobs_async(
        settings=settings,
        http_client=http_client,
        role=user.role,
        experience=user.experience,
        location=user.location,
        skills=skills,
        concurrency=settings.scraping_concurrency,
        time_range=time_range,
    )

    enriched = enrich_jobs_with_signals(scraped_jobs)
    repo.upsert_jobs(session, enriched)

    # Filter jobs by time range if specified
    jobs = repo.list_recent_jobs(session, limit=150)

    # Apply time-based filtering if time_range is specified
    if time_range in TIME_RANGES:
        cutoff = datetime.now(timezone.utc) - TIME_RANGES[time_range]
        jobs = [job for job in jobs if job.posted_date is not None and job.posted_date >= cutoff]

    filtered = filter_jobs_for_profile(jobs, user.experience)
    ranked = rank_jobs_for_user(user, filtered)
    return ranked[:max_results]
