import asyncio
import json
import random
import re
from html import unescape
from urllib.parse import urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

from job_brain_bot.config import Settings
from job_brain_bot.scraping.dynamic_fetch import fetch_dynamic_html_async
from job_brain_bot.scraping.safety import is_public_url, robots_allows_async
from job_brain_bot.scraping.time_parser import extract_posted_date_from_html
from job_brain_bot.types import JobRecord

EXP_RE = re.compile(r"(\d+)\s*(?:\+|-|to)?\s*(\d+)?\s*years?", re.IGNORECASE)
logger = structlog.get_logger(__name__)


def _guess_source(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "linkedin.com" in host or "indeed.com" in host or "naukri.com" in host:
        return "job_board_public"
    if "google." in host:
        return "google"
    return "company_page"


def _extract_experience(text: str) -> str:
    match = EXP_RE.search(text)
    if not match:
        if "fresher" in text.lower():
            return "0-1 years"
        return "Not specified"
    low = match.group(1)
    high = match.group(2) or low
    return f"{low}-{high} years"


def _extract_company(soup: BeautifulSoup, default: str) -> str:
    # Prefer schema.org JobPosting metadata when available.
    for script in soup.select("script[type='application/ld+json']"):
        payload = script.string or script.get_text(strip=True)
        if not payload:
            continue
        try:
            data = json.loads(unescape(payload))
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            org = item.get("hiringOrganization")
            if isinstance(org, dict) and org.get("name"):
                return str(org["name"]).strip()[:200]
            if item.get("name") and item.get("@type") in {"Organization", "Corporation"}:
                return str(item["name"]).strip()[:200]

    for selector in (
        "meta[property='og:site_name']",
        "meta[name='application-name']",
        "meta[name='author']",
        "[data-company]",
    ):
        element = soup.select_one(selector)
        if not element:
            continue
        content = (
            element.get("content") or element.get("data-company") or element.get_text(strip=True)
        )
        if content:
            return content.strip()[:200]

    for selector in ("meta[property='og:site_name']", "meta[name='application-name']"):
        element = soup.select_one(selector)
        if element and element.get("content"):
            return element["content"].strip()[:200]
    return default


async def parse_job_page_async(
    client: httpx.AsyncClient, url: str, settings: Settings
) -> JobRecord | None:
    try:
        decision = is_public_url(url)
        if not decision.allowed:
            return None

        ua = "Mozilla/5.0 JobBrainBot/1.0 (+public-job-indexing)"
        if not await robots_allows_async(client, url, ua, timeout=settings.request_timeout_seconds):
            return None

        headers = {"User-Agent": ua}
        html = ""
        try:
            response = await client.get(url, headers=headers)
            if response.status_code >= 400:
                return None
            html = response.text
            await asyncio.sleep(
                random.uniform(settings.min_delay_seconds, settings.max_delay_seconds)
            )
        except httpx.HTTPError:
            if settings.playwright_enabled:
                html = await fetch_dynamic_html_async(url, settings.playwright_timeout_ms)
        if not html:
            return None

        soup = BeautifulSoup(html, "lxml")
        title = (soup.title.string.strip() if soup.title and soup.title.string else "Unknown role")[
            :250
        ]
        body_text = soup.get_text(" ", strip=True)
        company_guess = urlparse(url).netloc.replace("www.", "").split(".")[0].title()
        company = _extract_company(soup, company_guess)

        location = "Remote" if "remote" in body_text.lower() else "Not specified"
        experience = _extract_experience(body_text)
        if "fresher" in body_text.lower() and experience == "Not specified":
            experience = "0-1 years"

        posted_date = extract_posted_date_from_html(soup)

        return JobRecord(
            title=title,
            company=company,
            location=location,
            experience=experience,
            link=url,
            source=_guess_source(url),
            description=body_text[:2000],
            posted_date=posted_date,
        )
    except Exception:
        logger.exception("job_page_parse_failed", url=url)
        return None
