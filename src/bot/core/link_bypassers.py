"""
Phase 10: Link Bypassers

Normalizes shorteners, ad wrappers, and protected links.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from urllib.parse import parse_qs, unquote, urljoin, urlparse
import asyncio
import logging
import re
import time

import requests

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
    domains = [
        "bit.ly",
        "tinyurl.com",
        "t.co",
        "short.link",
        "goo.gl",
        "is.gd",
        "v.gd",
        "ow.ly",
        "buff.ly",
        "rebrand.ly",
        "bl.ink",
        "tiny.cc",
        "s.id",
        "soo.gd",
        "s2r.co",
        "cutt.ly",
        "rb.gy",
        "shorte.st",
        "adfoc.us",
        "clk.sh",
        "cutt.us",
        "chilp.it",
        "zi.pe",
        "shorturl.at",
        "gg.gg",
        "lc.chat",
        "lnk.to",
        "trib.al",
        "po.st",
        "mcaf.ee",
        "cutt.us",
        "t.ly",
        "tiny.one",
    ]

    def bypass_sync(self, url: str) -> BypassResult:
        start = time.perf_counter()
        target, reason = _resolve_real_url(url)
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
    domains = [
        "adf.ly",
        "linkvertise.com",
        "shrink.me",
        "ouo.io",
        "ouo.press",
        "exe.io",
        "fc.lc",
        "bc.vc",
        "adfoc.us",
        "adshort.co",
        "link-hub.net",
        "linksly.co",
    ]

    def bypass_sync(self, url: str) -> BypassResult:
        start = time.perf_counter()
        target, reason = _resolve_real_url(url)
        return BypassResult(
            original_url=url,
            final_url=target,
            bypassed=target != url,
            service=self.name,
            duration_seconds=time.perf_counter() - start,
            reason=reason,
        )


class FileHostBypasser(BaseBypasser):
    name = "filehost"
    domains = ["mediafire.com", "mega.nz", "dropbox.com", "1drv.ms"]

    def bypass_sync(self, url: str) -> BypassResult:
        start = time.perf_counter()
        target, reason = _resolve_real_url(url)
        return BypassResult(
            original_url=url,
            final_url=target,
            bypassed=target != url,
            service=self.name,
            duration_seconds=time.perf_counter() - start,
            reason=reason,
        )


class StreamingBypasser(BaseBypasser):
    name = "streaming"
    domains = ["youtube.com", "vimeo.com", "twitch.tv", "tiktok.com"]

    def bypass_sync(self, url: str) -> BypassResult:
        start = time.perf_counter()
        target, reason = _resolve_real_url(url)
        return BypassResult(
            original_url=url,
            final_url=target,
            bypassed=target != url,
            service=self.name,
            duration_seconds=time.perf_counter() - start,
            reason=reason,
        )


class GenericRedirectBypasser(BaseBypasser):
    name = "generic"
    domains = []

    def supports(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    def bypass_sync(self, url: str) -> BypassResult:
        start = time.perf_counter()
        target, reason = _resolve_real_url(url)
        return BypassResult(
            original_url=url,
            final_url=target,
            bypassed=target != url,
            service=self.name,
            duration_seconds=time.perf_counter() - start,
            reason=reason,
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
            GenericRedirectBypasser(),
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
    for key in (
        "url",
        "target",
        "u",
        "redirect",
        "r",
        "to",
        "dest",
        "destination",
        "redirect_url",
        "redirect_uri",
        "next",
        "continue",
        "out",
        "go",
        "link",
    ):
        if key in params and params[key]:
            candidate = unquote(params[key][0]).strip()
            parsed_candidate = urlparse(candidate)
            if parsed_candidate.scheme in {"http", "https"} and parsed_candidate.netloc:
                return candidate
    return None


def _resolve_real_url(url: str, max_hops: int = 10, timeout: int = 12) -> tuple[str, str]:
    if not _is_http_url(url):
        return url, "not_http"

    current = url
    visited: Set[str] = set()
    changed = False
    reason = "unchanged"

    for _ in range(max_hops):
        if current in visited:
            return current, "loop_detected"
        visited.add(current)

        extracted = _extract_target_param(current)
        if extracted and extracted != current:
            current = extracted
            changed = True
            reason = "query_param"
            continue

        try:
            next_url, network_reason = _resolve_one_hop(current, timeout=timeout)
        except Exception as e:
            logger.debug("Bypass request failed for %s: %s", current, e)
            return current, "network_error" if changed else "request_failed"

        if not next_url or next_url == current:
            return current, reason if changed else network_reason

        current = next_url
        changed = True
        reason = network_reason

    return current, "max_hops"


def _resolve_one_hop(url: str, timeout: int) -> tuple[str, str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    with requests.Session() as session:
        response = session.get(
            url,
            allow_redirects=False,
            timeout=timeout,
            headers=headers,
            stream=True,
        )

        if 300 <= response.status_code < 400:
            location = response.headers.get("Location")
            if location:
                return _normalize_redirect(url, location), "http_redirect"
            return url, "redirect_no_location"

        target = _extract_target_param(str(response.url))
        if target and target != str(response.url):
            return target, "response_url_param"

        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type.lower():
            body = response.text[:100000]
            meta_target = _extract_meta_refresh_target(body, str(response.url))
            if meta_target:
                return meta_target, "meta_refresh"

            js_target = _extract_js_redirect_target(body, str(response.url))
            if js_target:
                return js_target, "js_redirect"

    return str(response.url), "final"


def _normalize_redirect(base_url: str, location: str) -> str:
    location = location.strip()
    if location.startswith("//"):
        scheme = urlparse(base_url).scheme or "https"
        return f"{scheme}:{location}"
    return urljoin(base_url, location)


def _extract_meta_refresh_target(html: str, base_url: str) -> Optional[str]:
    match = re.search(
        r"<meta[^>]+http-equiv=[\"']?refresh[\"']?[^>]+content=[\"'][^\"']*url=([^\"'>]+)",
        html,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    candidate = unquote(match.group(1).strip())
    if not candidate:
        return None
    normalized = _normalize_redirect(base_url, candidate)
    return normalized if _is_http_url(normalized) else None


def _extract_js_redirect_target(html: str, base_url: str) -> Optional[str]:
    patterns = [
        r"location\.href\s*=\s*['\"]([^'\"]+)['\"]",
        r"window\.location\s*=\s*['\"]([^'\"]+)['\"]",
        r"window\.location\.replace\(['\"]([^'\"]+)['\"]\)",
        r"window\.open\(['\"]([^'\"]+)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.IGNORECASE)
        if not match:
            continue
        candidate = unquote(match.group(1).strip())
        if not candidate:
            continue
        normalized = _normalize_redirect(base_url, candidate)
        if _is_http_url(normalized):
            return normalized
    return None


def _is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)