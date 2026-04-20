from contextlib import contextmanager
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from job_brain_bot.config import Settings
from job_brain_bot.db.models import Base


def _normalize_database_url(raw_url: str) -> str:
    """
    Ensure SQLAlchemy uses psycopg (v3) driver explicitly.

    Many platforms provide DATABASE_URL as:
    - postgres://...
    - postgresql://...
    which defaults SQLAlchemy to psycopg2 unless a driver is specified.
    """
    value = (raw_url or "").strip()
    if not value:
        return value

    if value.startswith("postgres://"):
        return "postgresql+psycopg://" + value[len("postgres://") :]

    if value.startswith("postgresql://"):
        return "postgresql+psycopg://" + value[len("postgresql://") :]

    if value.startswith("postgresql+psycopg://"):
        return value

    return value


def database_driver_prefix(raw_url: str) -> str:
    normalized = _normalize_database_url(raw_url)
    if "://" not in normalized:
        return "unknown"
    return normalized.split("://", 1)[0] + "://"


def build_engine(settings: Settings):
    database_url = _normalize_database_url(settings.database_url)
    return create_engine(database_url, future=True, pool_pre_ping=True)


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
