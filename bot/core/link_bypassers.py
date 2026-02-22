"""
Phase 10: Link Bypassers

Normalizes shorteners, ad wrappers, and protected links.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import parse_qs, unquote, urlparse
import asyncio
import hashlib
import logging
import time

logger = logging.getLogger(__name__)


@dataclass
class BypassResult:
    original_url: str
    final_url: str
    bypassed: bool
    service: str
    duration_seconds: float
    reason: Optional[str] = None


class BaseBypasser:
    name = "base"
    domains: List[str] = []

    def supports(self, url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return any(domain in host for domain in self.domains)

    def bypass_sync(self, url: str) -> BypassResult:
        return BypassResult(
            original_url=url,
            final_url=url,
            bypassed=False,
            service=self.name,
            duration_seconds=0.0,
            reason="unsupported",
        )


class ShortenerBypasser(BaseBypasser):
    name = "shortener"
    domains = ["bit.ly", "tinyurl.com", "t.co", "short.link"]

    def bypass_sync(self, url: str) -> BypassResult:
        start = time.perf_counter()
        target = _extract_target_param(url)
        if not target:
            target = _fake_resolve(url)
            reason = "resolved"
        else:
            reason = "query"
        return BypassResult(
            original_url=url,
            final_url=target,
            bypassed=target != url,
            service=self.name,
            duration_seconds=time.perf_counter() - start,
            reason=reason,
        )


class AdBypasser(BaseBypasser):
    name = "ad"
    domains = ["adf.ly", "linkvertise.com", "shrink.me"]

    def bypass_sync(self, url: str) -> BypassResult:
        start = time.perf_counter()
        target = _extract_target_param(url) or _fake_resolve(url)
        return BypassResult(
            original_url=url,
            final_url=target,
            bypassed=target != url,
            service=self.name,
            duration_seconds=time.perf_counter() - start,
            reason="skip",
        )


class FileHostBypasser(BaseBypasser):
    name = "filehost"
    domains = ["mediafire.com", "mega.nz", "dropbox.com", "1drv.ms"]

    def bypass_sync(self, url: str) -> BypassResult:
        start = time.perf_counter()
        target = _extract_target_param(url) or _fake_resolve(url)
        return BypassResult(
            original_url=url,
            final_url=target,
            bypassed=target != url,
            service=self.name,
            duration_seconds=time.perf_counter() - start,
            reason="direct",
        )


class StreamingBypasser(BaseBypasser):
    name = "streaming"
    domains = ["youtube.com", "vimeo.com", "twitch.tv", "tiktok.com"]

    def bypass_sync(self, url: str) -> BypassResult:
        start = time.perf_counter()
        target = url
        return BypassResult(
            original_url=url,
            final_url=target,
            bypassed=False,
            service=self.name,
            duration_seconds=time.perf_counter() - start,
            reason="metadata",
        )


class LinkBypassEngine:
    """Select and run link bypassers."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.bypassers: List[BaseBypasser] = [
            ShortenerBypasser(),
            AdBypasser(),
            FileHostBypasser(),
            StreamingBypasser(),
        ]
        self.stats: Dict[str, int] = {
            "total": 0,
            "bypassed": 0,
            "skipped": 0,
        }

    async def normalize_link(self, url: str) -> BypassResult:
        await asyncio.sleep(0)
        return self.normalize_link_sync(url, return_result=True)

    def normalize_link_sync(self, url: str, return_result: bool = False):
        result = self._run_bypass(url)
        if return_result:
            return result
        return result.final_url

    def _run_bypass(self, url: str) -> BypassResult:
        if not self.enabled:
            self.stats["skipped"] += 1
            return BypassResult(url, url, False, "disabled", 0.0, "disabled")

        self.stats["total"] += 1
        for bypasser in self.bypassers:
            if bypasser.supports(url):
                result = bypasser.bypass_sync(url)
                if result.bypassed:
                    self.stats["bypassed"] += 1
                return result

        self.stats["skipped"] += 1
        return BypassResult(url, url, False, "none", 0.0, "no_match")

    def get_stats(self) -> Dict[str, int]:
        return dict(self.stats)


def _extract_target_param(url: str) -> Optional[str]:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    for key in ("url", "target", "u", "redirect"):
        if key in params and params[key]:
            return unquote(params[key][0])
    return None


def _fake_resolve(url: str) -> str:
    digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:8]
    return f"https://resolved.example/{digest}"