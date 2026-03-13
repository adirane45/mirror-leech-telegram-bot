"""
Intelligent Client Selection - Automatic routing to best download client
Routes downloads to Aria2, qBittorrent, or Sabnzbd based on:
- Link type (direct/torrent/nzb)
- Current client load
- Success history
- Network conditions

Enhanced by: justadi
Date: February 8, 2026
"""

import asyncio
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .. import LOGGER
from .client_selector_models import ClientType, LinkType


class ClientMetrics:
    """Track client performance metrics"""

    def __init__(self) -> None:
        self.aria2_active = 0
        self.qbit_active = 0
        self.sabnzbd_active = 0

        # Success rates (0-100%)
        self.aria2_success_rate = 95.0
        self.qbit_success_rate = 92.0
        self.sabnzbd_success_rate = 88.0

        # Last error times
        self.aria2_last_error: Optional[datetime] = None
        self.qbit_last_error: Optional[datetime] = None
        self.sabnzbd_last_error: Optional[datetime] = None

        # Avg speeds (bytes/sec)
        self.aria2_avg_speed = 2_000_000  # 2 MB/s default
        self.qbit_avg_speed = 1_500_000   # 1.5 MB/s default
        self.sabnzbd_avg_speed = 1_200_000  # 1.2 MB/s default

    def is_client_healthy(self, client: ClientType) -> bool:
        """Check if client is healthy"""
        last_error = {
            ClientType.ARIA2: self.aria2_last_error,
            ClientType.QBITTORRENT: self.qbit_last_error,
            ClientType.SABNZBD: self.sabnzbd_last_error,
        }[client]

        # Unhealthy if errored in last 5 minutes
        if last_error and (datetime.now() - last_error).total_seconds() < 300:
            return False
        return True

    def get_load_percentage(self, client: ClientType) -> float:
        """Get current load % (0-100) based on active tasks"""
        active_count = {
            ClientType.ARIA2: self.aria2_active,
            ClientType.QBITTORRENT: self.qbit_active,
            ClientType.SABNZBD: self.sabnzbd_active,
        }[client]

        # Max 50 concurrent tasks per client
        return min(100.0, (active_count / 50.0) * 100.0)

    def get_success_rate(self, client: ClientType) -> float:
        """Get success rate for client (0-100%)"""
        return {
            ClientType.ARIA2: self.aria2_success_rate,
            ClientType.QBITTORRENT: self.qbit_success_rate,
            ClientType.SABNZBD: self.sabnzbd_success_rate,
        }[client]

    def log_error(self, client: ClientType) -> None:
        """Record error for client and reduce success rate"""
        error_attrs = {
            ClientType.ARIA2: ("aria2_last_error", "aria2_success_rate"),
            ClientType.QBITTORRENT: ("qbit_last_error", "qbit_success_rate"),
            ClientType.SABNZBD: ("sabnzbd_last_error", "sabnzbd_success_rate"),
        }

        error_field, rate_field = error_attrs[client]
        setattr(self, error_field, datetime.now())

        # Reduce success rate (recover over time)
        current_rate = getattr(self, rate_field)
        setattr(self, rate_field, max(70.0, current_rate - 5.0))

    def log_success(self, client: ClientType) -> None:
        """Record success and increase success rate"""
        rate_field = {
            ClientType.ARIA2: "aria2_success_rate",
            ClientType.QBITTORRENT: "qbit_success_rate",
            ClientType.SABNZBD: "sabnzbd_success_rate",
        }[client]

        current_rate = getattr(self, rate_field)
        setattr(self, rate_field, min(99.0, current_rate + 1.0))


class ClientSelector:
    """Singleton intelligent client selector"""

    _instance: Optional['ClientSelector'] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> 'ClientSelector':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self.metrics = ClientMetrics()
        LOGGER.info("✅ Client Selector initialized")

    @classmethod
    def get_instance(cls) -> 'ClientSelector':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _is_torrent_link(self, link: str) -> bool:
        return link.startswith("magnet:") or link.endswith(".torrent")

    def _is_nzb_link(self, link: str) -> bool:
        return link.endswith(".nzb") or ("nzb" in link and ("sabnzbd" in link or "usenet" in link))

    def _is_gdrive_link(self, link: str) -> bool:
        return "drive.google.com" in link or "gdrive" in link

    def _is_mediafire_link(self, link: str) -> bool:
        return "mediafire.com" in link

    def _is_archive_link(self, link: str) -> bool:
        return bool(re.search(r'\.(zip|7z|rar|tar\.gz)$', link))

    def _is_direct_http_link(self, link: str) -> bool:
        return link.startswith(("http://", "https://"))

    # ==================== LINK TYPE DETECTION ====================

    def _detect_link_type(self, link: str) -> LinkType:
        """Detect link type from URL/magnet"""
        link = link.lower().strip()

        if self._is_torrent_link(link):
            return LinkType.TORRENT

        if self._is_nzb_link(link):
            return LinkType.NZB

        if self._is_gdrive_link(link):
            return LinkType.GDRIVE

        if self._is_mediafire_link(link):
            return LinkType.MEDIAFIRE

        if self._is_archive_link(link):
            return LinkType.ZIP_ARCHIVE

        if self._is_direct_http_link(link):
            return LinkType.DIRECT

        return LinkType.UNKNOWN

    # ==================== CLIENT SCORING ====================

    def _calculate_client_score(self, client: ClientType, link_type: LinkType) -> float:
        """
        Calculate suitability score for client (0-100)
        Higher = better choice
        """
        score = 50.0  # Base score

        # Health bonus
        if self.metrics.is_client_healthy(client):
            score += 15.0
        else:
            score -= 30.0  # Heavily penalize unhealthy clients

        # Load penalty (lower load = higher score)
        load = self.metrics.get_load_percentage(client)
        score -= (load * 0.2)  # Max 10 point penalty

        # Success rate bonus
        success_rate = self.metrics.get_success_rate(client)
        score += (success_rate - 80.0) * 0.5  # Bonus/penalty based on rate

        # Link-type affinity bonuses
        if link_type == LinkType.TORRENT:
            if client == ClientType.QBITTORRENT:
                score += 25.0  # Specialist bonus
            elif client == ClientType.ARIA2:
                score += 10.0  # Can handle it
            else:
                score -= 15.0  # Not ideal

        elif link_type == LinkType.NZB:
            if client == ClientType.SABNZBD:
                score += 25.0  # Specialist bonus
            else:
                score -= 20.0  # Can't handle NZB

        elif link_type in (LinkType.DIRECT, LinkType.GDRIVE, LinkType.MEDIAFIRE, LinkType.ZIP_ARCHIVE):
            if client == ClientType.ARIA2:
                score += 20.0  # Excellent for direct links
            elif client == ClientType.QBITTORRENT:
                score += 5.0
            else:
                score -= 10.0

        return max(0.0, min(100.0, score))

    # ==================== SELECTION LOGIC ====================

    async def select_client(self, link: str, user_id: Optional[int] = None) -> Tuple[ClientType, str]:
        """
        Select best client for download

        Returns:
            Tuple[ClientType, reason_string]
        """
        async with self._lock:
            link_type = self._detect_link_type(link)

            scores = {}
            reasons = {}

            # Score each client
            for client in ClientType:
                score = self._calculate_client_score(client, link_type)
                scores[client] = score
                reasons[client] = self._build_reason(client, link_type, score)

            # Select highest scoring
            selected = max(scores.items(), key=lambda x: x[1])[0]
            reason = reasons[selected]

            LOGGER.info(
                f"👤 User {user_id}: Selected {selected.value.upper()} "
                f"for {link_type.value} ({reason})"
            )

            return selected, reason

    def _build_reason(self, client: ClientType, link_type: LinkType, score: float) -> str:
        """Build human-readable reason for selection"""
        reasons = []

        load = self.metrics.get_load_percentage(client)
        success = self.metrics.get_success_rate(client)

        type_reason = self._build_type_reason(client, link_type)
        if type_reason:
            reasons.append(type_reason)

        load_reason = self._build_load_reason(load)
        if load_reason:
            reasons.append(load_reason)

        health_reason = self._build_health_reason(client)
        if health_reason:
            reasons.append(health_reason)

        success_reason = self._build_success_reason(success)
        if success_reason:
            reasons.append(success_reason)

        return ", ".join(reasons) if reasons else f"score {score:.1f}"

    def _build_type_reason(self, client: ClientType, link_type: LinkType) -> str:
        if link_type == LinkType.TORRENT and client == ClientType.QBITTORRENT:
            return "torrent specialist"
        if link_type == LinkType.NZB and client == ClientType.SABNZBD:
            return "usenet specialist"
        if link_type in (LinkType.DIRECT, LinkType.GDRIVE) and client == ClientType.ARIA2:
            return "direct link specialist"
        return ""

    def _build_load_reason(self, load: float) -> str:
        if load < 30:
            return "low load"
        if load > 70:
            return "high load"
        return ""

    def _build_health_reason(self, client: ClientType) -> str:
        if self.metrics.is_client_healthy(client):
            return "healthy"
        return ""

    def _build_success_reason(self, success: float) -> str:
        if success > 95:
            return f"{success:.0f}% success rate"
        if success < 85:
            return f"recovering ({success:.0f}%)"
        return ""

    # ==================== FEEDBACK ====================

    def record_download(self, client: ClientType, success: bool, duration: float, size_mb: float) -> None:
        """Record download result for metrics"""
        if success:
            self.metrics.log_success(client)
            speed = (size_mb / duration) if duration > 0 else 0

            # Update average speed
            speed_field = {
                ClientType.ARIA2: "aria2_avg_speed",
                ClientType.QBITTORRENT: "qbit_avg_speed",
                ClientType.SABNZBD: "sabnzbd_avg_speed",
            }[client]

            current_avg = getattr(self.metrics, speed_field, 0)
            new_avg = (current_avg * 0.7) + (speed * 1_000_000 * 0.3)  # Weighted average
            setattr(self.metrics, speed_field, new_avg)

            LOGGER.debug(f"✅ {client.value}: Success ({size_mb:.1f}MB in {duration:.1f}s)")
        else:
            self.metrics.log_error(client)
            LOGGER.warning(f"❌ {client.value}: Failed")

    def update_active_count(self, client: ClientType, count: int) -> None:
        """Update active task count for client"""
        field = {
            ClientType.ARIA2: "aria2_active",
            ClientType.QBITTORRENT: "qbit_active",
            ClientType.SABNZBD: "sabnzbd_active",
        }[client]
        setattr(self.metrics, field, count)

    # ==================== STATUS ====================

    def get_status(self) -> Dict[str, Any]:
        """Get current client statuses"""
        return {
            "aria2": {
                "active": self.metrics.aria2_active,
                "load_percent": self.metrics.get_load_percentage(ClientType.ARIA2),
                "success_rate": self.metrics.aria2_success_rate,
                "healthy": self.metrics.is_client_healthy(ClientType.ARIA2),
                "avg_speed_mbps": self.metrics.aria2_avg_speed / 1_000_000,
            },
            "qbittorrent": {
                "active": self.metrics.qbit_active,
                "load_percent": self.metrics.get_load_percentage(ClientType.QBITTORRENT),
                "success_rate": self.metrics.qbit_success_rate,
                "healthy": self.metrics.is_client_healthy(ClientType.QBITTORRENT),
                "avg_speed_mbps": self.metrics.qbit_avg_speed / 1_000_000,
            },
            "sabnzbd": {
                "active": self.metrics.sabnzbd_active,
                "load_percent": self.metrics.get_load_percentage(ClientType.SABNZBD),
                "success_rate": self.metrics.sabnzbd_success_rate,
                "healthy": self.metrics.is_client_healthy(ClientType.SABNZBD),
                "avg_speed_mbps": self.metrics.sabnzbd_avg_speed / 1_000_000,
            },
        }


# Global instance
client_selector = ClientSelector.get_instance()
