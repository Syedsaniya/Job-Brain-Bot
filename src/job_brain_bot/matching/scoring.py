import re
from dataclasses import dataclass
from datetime import UTC, datetime

from job_brain_bot.db.models import Job, User
from job_brain_bot.matching.skill_ontology import get_role_skill_set

SKILLS_WEIGHT = 35
EXPERIENCE_WEIGHT = 25
LOCATION_WEIGHT = 20
KEYWORD_WEIGHT = 10
RECENCY_WEIGHT = 20


@dataclass(slots=True)
class ScoredJob:
    job: Job
    total_score: float
    skills_score: float
    experience_score: float
    location_score: float
    keyword_score: float
    recency_score: float


def _tokenize(text: str) -> set[str]:
    return {
        part.strip().lower()
        for part in text.replace("/", " ").replace(",", " ").split()
        if part.strip()
    }


def _skills_match(profile_skills: set[str], job_text: str) -> float:
    if not profile_skills:
        return 0.5
    matched = sum(1 for skill in profile_skills if skill in job_text.lower())
    return min(1.0, matched / len(profile_skills))


def _resume_relevance(resume_text: str, role: str, job_text: str) -> float:
    if not resume_text:
        return 0.0
    resume_tokens = _tokenize(resume_text)
    role_tokens = _tokenize(role)
    if not resume_tokens:
        return 0.0
    weighted_tokens = set(list(resume_tokens)[:40]) | role_tokens
    matched = sum(1 for token in weighted_tokens if token in job_text.lower())
    return min(1.0, matched / max(len(weighted_tokens), 1))


def _extract_resume_fields(resume_text: str) -> tuple[set[str], set[str]]:
    skills_match = re.search(r"EXTRACTED_SKILLS:\s*(.+)", resume_text, re.IGNORECASE)
    keywords_match = re.search(r"EXTRACTED_KEYWORDS:\s*(.+)", resume_text, re.IGNORECASE)
    skills = set()
    keywords = set()
    if skills_match:
        skills = {item.strip().lower() for item in skills_match.group(1).split(",") if item.strip()}
    if keywords_match:
        keywords = {
            item.strip().lower() for item in keywords_match.group(1).split(",") if item.strip()
        }
    return skills, keywords


def _ontology_alignment(role: str, profile_skills: set[str], job_text: str) -> float:
    ontology = get_role_skill_set(role)
    if not ontology:
        return 0.0
    user_relevant = ontology.intersection(profile_skills)
    if not user_relevant:
        user_relevant = ontology
    matched = sum(1 for token in user_relevant if token in job_text.lower())
    return min(1.0, matched / max(len(user_relevant), 1))


def _experience_match(profile_exp: str, job_exp: str) -> float:
    p = profile_exp.lower()
    j = job_exp.lower()
    if "fresher" in p and ("fresher" in j or "0-1" in j or "0-2" in j):
        return 1.0
    if "0-2" in p and ("0-2" in j or "0-1" in j):
        return 1.0
    if any(token in j for token in _tokenize(p)):
        return 0.8
    return 0.4


def _location_match(profile_loc: str, job_loc: str) -> float:
    p = profile_loc.lower()
    j = job_loc.lower()
    if p == j:
        return 1.0
    if "remote" in p and "remote" in j:
        return 1.0
    if p and p in j:
        return 0.8
    return 0.3


def _keyword_relevance(role: str, job_title: str, description: str) -> float:
    role_tokens = _tokenize(role)
    corpus = f"{job_title} {description}".lower()
    if not role_tokens:
        return 0.0
    matched = sum(1 for token in role_tokens if token in corpus)
    return min(1.0, matched / len(role_tokens))


def _source_quality(source: str) -> float:
    lookup = {"company_page": 1.0, "job_board_public": 0.9, "google": 0.75}
    return lookup.get(source, 0.8)


def _recency_score(created_at: datetime | None) -> float:
    if not created_at:
        return 0.4
    now = datetime.now(UTC)
    age_hours = max((now - created_at).total_seconds() / 3600, 0.0)
    if age_hours <= 24:
        return 1.0
    if age_hours <= 72:
        return 0.8
    if age_hours <= 168:
        return 0.6
    return 0.35


def score_job_for_user(user: User, job: Job) -> ScoredJob:
    profile_skills = _tokenize(user.skills)
    job_text = f"{job.title} {job.description}"

    skills_component = _skills_match(profile_skills, job_text) * SKILLS_WEIGHT
    resume_component = _resume_relevance(user.resume_text, user.role, job_text) * 5
    resume_skills, resume_keywords = _extract_resume_fields(user.resume_text or "")
    resume_skill_bonus = min(
        sum(1.0 for token in resume_skills if token in job_text.lower())
        + sum(0.15 for token in resume_keywords if token in job_text.lower()),
        5.0,
    )
    experience_component = _experience_match(user.experience, job.experience) * EXPERIENCE_WEIGHT
    location_component = _location_match(user.location, job.location) * LOCATION_WEIGHT
    keyword_component = _keyword_relevance(user.role, job.title, job.description) * KEYWORD_WEIGHT
    ontology_component = (
        _ontology_alignment(user.role, profile_skills | resume_skills, job_text) * 3
    )

    quality_boost = _source_quality(job.source) * 2
    # Use posted_date if available, otherwise fall back to created_at
    recency_value = (
        _recency_score(job.posted_date if job.posted_date else job.created_at) * RECENCY_WEIGHT
    )
    total = (
        skills_component
        + experience_component
        + location_component
        + keyword_component
        + resume_component
        + resume_skill_bonus
        + ontology_component
        + quality_boost
        + recency_value
    )
    return ScoredJob(
        job=job,
        total_score=round(min(total, 100.0), 2),
        skills_score=round(skills_component, 2),
        experience_score=round(experience_component, 2),
        location_score=round(location_component, 2),
        keyword_score=round(keyword_component, 2),
        recency_score=round(recency_value, 2),
    )


def rank_jobs_for_user(user: User, jobs: list[Job]) -> list[ScoredJob]:
    scored = [score_job_for_user(user, job) for job in jobs]
    return sorted(scored, key=lambda item: item.total_score, reverse=True)
