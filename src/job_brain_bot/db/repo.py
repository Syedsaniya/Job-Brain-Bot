import hashlib
from collections.abc import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from job_brain_bot.db.models import Alert, Job, User, UserJobView
from job_brain_bot.types import JobRecord, UserProfile


def _skills_to_text(skills: list[str]) -> str:
    return ",".join(sorted({s.strip().lower() for s in skills if s.strip()}))


def _safe_link(job: JobRecord) -> str:
    link = (job.link or "").strip()
    if link:
        parts = urlsplit(link)
        params = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_")]
        return urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                (parts.path.rstrip("/") or "/"),
                urlencode(sorted(params)),
                "",
            )
        )
    payload = f"{job.title}:{job.company}:{job.location}:{job.source}"
    return f"generated://{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


def upsert_user(session: Session, profile: UserProfile) -> User:
    existing = session.get(User, profile.user_id)
    if existing:
        existing.role = profile.role
        existing.experience = profile.experience
        existing.location = profile.location
        existing.skills = _skills_to_text(profile.skills)
        existing.resume_text = profile.resume_text
        existing.alerts_enabled = profile.alerts_enabled
        return existing

    user = User(
        user_id=profile.user_id,
        role=profile.role,
        experience=profile.experience,
        location=profile.location,
        skills=_skills_to_text(profile.skills),
        resume_text=profile.resume_text,
        alerts_enabled=profile.alerts_enabled,
    )
    session.add(user)
    return user


def get_user(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)


def get_job(session: Session, job_id: int) -> Job | None:
    return session.get(Job, job_id)


def list_users_with_alerts(session: Session) -> list[User]:
    stmt: Select[tuple[User]] = select(User).where(User.alerts_enabled.is_(True))
    return list(session.scalars(stmt))


def upsert_jobs(session: Session, jobs: Iterable[JobRecord]) -> list[Job]:
    created_or_existing: list[Job] = []
    for job in jobs:
        stmt = (
            insert(Job)
            .values(
                title=job.title,
                company=job.company,
                location=job.location,
                experience=job.experience,
                link=_safe_link(job),
                source=job.source,
                description=job.description,
                posted_date=job.posted_date,
                signals_json=job.signals,
            )
            .on_conflict_do_update(
                index_elements=[Job.link],
                set_={
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "experience": job.experience,
                    "source": job.source,
                    "description": job.description,
                    "posted_date": job.posted_date,
                    "signals_json": job.signals,
                },
            )
            .returning(Job.job_id)
        )
        job_id = session.execute(stmt).scalar_one()
        obj = session.get(Job, job_id)
        if obj:
            created_or_existing.append(obj)
    return created_or_existing


def normalize_job_identity(title: str, company: str, location: str) -> str:
    title_key = " ".join(title.lower().split())
    company_key = " ".join(company.lower().split())
    location_key = " ".join(location.lower().split())
    raw = f"{title_key}:{company_key}:{location_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def list_recent_jobs(session: Session, limit: int = 100) -> list[Job]:
    stmt: Select[tuple[Job]] = select(Job).order_by(Job.created_at.desc()).limit(limit)
    return list(session.scalars(stmt))


def create_alert_if_missing(session: Session, user_id: int, job_id: int) -> bool:
    existing = session.get(Alert, {"user_id": user_id, "job_id": job_id})
    if existing:
        return False
    session.add(Alert(user_id=user_id, job_id=job_id))
    return True


def replace_user_job_views(session: Session, user_id: int, ranked_job_ids: list[int]) -> None:
    session.query(UserJobView).filter(UserJobView.user_id == user_id).delete()
    for idx, job_id in enumerate(ranked_job_ids, start=1):
        session.add(UserJobView(user_id=user_id, job_id=job_id, rank=idx))


def list_user_job_views(session: Session, user_id: int, limit: int = 20) -> list[UserJobView]:
    stmt: Select[tuple[UserJobView]] = (
        select(UserJobView)
        .where(UserJobView.user_id == user_id)
        .order_by(UserJobView.rank.asc())
        .limit(limit)
    )
    return list(session.scalars(stmt))
