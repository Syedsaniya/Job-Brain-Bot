from contextlib import contextmanager
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from job_brain_bot.config import Settings
from job_brain_bot.db.models import Base


def build_engine(settings: Settings):
    return create_engine(settings.database_url, future=True, pool_pre_ping=True)


def build_session_factory(settings: Settings) -> sessionmaker[Session]:
    return sessionmaker(bind=build_engine(settings), autoflush=False, autocommit=False, expire_on_commit=False)


def create_tables(settings: Settings) -> None:
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Generator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
