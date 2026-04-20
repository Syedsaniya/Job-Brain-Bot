from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session, sessionmaker
from telegram.ext import Application

from job_brain_bot.config import Settings
from job_brain_bot.db import repo
from job_brain_bot.db.session import session_scope
from job_brain_bot.networking.http_client import SharedHttpClientLifecycle
from job_brain_bot.services import fetch_and_rank_jobs_for_user_async
from job_brain_bot.telegram.formatters import format_job_message


async def run_alert_cycle(
    app: Application,
    settings: Settings,
    session_factory: sessionmaker[Session],
    http_client_lifecycle: SharedHttpClientLifecycle,
) -> None:
    with session_scope(session_factory) as session:
        users = repo.list_users_with_alerts(session)
        user_ids = [user.user_id for user in users]

    for user_id in user_ids:
        with session_scope(session_factory) as session:
            ranked = await fetch_and_rank_jobs_for_user_async(
                session,
                settings,
                http_client_lifecycle.client,
                user_id,
                max_results=5,
            )
            for scored in ranked:
                created = repo.create_alert_if_missing(session, user_id, scored.job.job_id)
                if not created:
                    continue
                await app.bot.send_message(
                    chat_id=user_id,
                    text=format_job_message(scored),
                    disable_web_page_preview=True,
                )


def configure_scheduler(
    app: Application,
    settings: Settings,
    session_factory: sessionmaker[Session],
    http_client_lifecycle: SharedHttpClientLifecycle,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")

    async def _job() -> None:
        await run_alert_cycle(app, settings, session_factory, http_client_lifecycle)

    scheduler.add_job(
        _job,
        trigger="interval",
        hours=settings.scheduler_interval_hours,
        id="job_alert_cycle",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    return scheduler
