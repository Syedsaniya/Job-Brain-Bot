import random
from urllib.parse import quote_plus

import asyncio
import httpx
from bs4 import BeautifulSoup

from job_brain_bot.config import Settings

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/125.0 Safari/537.36",
]


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

    base = f"{role} {experience} jobs in {location} {skills_text}".strip()
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
    url = f"https://www.google.com/search?q={quote_plus(query)}&num={settings.max_jobs_per_query}"
    headers = {"User-Agent": _pick_ua(settings)}
    for attempt in range(1, 4):
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            await asyncio.sleep(random.uniform(settings.min_delay_seconds, settings.max_delay_seconds))
            return response.text
        except httpx.HTTPError:
            if attempt == 3:
                raise
            await asyncio.sleep(min(2**attempt, 8))
    return ""


async def search_google_public_links_async(
    query: str, settings: Settings, client: httpx.AsyncClient
) -> list[str]:
    html = await _fetch_google_html(query, settings, client)
    soup = BeautifulSoup(html, "lxml")
    links: list[str] = []
    for a_tag in soup.select("a"):
        href = a_tag.get("href", "")
        if href.startswith("/url?q="):
            link = href.split("/url?q=", 1)[1].split("&", 1)[0]
            if link.startswith("http"):
                links.append(link)
    deduped = list(dict.fromkeys(links))
    return deduped[: settings.max_jobs_per_query]
