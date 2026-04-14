import re

from job_brain_bot.db.models import Job

YEARS_RE = re.compile(r"(\d+)")
ENTRY_LEVEL_HINTS = ("fresher", "entry level", "graduate", "junior", "intern")
SENIOR_HINTS = ("senior", "lead", "principal", "staff", "manager")


def _extract_max_years(experience_text: str) -> int:
    values = [int(x) for x in YEARS_RE.findall(experience_text or "")]
    return max(values) if values else 0


def is_fresher_profile(experience_text: str) -> bool:
    text = (experience_text or "").lower()
    if "fresher" in text or "entry" in text:
        return True
    values = [int(x) for x in YEARS_RE.findall(text)]
    if not values:
        return False
    return max(values) <= 2


def filter_jobs_for_profile(jobs: list[Job], profile_experience: str) -> list[Job]:
    if not is_fresher_profile(profile_experience):
        return jobs

    filtered: list[Job] = []
    for job in jobs:
        text = f"{job.title} {job.experience} {job.description}".lower()
        max_years = _extract_max_years(job.experience)
        has_entry = any(token in text for token in ENTRY_LEVEL_HINTS)
        has_senior = any(token in text for token in SENIOR_HINTS)
        if max_years <= 3 and (has_entry or max_years <= 2) and not has_senior:
            filtered.append(job)
    return filtered
