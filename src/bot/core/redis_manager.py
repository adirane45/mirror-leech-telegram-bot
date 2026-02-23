"""
Refactored Redis Manager - Coordinator Pattern
Uses the Repository Pattern internally while maintaining backward compatibility
This is the new version that delegates to focused repositories
"""

from typing import Any, Optional, Union
from redis import asyncio as aioredis
from redis.exceptions import RedisError

from .. import LOGGER
from .config_manager import Config
from .repositories import (
    CacheRepository,
    TaskStatusRepository,
    SessionRepository,
    RateLimitRepository,
    StatsRepository,
)


class RedisManager:
    """
    Refactored Redis Manager using Repository Pattern
    Provides focused, maintainable components while maintaining backward compatibility
    
    Architecture:
    - CacheRepository: Core cache operations (get, set, delete, etc.)
    - TaskStatusRepository: Task-specific caching
    - SessionRepository: Session management
    - RateLimitRepository: Rate limiting
    - StatsRepository: Statistics and monitoring
    """
    
    _instance = None
    _client: Optional[aioredis.Redis] = None
    _enabled: bool = False
    
    # Repository instances
    _cache: Optional[CacheRepository] = None
    _task_status: Optional[TaskStatusRepository] = None
    _session: Optional[SessionRepository] = None
    _rate_limit: Optional[RateLimitRepository] = None
    _stats: Optional[StatsRepository] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self, host: str = "redis", port: int = 6379, db: int = 0) -> bool:
        """
        Initialize Redis connection and all repositories
        
        Args:
            host: Redis host (default: redis - docker service name)
            port: Redis port (default: 6379)
            db: Redis database number (default: 0)
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Check if Redis is enabled in config
            self._enabled = getattr(Config, 'ENABLE_REDIS_CACHE', False)
            
            if not self._enabled:
                LOGGER.info("Redis caching is DISABLED - using fallback mode")
                return False
            
            # Create Redis connection pool
            self._client = await aioredis.from_url(
                f"redis://{host}:{port}/{db}",
                encoding="utf-8",
                decode_responses=False,
                max_connections=50,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            
            # Test connection
            await self._client.ping()
            LOGGER.info(f"✅ Redis connected successfully at {host}:{port}")
            
            # Initialize all repositories with the shared client
            self._cache = CacheRepository(self._client)
            self._task_status = TaskStatusRepository(self._client)
            self._session = SessionRepository(self._client)
            self._rate_limit = RateLimitRepository(self._client)
            self._stats = StatsRepository(self._client)
            
            self._enabled = True
            return True
            
        except RedisError as e:
            LOGGER.warning(f"⚠️ Redis connection failed: {e}")
            LOGGER.warning("Continuing in fallback mode (no caching)")
            self._enabled = False
            self._client = None
            return False
        except Exception as e:
            LOGGER.error(f"Unexpected error initializing Redis: {e}")
            self._enabled = False
            return False
    
    async def close(self):
        """Close Redis connection gracefully"""
        try:
            if self._cache:
                await self._cache.close()
            if self._task_status:
                await self._task_status.close()
            if self._session:
                await self._session.close()
            if self._rate_limit:
                await self._rate_limit.close()
            if self._stats:
                await self._stats.close()
            
            if self._client:
                await self._client.close()
                LOGGER.info("Redis connection closed")
        except Exception as e:
            LOGGER.error(f"Error closing Redis: {e}")
    
    @property
    def is_enabled(self) -> bool:
        """Check if Redis is enabled and connected"""
        return self._enabled and self._client is not None
    
    # ==================== REPOSITORY ACCESS (Delegated Methods) ====================
    
    # Cache Repository delegation
    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        """Get value from cache - delegates to CacheRepository"""
        if not self._cache:
            return default
        return await self._cache.get(key, default)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache - delegates to CacheRepository"""
        if not self._cache:
            return False
        return await self._cache.set(key, value, ttl)
    
    async def delete(self, *keys: str) -> int:
        """Delete keys from cache - delegates to CacheRepository"""
        if not self._cache:
            return 0
        return await self._cache.delete(*keys)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists - delegates to CacheRepository"""
        if not self._cache:
            return False
        return await self._cache.exists(key)
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiry for key - delegates to CacheRepository"""
        if not self._cache:
            return False
        return await self._cache.expire(key, ttl)
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter - delegates to CacheRepository"""
        if not self._cache:
            return None
        return await self._cache.increment(key, amount)
    
    async def get_many(self, *keys: str) -> dict:
        """Get multiple values - delegates to CacheRepository"""
        if not self._cache:
            return {}
        return await self._cache.get_many(*keys)
    
    async def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set multiple values - delegates to CacheRepository"""
        if not self._cache:
            return False
        return await self._cache.set_many(mapping, ttl)
    
    async def flush_pattern(self, pattern: str) -> int:
        """Flush keys by pattern - delegates to CacheRepository"""
        if not self._cache:
            return 0
        return await self._cache.flush_pattern(pattern)
    
    # Task Status Repository delegation
    async def cache_task_status(self, task_id: str, status: dict, ttl: int = 300) -> bool:
        """Cache task status - delegates to TaskStatusRepository"""
        if not self._task_status:
            return False
        return await self._task_status.cache_task_status(task_id, status, ttl)
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get task status - delegates to TaskStatusRepository"""
        if not self._task_status:
            return None
        return await self._task_status.get_task_status(task_id)
    
    async def invalidate_task_cache(self, task_id: str) -> bool:
        """Invalidate task cache - delegates to TaskStatusRepository"""
        if not self._task_status:
            return False
        return await self._task_status.invalidate_task_status(task_id)
    
    # Rate Limiting Repository delegation
    async def check_rate_limit(
        self, 
        user_id: int, 
        action: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, int]:
        """Check rate limit - delegates to RateLimitRepository"""
        if not self._rate_limit:
            return True, limit
        return await self._rate_limit.check_rate_limit(user_id, action, limit, window)
    
    # Session Repository delegation
    async def create_session(self, session_id: str, data: dict, ttl: int = 3600) -> bool:
        """Create session - delegates to SessionRepository"""
        if not self._session:
            return False
        return await self._session.create_session(session_id, data, ttl)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session - delegates to SessionRepository"""
        if not self._session:
            return None
        return await self._session.get_session(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session - delegates to SessionRepository"""
        if not self._session:
            return False
        return await self._session.delete_session(session_id)
    
    # Statistics Repository delegation
    async def get_stats(self) -> dict:
        """Get statistics - delegates to StatsRepository"""
        if not self._stats:
            return {"enabled": False}
        return await self._stats.get_stats()
    
    # ==================== REPOSITORY ACCESS (Direct Access) ====================
    
    @property
    def cache(self) -> Optional[CacheRepository]:
        """Direct access to cache repository"""
        return self._cache
    
    @property
    def task_status(self) -> Optional[TaskStatusRepository]:
        """Direct access to task status repository"""
        return self._task_status
    
    @property
    def session(self) -> Optional[SessionRepository]:
        """Direct access to session repository"""
        return self._session
    
    @property
    def rate_limit(self) -> Optional[RateLimitRepository]:
        """Direct access to rate limit repository"""
        return self._rate_limit
    
    @property
    def stats(self) -> Optional[StatsRepository]:
        """Direct access to statistics repository"""
        return self._stats


# Global instance
redis_client = RedisManager()
