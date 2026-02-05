"""
Redis Manager - Transparent Caching Layer
Provides caching without modifying existing functionality
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

import json
import pickle
from typing import Any, Optional, Union
from redis import asyncio as aioredis
from redis.exceptions import RedisError

from .. import LOGGER
from .config_manager import Config


class RedisManager:
    """
    Manages Redis connections and caching operations
    Transparent to existing code - can be disabled via config
    """
    
    _instance = None
    _client: Optional[aioredis.Redis] = None
    _enabled: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self, host: str = "redis", port: int = 6379, db: int = 0):
        """
        Initialize Redis connection
        
        Args:
            host: Redis host (default: redis - docker service name)
            port: Redis port (default: 6379)
            db: Redis database number (default: 0)
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
        if self._client:
            try:
                await self._client.close()
                LOGGER.info("Redis connection closed")
            except Exception as e:
                LOGGER.error(f"Error closing Redis: {e}")
    
    @property
    def is_enabled(self) -> bool:
        """Check if Redis is enabled and connected"""
        return self._enabled and self._client is not None
    
    # ==================== CACHING OPERATIONS ====================
    
    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get value from cache
        Returns default if Redis is disabled or key not found
        """
        if not self.is_enabled:
            return default
        
        try:
            value = await self._client.get(key)
            if value is None:
                return default
            
            # Try to unpickle, fallback to decode
            try:
                return pickle.loads(value)
            except:
                return value.decode('utf-8')
                
        except RedisError as e:
            LOGGER.debug(f"Redis GET error for {key}: {e}")
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
            LOGGER.debug(f"Redis SET error for {key}: {e}")
            return False
    
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from cache"""
        if not self.is_enabled:
            return 0
        
        try:
            return await self._client.delete(*keys)
        except RedisError as e:
            LOGGER.debug(f"Redis DELETE error: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_enabled:
            return False
        
        try:
            return await self._client.exists(key) > 0
        except RedisError:
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiry time for a key"""
        if not self.is_enabled:
            return False
        
        try:
            return await self._client.expire(key, ttl)
        except RedisError:
            return False
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter"""
        if not self.is_enabled:
            return None
        
        try:
            return await self._client.incrby(key, amount)
        except RedisError as e:
            LOGGER.debug(f"Redis INCR error: {e}")
            return None
    
    async def get_many(self, *keys: str) -> dict:
        """Get multiple values at once"""
        if not self.is_enabled:
            return {}
        
        try:
            values = await self._client.mget(*keys)
            result = {}
            for key, value in zip(keys, values):
                if value:
                    try:
                        result[key] = pickle.loads(value)
                    except:
                        result[key] = value.decode('utf-8')
            return result
        except RedisError:
            return {}
    
    async def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs at once"""
        if not self.is_enabled:
            return False
        
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
        
        try:
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            if keys:
                return await self._client.delete(*keys)
            return 0
        except RedisError:
            return 0
    
    # ==================== TASK STATUS CACHING ====================
    
    async def cache_task_status(self, task_id: str, status: dict, ttl: int = 300):
        """Cache task status for fast retrieval"""
        key = f"task:status:{task_id}"
        return await self.set(key, status, ttl)
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get cached task status"""
        key = f"task:status:{task_id}"
        return await self.get(key)
    
    async def invalidate_task_cache(self, task_id: str):
        """Remove task from cache when status changes"""
        key = f"task:status:{task_id}"
        await self.delete(key)
    
    # ==================== RATE LIMITING ====================
    
    async def check_rate_limit(
        self, 
        user_id: int, 
        action: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: User ID
            action: Action name (e.g., 'download', 'upload')
            limit: Maximum actions per window
            window: Time window in seconds
        
        Returns:
            (allowed: bool, remaining: int)
        """
        if not self.is_enabled:
            return True, limit  # No rate limiting if Redis disabled
        
        try:
            key = f"ratelimit:{user_id}:{action}"
            current = await self._client.get(key)
            
            if current is None:
                await self._client.setex(key, window, 1)
                return True, limit - 1
            
            count = int(current)
            if count >= limit:
                return False, 0
            
            await self._client.incr(key)
            return True, limit - count - 1
            
        except RedisError:
            return True, limit  # Allow on error (fail open)
    
    # ==================== SESSION MANAGEMENT ====================
    
    async def create_session(self, session_id: str, data: dict, ttl: int = 3600):
        """Create a user session"""
        key = f"session:{session_id}"
        return await self.set(key, data, ttl)
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        key = f"session:{session_id}"
        return await self.get(key)
    
    async def delete_session(self, session_id: str):
        """Delete a session"""
        key = f"session:{session_id}"
        await self.delete(key)
    
    # ==================== STATISTICS ====================
    
    async def get_stats(self) -> dict:
        """Get Redis statistics"""
        if not self.is_enabled:
            return {"enabled": False}
        
        try:
            info = await self._client.info()
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            }
        except RedisError:
            return {"enabled": True, "error": "Failed to get stats"}


# Global instance
redis_client = RedisManager()
