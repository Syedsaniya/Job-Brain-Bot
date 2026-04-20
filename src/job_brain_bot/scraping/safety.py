import ipaddress
import socket
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
    host = parsed.hostname or ""
    if _is_private_host(host):
        return SafetyDecision(False, "private_host_blocked")
    return SafetyDecision(True, "ok")


def _is_private_host(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True
    for info in infos:
        try:
            addr = info[4][0]
            ip = ipaddress.ip_address(addr)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
        except ValueError:
            return True
    return False


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
