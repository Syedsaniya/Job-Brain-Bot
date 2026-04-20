import asyncio
import random
from urllib.parse import quote_plus

import httpx
import structlog
from bs4 import BeautifulSoup

from job_brain_bot.config import Settings

logger = structlog.get_logger(__name__)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
]

_QUERY_CACHE: dict[str, tuple[float, list[str]]] = {}
_CACHE_TTL_SECONDS = 600.0
_GOOGLE_BLOCKED_UNTIL = 0.0


def build_search_queries(
    role: str, experience: str, location: str, skills: list[str], time_range: str = "7d"
) -> list[str]:
    skills_text = " ".join(skills[:3]).strip()

    # Build time-based modifier
    time_modifier = ""
    if time_range == "24h":
        time_modifier = "posted in last 24 hours today"
    elif time_range == "48h":
        time_modifier = "posted in last 48 hours 2 days"
    elif time_range == "7d":
        time_modifier = "posted in last 7 days this week"

    base_with_time = f"{role} {experience} jobs {time_modifier} {location} {skills_text}".strip()

    return [
        base_with_time,
        f"site:linkedin.com/jobs {role} {experience} {location} {time_modifier}",
        f"site:indeed.com {role} {experience} jobs {location} {time_modifier}",
        f"site:naukri.com {role} {experience} jobs {location} {time_modifier}",
        f"site:glassdoor.com {role} {experience} jobs {location} {time_modifier}",
        f"{role} {experience} jobs {location} today",
        f"{role} fresher careers {location} hiring now",
        f"{role} {location} company careers {time_modifier}",
        f"we are hiring {role} {location} {time_modifier}",
        f"hiring now {role} {location} immediate joining",
    ]


def _pick_ua(settings: Settings) -> str:
    if not settings.allowed_user_agent_rotation:
        return USER_AGENTS[0]
    return random.choice(USER_AGENTS)


async def _fetch_google_html(query: str, settings: Settings, client: httpx.AsyncClient) -> str:
    global _GOOGLE_BLOCKED_UNTIL

    now = asyncio.get_running_loop().time()
    if now < _GOOGLE_BLOCKED_UNTIL:
        logger.warning(
            "google_search_temporarily_paused",
            cooldown_remaining_seconds=round(_GOOGLE_BLOCKED_UNTIL - now, 1),
        )
        return ""

    url = f"https://www.google.com/search?q={quote_plus(query)}&num={settings.max_jobs_per_query}"
    headers = {"User-Agent": _pick_ua(settings)}
    for attempt in range(1, 4):
        try:
            response = await client.get(url, headers=headers)
            final_url = str(response.url)
            if "/sorry/" in final_url or "/sorry/index" in final_url:
                _GOOGLE_BLOCKED_UNTIL = (
                    asyncio.get_running_loop().time() + settings.google_block_cooldown_seconds
                )
                logger.warning(
                    "google_search_blocked_sorry_page",
                    cooldown_seconds=settings.google_block_cooldown_seconds,
                )
                return ""
            response.raise_for_status()
            await asyncio.sleep(
                random.uniform(settings.min_delay_seconds, settings.max_delay_seconds)
            )
            return response.text
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 429:
                _GOOGLE_BLOCKED_UNTIL = (
                    asyncio.get_running_loop().time() + settings.google_block_cooldown_seconds
                )
            if exc.response is not None and exc.response.status_code not in {
                429,
                500,
                502,
                503,
                504,
            }:
                logger.warning(
                    "google_search_non_retryable_status", status=exc.response.status_code
                )
                return ""
            if attempt == 3:
                logger.warning("google_search_retries_exhausted", error=str(exc))
                return ""
            await asyncio.sleep(min(2**attempt + random.uniform(0, 0.5), 8))
        except httpx.HTTPError as exc:
            if attempt == 3:
                logger.warning("google_search_http_error", error=str(exc))
                return ""
            await asyncio.sleep(min(2**attempt + random.uniform(0, 0.5), 8))
    return ""


async def search_google_public_links_async(
    query: str, settings: Settings, client: httpx.AsyncClient
) -> list[str]:
    now = asyncio.get_running_loop().time()
    cached = _QUERY_CACHE.get(query)
    if cached and (now - cached[0]) <= _CACHE_TTL_SECONDS:
        return cached[1][: settings.max_jobs_per_query]

    html = await _fetch_google_html(query, settings, client)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    links: list[str] = []
    for a_tag in soup.select("a"):
        href = a_tag.get("href", "")
        if href.startswith("/url?q="):
            link = href.split("/url?q=", 1)[1].split("&", 1)[0]
            if link.startswith("http"):
                links.append(link)
    deduped = list(dict.fromkeys(links))
    result = deduped[: settings.max_jobs_per_query]
    _QUERY_CACHE[query] = (now, result)
    return result
