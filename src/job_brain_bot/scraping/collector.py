from collections.abc import Iterable
import asyncio
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
import structlog

from job_brain_bot.config import Settings
from job_brain_bot.db.repo import normalize_job_identity
from job_brain_bot.scraping.google_search import build_search_queries, search_google_public_links_async
from job_brain_bot.scraping.job_page_parser import parse_job_page_async
from job_brain_bot.types import JobRecord


DROP_QUERY_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "ref", "refid"}
logger = structlog.get_logger(__name__)


def canonicalize_url(raw_url: str) -> str:
    parts = urlsplit(raw_url.strip())
    query_pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in DROP_QUERY_PARAMS]
    normalized_query = urlencode(sorted(query_pairs))
    normalized_path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), normalized_path, normalized_query, ""))


def collect_jobs(
    settings: Settings, role: str, experience: str, location: str, skills: list[str]
) -> list[JobRecord]:
    raise RuntimeError("Use collect_jobs_async with shared http client lifecycle.")


async def collect_jobs_async(
    settings: Settings,
    http_client: httpx.AsyncClient,
    role: str,
    experience: str,
    location: str,
    skills: list[str],
    concurrency: int = 8,
    time_range: str = "7d",
) -> list[JobRecord]:
    queries = build_search_queries(role=role, experience=experience, location=location, skills=skills, time_range=time_range)
    query_sem = asyncio.Semaphore(max(1, min(concurrency, 5)))

    async def _query(q: str) -> list[str]:
        async with query_sem:
            try:
                return await search_google_public_links_async(q, settings, http_client)
            except Exception:
                logger.exception("query_collection_failed", query=q)
                return []

    query_results = await asyncio.gather(*[_query(q) for q in queries])
    all_links = [link for links in query_results for link in links]

    deduped_links = list(dict.fromkeys(canonicalize_url(link) for link in all_links))
    sem = asyncio.Semaphore(concurrency)

    async def _fetch(link: str) -> JobRecord | None:
        async with sem:
            return await parse_job_page_async(http_client, link, settings)

    jobs = [job for job in await asyncio.gather(*[_fetch(link) for link in deduped_links]) if job]
    return dedupe_jobs(jobs)


def dedupe_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    by_key: dict[str, JobRecord] = {}
    for job in jobs:
        key = normalize_job_identity(job.title, job.company, job.location)
        existing = by_key.get(key)
        if not existing:
            by_key[key] = job
            continue
        # Prefer richer records when duplicates collide.
        existing_len = len(existing.description or "")
        current_len = len(job.description or "")
        if current_len > existing_len:
            by_key[key] = job
    return list(by_key.values())


async def collect_jobs_for_profiles_async(
    settings: Settings,
    http_client: httpx.AsyncClient,
    profiles: Iterable[dict[str, str]],
    time_range: str = "7d",
) -> list[JobRecord]:
    collected: list[JobRecord] = []
    for profile in profiles:
        skills = [
            skill.strip()
            for skill in profile.get("skills", "").split(",")
            if skill and skill.strip()
        ]
        collected.extend(
            await collect_jobs_async(
                settings=settings,
                http_client=http_client,
                role=profile.get("role", ""),
                experience=profile.get("experience", ""),
                location=profile.get("location", ""),
                skills=skills,
                time_range=time_range,
            )
        )
    return dedupe_jobs(collected)
