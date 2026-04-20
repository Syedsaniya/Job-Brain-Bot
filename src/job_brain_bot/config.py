from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    database_url: str = Field(alias="DATABASE_URL")
    auto_create_tables: bool = Field(default=False, alias="AUTO_CREATE_TABLES")
    apply_migrations_on_startup: bool = Field(default=True, alias="APPLY_MIGRATIONS_ON_STARTUP")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    bot_poll_interval_seconds: float = Field(
        default=1.0, ge=0.1, le=10.0, alias="BOT_POLL_INTERVAL_SECONDS"
    )

    scheduler_enabled: bool = Field(default=True, alias="SCHEDULER_ENABLED")
    scheduler_interval_hours: int = Field(default=6, ge=1, le=24, alias="SCHEDULER_INTERVAL_HOURS")

    max_jobs_per_query: int = Field(default=20, ge=5, le=50, alias="MAX_JOBS_PER_QUERY")
    scraping_concurrency: int = Field(default=8, ge=1, le=20, alias="SCRAPING_CONCURRENCY")
    request_timeout_seconds: int = Field(default=20, ge=5, le=120, alias="REQUEST_TIMEOUT_SECONDS")
    min_delay_seconds: float = Field(default=1.0, ge=0.0, le=30.0, alias="MIN_DELAY_SECONDS")
    max_delay_seconds: float = Field(default=3.5, ge=0.1, le=60.0, alias="MAX_DELAY_SECONDS")

    playwright_enabled: bool = Field(default=True, alias="PLAYWRIGHT_ENABLED")
    playwright_timeout_ms: int = Field(
        default=30000, ge=5000, le=120000, alias="PLAYWRIGHT_TIMEOUT_MS"
    )
    allowed_user_agent_rotation: bool = Field(default=True, alias="ALLOWED_USER_AGENT_ROTATION")

    # AI Intelligence Layer Settings
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    ai_provider: str = Field(default="pattern", alias="AI_PROVIDER")  # pattern, openai, anthropic
    ai_analysis_enabled: bool = Field(default=True, alias="AI_ANALYSIS_ENABLED")
    networking_generator_enabled: bool = Field(default=True, alias="NETWORKING_GENERATOR_ENABLED")
    admin_user_ids: str = Field(default="", alias="ADMIN_USER_IDS")

    def admin_ids_set(self) -> set[int]:
        if not self.admin_user_ids.strip():
            return set()
        values: set[int] = set()
        for part in self.admin_user_ids.split(","):
            item = part.strip()
            if not item:
                continue
            try:
                values.add(int(item))
            except ValueError:
                continue
        return values


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
