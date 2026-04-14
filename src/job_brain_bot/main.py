from job_brain_bot.config import get_settings
from job_brain_bot.db.session import build_session_factory, create_tables
from job_brain_bot.logging_config import configure_logging
from job_brain_bot.networking.http_client import SharedHttpClientLifecycle
from job_brain_bot.scheduler.jobs import configure_scheduler
from job_brain_bot.telegram.bot import build_bot_application


def run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    create_tables(settings)
    session_factory = build_session_factory(settings)
    http_client_lifecycle = SharedHttpClientLifecycle(settings)
    app = build_bot_application(settings, session_factory, http_client_lifecycle)

    if settings.scheduler_enabled:
        scheduler = configure_scheduler(app, settings, session_factory, http_client_lifecycle)
        scheduler.start()

    app.run_polling(poll_interval=settings.bot_poll_interval_seconds)


if __name__ == "__main__":
    run()
