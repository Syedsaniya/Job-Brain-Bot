import httpx

from job_brain_bot.config import Settings


class SharedHttpClientLifecycle:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: httpx.AsyncClient | None = None

    async def startup(self) -> None:
        if self._client is not None:
            return
        limits = httpx.Limits(
            max_connections=max(self._settings.scraping_concurrency * 4, 20),
            max_keepalive_connections=max(self._settings.scraping_concurrency * 2, 10),
        )
        self._client = httpx.AsyncClient(
            timeout=self._settings.request_timeout_seconds,
            follow_redirects=True,
            limits=limits,
        )

    async def shutdown(self) -> None:
        if self._client is None:
            return
        await self._client.aclose()
        self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("HTTP client not initialized. Call startup first.")
        return self._client
