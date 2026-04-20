"""Tests for the time parsing utilities."""

from datetime import UTC, datetime, timedelta

from job_brain_bot.scraping.time_parser import (
    TIME_RANGES,
    calculate_recency_score,
    format_time_ago,
    is_within_time_range,
    normalize_time_range,
    parse_absolute_date,
    parse_relative_time,
)


def test_parse_relative_time_hours():
    """Test parsing 'X hours ago' strings."""
    result = parse_relative_time("posted 5 hours ago")
    assert result is not None
    # Should be approximately 5 hours ago
    now = datetime.now(UTC)
    diff = now - result
    assert timedelta(hours=4) < diff < timedelta(hours=6)


def test_parse_relative_time_days():
    """Test parsing 'X days ago' strings."""
    result = parse_relative_time("posted 3 days ago")
    assert result is not None
    now = datetime.now(UTC)
    diff = now - result
    assert timedelta(days=2, hours=20) < diff < timedelta(days=3, hours=4)


def test_parse_relative_time_yesterday():
    """Test parsing 'yesterday' strings."""
    result = parse_relative_time("posted yesterday")
    assert result is not None
    now = datetime.now(UTC)
    diff = now - result
    assert timedelta(hours=20) < diff < timedelta(days=2)


def test_parse_relative_time_just_now():
    """Test parsing 'just now' strings."""
    result = parse_relative_time("posted just now")
    assert result is not None
    now = datetime.now(UTC)
    diff = now - result
    assert diff < timedelta(minutes=1)


def test_parse_relative_time_minutes():
    """Test parsing 'X minutes ago' strings."""
    result = parse_relative_time("posted 30 minutes ago")
    assert result is not None
    now = datetime.now(UTC)
    diff = now - result
    assert timedelta(minutes=28) < diff < timedelta(minutes=32)


def test_parse_relative_time_weeks():
    """Test parsing 'X weeks ago' strings."""
    result = parse_relative_time("posted 2 weeks ago")
    assert result is not None
    now = datetime.now(UTC)
    diff = now - result
    assert timedelta(days=13) < diff < timedelta(days=15)


def test_parse_relative_time_unknown():
    """Test parsing unknown time strings returns None."""
    result = parse_relative_time("posted some time ago")
    assert result is None


def test_parse_absolute_date_iso():
    """Test parsing ISO format dates."""
    result = parse_absolute_date("2024-01-15T10:30:00+00:00")
    assert result is not None
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


def test_parse_absolute_date_common():
    """Test parsing common date formats."""
    result = parse_absolute_date("Jan 15, 2024")
    assert result is not None
    assert result.year == 2024
    assert result.month == 1
    assert result.day == 15


def test_normalize_time_range():
    """Test time range normalization."""
    assert normalize_time_range("24h") == "24h"
    assert normalize_time_range("24hrs") == "24h"
    assert normalize_time_range("24 hours") == "24h"
    assert normalize_time_range("48h") == "48h"
    assert normalize_time_range("2d") == "48h"
    assert normalize_time_range("7d") == "7d"
    assert normalize_time_range("1 week") == "7d"
    assert normalize_time_range("invalid") == "7d"  # Default


def test_is_within_time_range():
    """Test time range filtering."""
    now = datetime.now(UTC)

    # Job posted 12 hours ago should be within 24h, 48h, and 7d
    job_12h = now - timedelta(hours=12)
    assert is_within_time_range(job_12h, "24h") is True
    assert is_within_time_range(job_12h, "48h") is True
    assert is_within_time_range(job_12h, "7d") is True

    # Job posted 30 hours ago should NOT be within 24h but within 48h and 7d
    job_30h = now - timedelta(hours=30)
    assert is_within_time_range(job_30h, "24h") is False
    assert is_within_time_range(job_30h, "48h") is True
    assert is_within_time_range(job_30h, "7d") is True

    # Job posted 5 days ago should only be within 7d
    job_5d = now - timedelta(days=5)
    assert is_within_time_range(job_5d, "24h") is False
    assert is_within_time_range(job_5d, "48h") is False
    assert is_within_time_range(job_5d, "7d") is True

    # None posted date should return False
    assert is_within_time_range(None, "7d") is False


def test_format_time_ago():
    """Test human-readable time formatting."""
    now = datetime.now(UTC)

    # Just now
    assert format_time_ago(now) == "Just now"

    # Minutes ago
    assert format_time_ago(now - timedelta(minutes=5)) == "5 minutes ago"
    assert format_time_ago(now - timedelta(minutes=1)) == "1 minute ago"

    # Hours ago
    assert format_time_ago(now - timedelta(hours=3)) == "3 hours ago"
    assert format_time_ago(now - timedelta(hours=1)) == "1 hour ago"

    # Days ago
    assert format_time_ago(now - timedelta(days=2)) == "2 days ago"
    assert format_time_ago(now - timedelta(days=1)) == "1 day ago"

    # Weeks ago
    assert format_time_ago(now - timedelta(weeks=2)) == "2 weeks ago"

    # Months ago
    assert format_time_ago(now - timedelta(days=65)) == "2 months ago"

    # Unknown
    assert format_time_ago(None) == "Unknown"


def test_calculate_recency_score():
    """Test recency score calculation."""
    now = datetime.now(UTC)

    # < 24 hours = highest score
    assert calculate_recency_score(now - timedelta(hours=12)) == 1.0

    # < 48 hours = medium-high score
    assert calculate_recency_score(now - timedelta(hours=36)) == 0.8

    # < 7 days = medium score
    assert calculate_recency_score(now - timedelta(days=3)) == 0.6

    # 1-2 weeks = lower score
    assert calculate_recency_score(now - timedelta(days=10)) == 0.4

    # > 2 weeks = lowest score
    assert calculate_recency_score(now - timedelta(days=20)) == 0.2

    # Unknown date = low score but not 0
    assert calculate_recency_score(None) == 0.3


def test_time_ranges_constants():
    """Test that TIME_RANGES has expected values."""
    assert "24h" in TIME_RANGES
    assert "48h" in TIME_RANGES
    assert "7d" in TIME_RANGES
    assert TIME_RANGES["24h"] == timedelta(hours=24)
    assert TIME_RANGES["48h"] == timedelta(hours=48)
    assert TIME_RANGES["7d"] == timedelta(days=7)
