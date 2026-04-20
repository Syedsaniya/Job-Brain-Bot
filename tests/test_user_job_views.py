from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from job_brain_bot.db import repo
from job_brain_bot.db.models import Base, Job
from job_brain_bot.types import UserProfile


def _session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return factory()


def test_replace_and_list_user_job_views() -> None:
    session = _session()
    repo.upsert_user(
        session,
        UserProfile(
            user_id=123, role="Backend", experience="Fresher", location="Remote", skills=[]
        ),
    )
    j1 = Job(
        title="Backend Engineer",
        company="A",
        location="Remote",
        experience="0-2 years",
        link="https://a/1",
        source="company_page",
        description="",
    )
    j2 = Job(
        title="Backend Engineer 2",
        company="B",
        location="Remote",
        experience="0-2 years",
        link="https://b/2",
        source="company_page",
        description="",
    )
    session.add_all([j1, j2])
    session.commit()

    repo.replace_user_job_views(session, 123, [j1.job_id, j2.job_id])
    session.commit()
    views = repo.list_user_job_views(session, 123)
    assert len(views) == 2
    assert views[0].rank == 1 and views[0].job_id == j1.job_id
    assert views[1].rank == 2 and views[1].job_id == j2.job_id

    repo.replace_user_job_views(session, 123, [j2.job_id])
    session.commit()
    views = repo.list_user_job_views(session, 123)
    assert len(views) == 1
    assert views[0].job_id == j2.job_id
