"""
Phase 10: Debrid Service Integrations

Mock integration layer for debrid services.
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DebridService(str, Enum):
    REAL_DEBRID = "real_debrid"
    ALLDEBRID = "alldebrid"
    PREMIUMIZE = "premiumize"


@dataclass
class DebridResult:
    original_url: str
    unrestricted_url: str
    success: bool
    service: DebridService
    cached: bool = True
    error: Optional[str] = None


@dataclass
class MagnetResult:
    magnet: str
    links: List[str]
    service: DebridService
    success: bool
    error: Optional[str] = None


class BaseDebridClient:
    def __init__(self, api_token: str, service: DebridService):
        self.api_token = api_token
        self.service = service
        self.stats: Dict[str, int] = {"requests": 0, "errors": 0}

    async def unrestrict_link(self, url: str) -> DebridResult:
        self.stats["requests"] += 1
        await asyncio.sleep(0.05)
        try:
            token = self._make_token(url)
            return DebridResult(
                original_url=url,
                unrestricted_url=f"https://debrid.example/{self.service.value}/{token}",
                success=True,
                service=self.service,
                cached=True,
            )
        except Exception as exc:
            self.stats["errors"] += 1
            return DebridResult(url, url, False, self.service, error=str(exc))

    async def add_magnet(self, magnet: str) -> MagnetResult:
        self.stats["requests"] += 1
        await asyncio.sleep(0.05)
        try:
            token = self._make_token(magnet)
            links = [f"https://debrid.example/{self.service.value}/{token}/{i}" for i in range(1, 4)]
            return MagnetResult(magnet=magnet, links=links, service=self.service, success=True)
        except Exception as exc:
            self.stats["errors"] += 1
            return MagnetResult(magnet=magnet, links=[], service=self.service, success=False, error=str(exc))

    async def get_user_status(self) -> Dict[str, str]:
        self.stats["requests"] += 1
        await asyncio.sleep(0.02)
        return {
            "service": self.service.value,
            "status": "active",
            "plan": "premium",
        }

    def _make_token(self, value: str) -> str:
        return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


class RealDebridClient(BaseDebridClient):
    def __init__(self, api_token: str):
        super().__init__(api_token, DebridService.REAL_DEBRID)


class AllDebridClient(BaseDebridClient):
    def __init__(self, api_token: str):
        super().__init__(api_token, DebridService.ALLDEBRID)


class PremiumizeClient(BaseDebridClient):
    def __init__(self, api_token: str):
        super().__init__(api_token, DebridService.PREMIUMIZE)


class DebridManager:
    """Facade for debrid services."""

    def __init__(self, service: DebridService, api_token: str):
        self.service = service
        self.client = self._build_client(service, api_token)

    async def unrestrict_link(self, url: str) -> DebridResult:
        return await self.client.unrestrict_link(url)

    async def add_magnet(self, magnet: str) -> MagnetResult:
        return await self.client.add_magnet(magnet)

    async def get_user_status(self) -> Dict[str, str]:
        return await self.client.get_user_status()

    def _build_client(self, service: DebridService, api_token: str) -> BaseDebridClient:
        if service == DebridService.REAL_DEBRID:
            return RealDebridClient(api_token)
        if service == DebridService.ALLDEBRID:
            return AllDebridClient(api_token)
        if service == DebridService.PREMIUMIZE:
            return PremiumizeClient(api_token)
        raise ValueError(f"Unsupported debrid service: {service}")
