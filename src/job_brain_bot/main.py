import structlog

from job_brain_bot.config import get_settings
from job_brain_bot.db.session import build_session_factory, create_tables, database_driver_prefix
from job_brain_bot.logging_config import configure_logging
from job_brain_bot.networking.http_client import SharedHttpClientLifecycle
from job_brain_bot.scheduler.jobs import configure_scheduler
from job_brain_bot.telegram.bot import build_bot_application


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = structlog.get_logger(__name__)
    logger.info(
        "startup_configuration", db_driver_prefix=database_driver_prefix(settings.database_url)
    )
    if settings.auto_create_tables:
        create_tables(settings)
        logger.info("schema_bootstrap", mode="auto_create_tables_enabled")
    session_factory = build_session_factory(settings)
    http_client_lifecycle = SharedHttpClientLifecycle(settings)
    scheduler_factory = None
    if settings.scheduler_enabled:
        scheduler_factory = lambda app: configure_scheduler(  # noqa: E731
            app, settings, session_factory, http_client_lifecycle
        )
    app = build_bot_application(
        settings,
        session_factory,
        http_client_lifecycle,
        scheduler_factory=scheduler_factory,
    )

    app.run_polling(poll_interval=settings.bot_poll_interval_seconds)


if __name__ == "__main__":
    run()
