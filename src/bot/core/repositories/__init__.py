"""
Redis Repository Pattern - Base Class
Provides interface for all Redis repositories
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from redis import asyncio as aioredis
from redis.exceptions import RedisError

from bot import LOGGER


class BaseRepository(ABC):
    """Base class for all Redis repositories"""

    def __init__(self, client: Optional[aioredis.Redis] = None) -> None:
        """
        Args:
            client: Redis client instance (shared across all repositories)
        """
        self._client = client
        self._enabled = client is not None

    @property
    def is_enabled(self) -> bool:
        """Check if Redis is enabled"""
        return self._enabled and self._client is not None

    def set_client(self, client: Optional[aioredis.Redis]) -> None:
        """Update the Redis client (for late initialization)"""
        self._client = client
        self._enabled = client is not None

    @abstractmethod
    async def close(self) -> None:
        """Close repository resources"""

    def _log_error(self, operation: str, error: Exception) -> None:
        """Log Redis errors consistently"""
        LOGGER.debug(f"Redis {operation} error: {error}")


# Import all repository classes for convenient access
from .cache_repository import CacheRepository
from .rate_limit_repository import RateLimitRepository
from .session_repository import SessionRepository
from .stats_repository import StatsRepository
from .task_status_repository import TaskStatusRepository

__all__ = [
    "BaseRepository",
    "CacheRepository",
    "TaskStatusRepository",
    "SessionRepository",
    "RateLimitRepository",
    "StatsRepository",
]
