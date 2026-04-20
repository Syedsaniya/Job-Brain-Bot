"""Health check utilities for monitoring bot status."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from job_brain_bot.config import Settings
from job_brain_bot.db.session import build_engine


@dataclass
class HealthStatus:
    """Health check result."""

    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str = "0.2.0"
    checks: dict[str, Any] = field(default_factory=dict)
    uptime_seconds: float = 0.0


# Global start time for uptime calculation
_start_time = time.time()


def check_database_connection(settings: Settings) -> dict[str, Any]:
    """Check database connectivity and basic operations."""
    try:
        engine = build_engine(settings)
        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT 1"))
            row = result.fetchone()

            # Test table existence
            tables_result = conn.execute(
                text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            )
            tables = [row[0] for row in tables_result.fetchall()]

            return {
                "status": "ok",
                "query_test": row[0] == 1 if row else False,
                "tables_found": tables,
                "connection": "established",
            }
    except Exception as e:
        return {
            "status": "error",
            "error": "database_connection_failed",
            "connection": "failed",
        }


def check_telegram_api(token: str) -> dict[str, Any]:
    """Check Telegram API connectivity."""
    try:
        response = httpx.get(
            f"https://api.telegram.org/bot{token}/getMe",
            timeout=10,
        )
        data = response.json()

        if response.status_code == 200 and data.get("ok"):
            bot_info = data.get("result", {})
            return {
                "status": "ok",
                "bot_username": bot_info.get("username"),
                "bot_name": bot_info.get("first_name"),
                "can_read_messages": bot_info.get("can_read_all_group_messages", False),
            }
        else:
            return {
                "status": "error",
                "error": data.get("description", "Unknown error"),
                "code": response.status_code,
            }
    except Exception as e:
        return {
            "status": "error",
            "error": "telegram_api_check_failed",
        }


def check_scraping_connectivity() -> dict[str, Any]:
    """Check if scraping endpoints are reachable."""
    test_urls = [
        "https://www.google.com",
        "https://httpbin.org/get",
    ]

    results = {}
    for url in test_urls:
        try:
            response = httpx.get(url, timeout=10, follow_redirects=True)
            results[url] = {
                "status": "ok" if response.status_code < 400 else "error",
                "status_code": response.status_code,
            }
        except Exception as e:
            results[url] = {
                "status": "error",
                "error": "endpoint_check_failed",
            }

    all_ok = all(r["status"] == "ok" for r in results.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "endpoints": results,
    }


def perform_health_check(settings: Settings) -> HealthStatus:
    """Perform comprehensive health check."""
    checks = {}

    # Database check
    checks["database"] = check_database_connection(settings)

    # Telegram API check (only if token is available)
    if settings.telegram_bot_token and settings.telegram_bot_token != "replace_me":
        checks["telegram_api"] = check_telegram_api(settings.telegram_bot_token)
    else:
        checks["telegram_api"] = {"status": "skipped", "reason": "No token configured"}

    # Scraping connectivity check
    checks["scraping"] = check_scraping_connectivity()

    # AI modules check
    try:
        from job_brain_bot.ai_intelligence.analyzer import analyze_job_description
        from job_brain_bot.ai_intelligence.networking import generate_cold_message
        from job_brain_bot.ai_intelligence.skill_gap import analyze_skill_gaps

        # Quick test of AI modules
        test_analysis = analyze_job_description("Test Job", "Python, SQL required")
        checks["ai_modules"] = {
            "status": "ok",
            "analyzer": test_analysis is not None,
            "components": ["analyzer", "skill_gap", "networking"],
        }
    except Exception as e:
        checks["ai_modules"] = {
            "status": "error",
            "error": "ai_module_health_failed",
        }

    # Determine overall status
    failed_checks = [
        name for name, result in checks.items()
        if result.get("status") == "error"
    ]

    if "database" in failed_checks:
        overall_status = "unhealthy"
    elif len(failed_checks) > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    uptime = time.time() - _start_time

    return HealthStatus(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        checks=checks,
        uptime_seconds=uptime,
    )


def format_health_status(status: HealthStatus) -> str:
    """Format health status for display."""
    emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(status.status, "❓")

    lines = [
        f"{emoji} Health Status: {status.status.upper()}",
        f"Version: {status.version}",
        f"Uptime: {status.uptime_seconds:.1f}s",
        f"Timestamp: {status.timestamp}",
        "",
        "Component Status:",
    ]

    for name, check in status.checks.items():
        status_emoji = "✅" if check.get("status") == "ok" else "⚠️" if check.get("status") in ["skipped", "degraded"] else "❌"
        lines.append(f"  {status_emoji} {name}: {check.get('status', 'unknown')}")

    return "\n".join(lines)
