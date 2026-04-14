from dataclasses import dataclass
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx


LOGIN_HINTS = ("login", "signin", "auth", "account")


@dataclass(slots=True)
class SafetyDecision:
    allowed: bool
    reason: str


def is_public_url(url: str) -> SafetyDecision:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return SafetyDecision(False, "unsupported_scheme")
    path = parsed.path.lower()
    if any(hint in path for hint in LOGIN_HINTS):
        return SafetyDecision(False, "login_path_blocked")
    return SafetyDecision(True, "ok")


async def robots_allows_async(
    client: httpx.AsyncClient, url: str, user_agent: str, timeout: int = 10
) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        response = await client.get(robots_url, timeout=timeout)
        if response.status_code >= 400:
            return True
        parser.parse(response.text.splitlines())
        return parser.can_fetch(user_agent, url)
    except httpx.HTTPError:
        # Best effort compliance, do not hard-fail ingestion.
        return True
