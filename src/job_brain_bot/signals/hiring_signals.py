from collections import Counter

from job_brain_bot.types import JobRecord

HIRING_PHRASES = ("we are hiring", "hiring now", "urgent hiring", "join our team")


def detect_hiring_signals(job: JobRecord) -> dict[str, str | bool | int]:
    text = f"{job.title} {job.description}".lower()
    active_hiring = any(phrase in text for phrase in HIRING_PHRASES)
    return {
        "active_hiring": active_hiring,
        "insight": "Company actively hiring" if active_hiring else "",
    }


def detect_multiple_openings(jobs: list[JobRecord]) -> dict[str, int]:
    counts = Counter(job.company.lower() for job in jobs if job.company)
    return {company: count for company, count in counts.items() if count > 1}


def enrich_jobs_with_signals(jobs: list[JobRecord]) -> list[JobRecord]:
    repeated = detect_multiple_openings(jobs)
    for job in jobs:
        signals = detect_hiring_signals(job)
        repeats = repeated.get(job.company.lower(), 0)
        if repeats > 1:
            signals["multiple_openings"] = True
            signals["openings_count"] = repeats
            insight = signals.get("insight", "")
            signals["insight"] = (
                f"{insight}. Multiple openings detected ({repeats})".strip(". ")
                if insight
                else f"Multiple openings detected ({repeats})"
            )
        job.signals = signals
    return jobs
