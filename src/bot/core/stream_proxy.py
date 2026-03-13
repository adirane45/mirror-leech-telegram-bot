from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from .config_manager import Config
from .redis_manager import redis_client


@dataclass
class StreamToken:
    token: str
    file_id: str
    file_name: str
    file_type: str
    mime_type: str
    expires_at: str


class StreamProxy:
    def __init__(self) -> None:
        self.enabled = bool(getattr(Config, "ENABLE_STREAM_LINKS", True))
        self.ttl_seconds = int(getattr(Config, "STREAM_LINK_TTL_SECONDS", 1800))
        self._memory: Dict[str, Dict[str, Any]] = {}

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _expires_at(self) -> datetime:
        return self._now() + timedelta(seconds=self.ttl_seconds)

    def _cache_key(self, token: str) -> str:
        return f"streamlink:{token}"

    def build_url(self, token: str) -> str:
        base_url = getattr(Config, "BASE_URL", "") or "http://localhost"
        base_url = base_url.rstrip("/")
        port = getattr(Config, "BASE_URL_PORT", 8060)
        if "://" in base_url and ":" not in base_url.split("//", 1)[1]:
            base_url = f"{base_url}:{port}"
        return f"{base_url}/stream/{token}"

    async def create_token(
        self,
        file_id: str,
        file_name: str,
        file_type: str,
        mime_type: str,
    ) -> Optional[StreamToken]:
        if not self.enabled:
            return None

        token = secrets.token_urlsafe(18)
        payload = {
            "file_id": file_id,
            "file_name": file_name,
            "file_type": file_type,
            "mime_type": mime_type,
            "expires_at": self._expires_at().isoformat(),
        }

        key = self._cache_key(token)
        if redis_client.is_enabled:
            await redis_client.set(key, payload, ttl=self.ttl_seconds)
        else:
            self._memory[key] = payload

        return StreamToken(
            token=token,
            file_id=file_id,
            file_name=file_name,
            file_type=file_type,
            mime_type=mime_type,
            expires_at=payload["expires_at"],
        )

    async def get_token(self, token: str) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        key = self._cache_key(token)
        payload = None
        if redis_client.is_enabled:
            payload = await redis_client.get(key)
        else:
            payload = self._memory.get(key)

        if not payload:
            return None
        expires_at = payload.get("expires_at")
        try:
            if expires_at and datetime.fromisoformat(expires_at) <= self._now():
                await self.delete_token(token)
                return None
        except ValueError:
            pass
        return payload

    async def delete_token(self, token: str) -> None:
        key = self._cache_key(token)
        if redis_client.is_enabled:
            await redis_client.delete(key)
        else:
            self._memory.pop(key, None)


stream_proxy = StreamProxy()
