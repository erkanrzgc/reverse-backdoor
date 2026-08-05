"""Malleable HTTP C2 profiles — configurable headers, URIs, behaviors."""

from dataclasses import dataclass, field
from typing import Optional
import random


@dataclass
class HttpProfile:
    name: str = "default"
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    poll_uri: str = "/poll"
    push_uri: str = "/push"
    stage_uri: str = "/stage"
    poll_method: str = "GET"
    push_method: str = "POST"
    extra_headers: dict = field(default_factory=dict)
    cookie: str = ""
    jitter: float = 0.3
    sleep: float = 5.0

    def get_headers(self) -> dict:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        headers.update(self.extra_headers)
        return headers

    def get_uris(self) -> tuple:
        return self.poll_uri, self.push_uri, self.stage_uri


PROFILES = {
    "default": HttpProfile(),
    "chrome": HttpProfile(
        name="chrome",
        poll_uri="/api/v1/status",
        push_uri="/api/v1/report",
        stage_uri="/api/v1/update",
        extra_headers={"Origin": "https://www.google.com"},
        sleep=10,
    ),
    "cdn": HttpProfile(
        name="cdn",
        poll_uri="/assets/bundle.js",
        push_uri="/assets/analytics.gif",
        stage_uri="/assets/font.woff2",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        extra_headers={"Referer": "https://cdn.example.com/"},
        sleep=30,
    ),
    "api": HttpProfile(
        name="api",
        poll_uri="/graphql",
        push_uri="/graphql",
        stage_uri="/graphql",
        poll_method="POST",
        extra_headers={"Content-Type": "application/json"},
        sleep=15,
    ),
    "office": HttpProfile(
        name="office",
        poll_uri="/EWS/Exchange.asmx",
        push_uri="/autodiscover/autodiscover.xml",
        stage_uri="/owa/auth/15.2.1258/themes/resources/favicon.ico",
        user_agent="Microsoft Office/16.0 (Windows NT 10.0; Microsoft Outlook 16.0.12026; Pro)",
        extra_headers={"X-OWA-Version": "15.2.1258.16"},
        sleep=60,
    ),
    "stealth": HttpProfile(
        name="stealth",
        poll_uri="/",
        push_uri="/",
        stage_uri="/robots.txt",
        user_agent="",
        sleep=120,
        jitter=0.5,
    ),
}


def get_profile(name: str = "default") -> HttpProfile:
    return PROFILES.get(name, PROFILES["default"])


def list_profiles() -> str:
    lines = ["[*] Available HTTP profiles:"]
    for name, p in PROFILES.items():
        lines.append(f"  {name}: {p.poll_uri} / {p.push_uri} (sleep={p.sleep}s)")
    return '\n'.join(lines)
