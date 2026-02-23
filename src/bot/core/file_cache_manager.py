from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
from typing import Any, Dict, Optional, Tuple

from aiofiles import open as aiopen
from aiofiles.os import path as aiopath

from .. import LOGGER
from .config_manager import Config
from .redis_manager import redis_client
from ..helper.ext_utils.db_handler import database


@dataclass
class FileCacheEntry:
    cache_key: str
    hashes: Dict[str, str]
    size: int
    file_id: str
    file_unique_id: str
    file_type: str
    mime_type: str
    file_name: str
    created_at: str
    last_seen: str
    hits: int
    expires_at: str


class FileCacheManager:
    def __init__(self) -> None:
        self.enabled = bool(getattr(Config, "ENABLE_FILE_CACHE", True))
        self.ttl_days = int(getattr(Config, "FILE_CACHE_TTL_DAYS", 30))
        self.chunk_size = int(getattr(Config, "FILE_CACHE_HASH_CHUNK_SIZE", 8 * 1024 * 1024))

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _expires_at(self) -> datetime:
        return self._now() + timedelta(days=self.ttl_days)

    def _cache_key(self, hashes: Dict[str, str], size: int) -> Optional[str]:
        sha1 = hashes.get("sha1") or hashes.get("md5")
        if not sha1 or not size:
            return None
        return f"filecache:{sha1}:{size}"

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        expires_at = entry.get("expires_at")
        if not expires_at:
            return False
        try:
            return datetime.fromisoformat(expires_at) <= self._now()
        except ValueError:
            return False

    async def compute_hashes(self, file_path: str) -> Optional[Dict[str, str]]:
        if not await aiopath.exists(file_path):
            return None
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        blake3_hasher = None
        try:
            import blake3  # type: ignore
            blake3_hasher = blake3.blake3()
        except Exception:
            blake3_hasher = None

        async with aiopen(file_path, "rb") as handle:
            while True:
                chunk = await handle.read(self.chunk_size)
                if not chunk:
                    break
                md5.update(chunk)
                sha1.update(chunk)
                if blake3_hasher is not None:
                    blake3_hasher.update(chunk)

        hashes = {
            "md5": md5.hexdigest(),
            "sha1": sha1.hexdigest(),
        }
        if blake3_hasher is not None:
            hashes["blake3"] = blake3_hasher.hexdigest()
        return hashes

    async def get_cached_entry(
        self, hashes: Dict[str, str], size: int
    ) -> Optional[Dict[str, Any]]:
        if not self.enabled:
            return None
        cache_key = self._cache_key(hashes, size)
        if not cache_key:
            return None

        entry = None
        if redis_client.is_enabled:
            entry = await redis_client.get(cache_key)
        if entry is None and database.db is not None:
            entry = await database.db.file_cache.find_one({"_id": cache_key})
            if entry:
                entry.pop("_id", None)

        if not entry:
            return None

        if self._is_expired(entry):
            await self.delete_entry(cache_key)
            return None

        await self._touch_entry(cache_key, entry)
        return entry

    async def delete_entry(self, cache_key: str) -> None:
        if redis_client.is_enabled:
            await redis_client.delete(cache_key)
        if database.db is not None:
            await database.db.file_cache.delete_one({"_id": cache_key})

    async def store_entry(
        self,
        hashes: Dict[str, str],
        size: int,
        file_id: str,
        file_unique_id: str,
        file_type: str,
        mime_type: str,
        file_name: str,
    ) -> Optional[FileCacheEntry]:
        if not self.enabled:
            return None
        cache_key = self._cache_key(hashes, size)
        if not cache_key:
            return None

        now = self._now()
        entry = FileCacheEntry(
            cache_key=cache_key,
            hashes=hashes,
            size=size,
            file_id=file_id,
            file_unique_id=file_unique_id,
            file_type=file_type,
            mime_type=mime_type,
            file_name=file_name,
            created_at=now.isoformat(),
            last_seen=now.isoformat(),
            hits=0,
            expires_at=self._expires_at().isoformat(),
        )

        entry_dict = entry.__dict__.copy()
        if redis_client.is_enabled:
            await redis_client.set(cache_key, entry_dict, ttl=self.ttl_days * 86400)

        if database.db is not None:
            await database.db.file_cache.update_one(
                {"_id": cache_key},
                {"$set": entry_dict},
                upsert=True,
            )

        return entry

    async def _touch_entry(self, cache_key: str, entry: Dict[str, Any]) -> None:
        now = self._now().isoformat()
        hits = int(entry.get("hits", 0)) + 1
        entry["hits"] = hits
        entry["last_seen"] = now
        entry["expires_at"] = self._expires_at().isoformat()

        if redis_client.is_enabled:
            await redis_client.set(cache_key, entry, ttl=self.ttl_days * 86400)
        if database.db is not None:
            await database.db.file_cache.update_one(
                {"_id": cache_key},
                {"$set": {"last_seen": now, "expires_at": entry["expires_at"]}, "$inc": {"hits": 1}},
                upsert=True,
            )

    async def prepare_hashes(self, file_path: str) -> Optional[Tuple[Dict[str, str], int]]:
        if not self.enabled:
            return None
        try:
            size = await aiopath.getsize(file_path)
            hashes = await self.compute_hashes(file_path)
            if not hashes:
                return None
            return hashes, size
        except Exception as exc:
            LOGGER.debug(f"File cache hash failed for {file_path}: {exc}")
            return None


file_cache_manager = FileCacheManager()
