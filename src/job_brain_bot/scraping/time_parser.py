"""Time parsing utilities for extracting and normalizing job posting timestamps."""

import re
from datetime import datetime, timedelta, timezone
from html import unescape

# Patterns for parsing relative time strings
RELATIVE_TIME_PATTERNS = [
    # "X hours ago", "X hrs ago"
    (re.compile(r"(\d+)\s*hours?\s*ago", re.IGNORECASE), "hours"),
    (re.compile(r"(\d+)\s*hrs?\s*ago", re.IGNORECASE), "hours"),
    # "X minutes ago", "X mins ago"
    (re.compile(r"(\d+)\s*minutes?\s*ago", re.IGNORECASE), "minutes"),
    (re.compile(r"(\d+)\s*mins?\s*ago", re.IGNORECASE), "minutes"),
    # "X days ago"
    (re.compile(r"(\d+)\s*days?\s*ago", re.IGNORECASE), "days"),
    # "X weeks ago"
    (re.compile(r"(\d+)\s*weeks?\s*ago", re.IGNORECASE), "weeks"),
    # "X months ago"
    (re.compile(r"(\d+)\s*months?\s*ago", re.IGNORECASE), "months"),
    # "just now", "today"
    (re.compile(r"just\s*now", re.IGNORECASE), "just_now"),
    (re.compile(r"posted\s*today", re.IGNORECASE), "just_now"),
    # "yesterday"
    (re.compile(r"yesterday", re.IGNORECASE), "days"),
]

# Patterns for parsing absolute dates
DATE_PATTERNS = [
    # ISO format: 2024-01-15 or 2024-01-15T10:30:00
    re.compile(r"(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)?)"),
    # Common formats: Jan 15, 2024 or January 15, 2024
    re.compile(r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*\d{4})", re.IGNORECASE),
    # 15 Jan 2024
    re.compile(r"(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4})", re.IGNORECASE),
    # 15/01/2024 or 01/15/2024
    re.compile(r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})"),
]

# Time range constants for filtering
TIME_RANGES = {
    "24h": timedelta(hours=24),
    "48h": timedelta(hours=48),
    "7d": timedelta(days=7),
}


def parse_relative_time(text: str) -> datetime | None:
    """Parse relative time strings like '2 days ago' into datetime."""
    text_lower = text.lower()

    for pattern, unit in RELATIVE_TIME_PATTERNS:
        match = pattern.search(text_lower)
        if not match:
            continue

        now = datetime.now(timezone.utc)

        if unit == "just_now":
            return now

        if unit == "days" and "yesterday" in text_lower:
            return now - timedelta(days=1)

        try:
            value = int(match.group(1))
        except (IndexError, ValueError):
            continue

        if unit == "hours":
            return now - timedelta(hours=value)
        elif unit == "minutes":
            return now - timedelta(minutes=value)
        elif unit == "days":
            return now - timedelta(days=value)
        elif unit == "weeks":
            return now - timedelta(weeks=value)
        elif unit == "months":
            return now - timedelta(days=value * 30)

    return None


def parse_absolute_date(text: str) -> datetime | None:
    """Parse absolute date strings into datetime."""
    text = text.strip()

    # Try ISO format first
    iso_match = DATE_PATTERNS[0].search(text)
    if iso_match:
        date_str = iso_match.group(1)
        try:
            # Handle Z suffix and timezone offsets
            date_str = date_str.replace("Z", "+00:00")
            if "T" in date_str:
                return datetime.fromisoformat(date_str)
            else:
                dt = datetime.fromisoformat(date_str)
                return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # Try common formats
    for pattern in DATE_PATTERNS[1:]:
        match = pattern.search(text)
        if match:
            date_str = match.group(1)
            formats = [
                "%b %d, %Y",
                "%B %d, %Y",
                "%d %b %Y",
                "%d %B %Y",
                "%b %d %Y",
                "%d/%m/%Y",
                "%m/%d/%Y",
            ]
            for fmt in formats:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue

    return None


def extract_posted_date_from_html(soup) -> datetime | None:
    """Extract posting date from BeautifulSoup HTML content."""
    from bs4 import BeautifulSoup
    import json

    if not isinstance(soup, BeautifulSoup):
        return None

    # 1. Try JSON-LD structured data first (most reliable)
    for script in soup.select("script[type='application/ld+json']"):
        payload = script.string or script.get_text(strip=True)
        if not payload:
            continue
        try:
            data = json.loads(unescape(payload))
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                # Look for JobPosting schema
                if item.get("@type") in {"JobPosting", "JobPostingPosting"}:
                    # Check datePosted field
                    date_posted = item.get("datePosted") or item.get("datePublished")
                    if date_posted:
                        parsed = parse_absolute_date(date_posted)
                        if parsed:
                            return parsed
                    # Check validThrough for context
                    valid_through = item.get("validThrough")
                    if valid_through:
                        parsed = parse_absolute_date(valid_through)
                        if parsed:
                            return parsed
        except json.JSONDecodeError:
            continue

    # 2. Try meta tags with common date patterns
    meta_selectors = [
        "meta[property='article:published_time']",
        "meta[name='datePosted']",
        "meta[name='date']",
        "meta[property='og:updated_time']",
        "meta[itemprop='datePosted']",
        "meta[itemprop='datePublished']",
    ]
    for selector in meta_selectors:
        meta = soup.select_one(selector)
        if meta:
            content = meta.get("content") or ""
            parsed = parse_absolute_date(content)
            if parsed:
                return parsed

    # 3. Try time elements with datetime attribute
    for time_elem in soup.select("time[datetime]"):
        dt_attr = time_elem.get("datetime", "")
        parsed = parse_absolute_date(dt_attr)
        if parsed:
            return parsed

    # 4. Look for common posting date text patterns in the page
    text_patterns = [
        re.compile(r"posted\s*:?\s*(.+?)(?:\n|$|<)", re.IGNORECASE),
        re.compile(r"published\s*:?\s*(.+?)(?:\n|$|<)", re.IGNORECASE),
        re.compile(r"date\s+posted\s*:?\s*(.+?)(?:\n|$|<)", re.IGNORECASE),
        re.compile(r"posted\s+on\s*:?\s*(.+?)(?:\n|$|<)", re.IGNORECASE),
    ]
    page_text = soup.get_text(" ", strip=True)
    for pattern in text_patterns:
        match = pattern.search(page_text)
        if match:
            date_text = match.group(1).strip()
            # Try parsing as relative time first, then absolute
            parsed = parse_relative_time(date_text)
            if parsed:
                return parsed
            parsed = parse_absolute_date(date_text)
            if parsed:
                return parsed

    # 5. Look for relative time indicators anywhere in the text
    relative_patterns = [
        re.compile(r"(\d+\s*(?:hours?|hrs?)\s*ago)", re.IGNORECASE),
        re.compile(r"(\d+\s*(?:days?)\s*ago)", re.IGNORECASE),
        re.compile(r"(just\s*now)", re.IGNORECASE),
        re.compile(r"(yesterday)", re.IGNORECASE),
        re.compile(r"(\d+\s*(?:minutes?|mins?)\s*ago)", re.IGNORECASE),
    ]
    for pattern in relative_patterns:
        match = pattern.search(page_text)
        if match:
            parsed = parse_relative_time(match.group(1))
            if parsed:
                return parsed

    return None


def is_within_time_range(posted_date: datetime | None, time_range: str) -> bool:
    """Check if a job was posted within the specified time range."""
    if not posted_date:
        return False

    if time_range not in TIME_RANGES:
        time_range = "7d"  # Default to 7 days

    cutoff = datetime.now(timezone.utc) - TIME_RANGES[time_range]
    return posted_date >= cutoff


def format_time_ago(posted_date: datetime | None) -> str:
    """Format a datetime as a human-readable 'time ago' string."""
    if not posted_date:
        return "Unknown"

    now = datetime.now(timezone.utc)
    diff = now - posted_date

    if diff < timedelta(minutes=1):
        return "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif diff < timedelta(days=30):
        weeks = diff.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"


def calculate_recency_score(posted_date: datetime | None) -> float:
    """Calculate a recency score (0.0-1.0) based on job posting age."""
    if not posted_date:
        return 0.3  # Lower score for unknown dates, but not 0

    now = datetime.now(timezone.utc)
    age_hours = max((now - posted_date).total_seconds() / 3600, 0.0)

    if age_hours <= 24:
        return 1.0  # Highest score for <24h
    elif age_hours <= 48:
        return 0.8  # Medium-high for <48h
    elif age_hours <= 168:  # 7 days
        return 0.6  # Medium for <7d
    elif age_hours <= 336:  # 14 days
        return 0.4  # Lower for 1-2 weeks
    else:
        return 0.2  # Lowest for older jobs


def normalize_time_range(user_input: str) -> str:
    """Normalize user time range input to standard format."""
    input_clean = user_input.lower().strip()

    if input_clean in {"24h", "24hrs", "24 hours", "1d", "1 day", "today"}:
        return "24h"
    elif input_clean in {"48h", "48hrs", "48 hours", "2d", "2 days"}:
        return "48h"
    elif input_clean in {"7d", "7 days", "1w", "1 week", "week"}:
        return "7d"
    else:
        return "7d"  # Default
