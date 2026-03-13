"""
Cache Repository - Handles core caching operations
Lower-level cache get/set/delete operations
"""

import pickle
from typing import Any, Dict, Optional

from redis.exceptions import RedisError

from bot import LOGGER

from . import BaseRepository


class CacheRepository(BaseRepository):
    """Handles core cache operations"""

    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get value from cache
        Returns default if Redis is disabled or key not found
        """
        if not self.is_enabled:
            return default
        assert self._client is not None

        try:
            value = await self._client.get(key)
            if value is None:
                return default

            # Try to unpickle, fallback to decode
            try:
                return pickle.loads(value)
            except (pickle.UnpicklingError, EOFError, TypeError) as e:
                LOGGER.debug(f"Could not unpickle value for {key}, returning as string: {e}")
                return value.decode('utf-8')

        except RedisError as e:
            self._log_error("GET", e)
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache (will be pickled)
            ttl: Time to live in seconds (None = no expiry)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_enabled:
            return False
        assert self._client is not None

        try:
            # Pickle complex objects, encode strings
            if isinstance(value, (str, int, float)):
                data = str(value).encode('utf-8')
            else:
                data = pickle.dumps(value)

            if ttl:
                await self._client.setex(key, ttl, data)
            else:
                await self._client.set(key, data)

            return True

        except RedisError as e:
            self._log_error("SET", e)
            return False

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from cache"""
        if not self.is_enabled:
            return 0
        assert self._client is not None

        try:
            return int(await self._client.delete(*keys))
        except RedisError as e:
            self._log_error("DELETE", e)
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_enabled:
            return False
        assert self._client is not None

        try:
            return int(await self._client.exists(key)) > 0
        except RedisError:
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiry time for a key"""
        if not self.is_enabled:
            return False
        assert self._client is not None

        try:
            return bool(await self._client.expire(key, ttl))
        except RedisError:
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        if not self.is_enabled:
            return None
        assert self._client is not None

        try:
            return int(await self._client.incrby(key, amount))
        except RedisError as e:
            self._log_error("INCR", e)
            return None

    async def get_many(self, *keys: str) -> Dict[str, Any]:
        """Get multiple values at once"""
        if not self.is_enabled:
            return {}
        assert self._client is not None

        try:
            values = await self._client.mget(*keys)
            result: Dict[str, Any] = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = pickle.loads(value)
                    except (pickle.UnpicklingError, EOFError, TypeError) as e:
                        LOGGER.debug(f"Could not unpickle value for {key}: {e}")
                        result[key] = value.decode('utf-8')
            return result
        except RedisError:
            return {}

    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs at once"""
        if not self.is_enabled:
            return False
        assert self._client is not None

        try:
            pipeline = self._client.pipeline()
            for key, value in mapping.items():
                data = pickle.dumps(value) if not isinstance(value, (str, int)) else str(value)
                if ttl:
                    pipeline.setex(key, ttl, data)
                else:
                    pipeline.set(key, data)
            await pipeline.execute()
            return True
        except RedisError:
            return False

    async def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if not self.is_enabled:
            return 0
        assert self._client is not None

        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)

            if keys:
                return int(await self._client.delete(*keys))
            return 0
        except RedisError:
            return 0

    async def close(self) -> None:
        """Cleanup cache repository"""
        # Nothing special to cleanup
