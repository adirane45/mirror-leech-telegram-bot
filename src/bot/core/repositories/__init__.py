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
    
    def __init__(self, client: Optional[aioredis.Redis] = None):
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
    
    def set_client(self, client: Optional[aioredis.Redis]):
        """Update the Redis client (for late initialization)"""
        self._client = client
        self._enabled = client is not None
    
    @abstractmethod
    async def close(self):
        """Close repository resources"""
        pass
    
    def _log_error(self, operation: str, error: Exception):
        """Log Redis errors consistently"""
        LOGGER.debug(f"Redis {operation} error: {error}")


# Import all repository classes for convenient access
from .cache_repository import CacheRepository
from .task_status_repository import TaskStatusRepository
from .session_repository import SessionRepository
from .rate_limit_repository import RateLimitRepository
from .stats_repository import StatsRepository

__all__ = [
    "BaseRepository",
    "CacheRepository",
    "TaskStatusRepository",
    "SessionRepository",
    "RateLimitRepository",
    "StatsRepository",
]

