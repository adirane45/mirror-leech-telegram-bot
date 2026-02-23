"""
Advanced Multi-Tier Caching System
L1: In-memory cache (fast, limited capacity)
L2: Redis cache (persistent, larger capacity)

Phase 4: Performance Optimization
Created by: justadi
Date: February 8, 2026
"""

import time
import logging
import hashlib
import pickle
from typing import Any, Optional, Callable, Dict, List, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
from datetime import datetime, timedelta
import asyncio
import functools

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.ttl_seconds is None:
            return False
        return (time.time() - self.created_at) > self.ttl_seconds
    
    def age_seconds(self) -> float:
        """Get entry age in seconds"""
        return time.time() - self.created_at


class LRUCache:
    """
    LRU (Least Recently Used) in-memory cache
    
    Features:
    - Size-limited (max entries or max memory)
    - LRU eviction policy
    - TTL support
    - Hit/miss statistics
    """
    
    def __init__(self, max_size: int = 1000, max_memory_mb: float = 100):
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_size_bytes = 0
        
        logger.info(f"LRUCache initialized (max_size={max_size}, max_memory={max_memory_mb}MB)")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.is_expired():
            self.delete(key)
            self.misses += 1
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        entry.accessed_at = time.time()
        entry.access_count += 1
        
        self.hits += 1
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in cache"""
        # Calculate size
        try:
            size_bytes = len(pickle.dumps(value))
        except Exception:
            size_bytes = 0
        
        # Check if entry exists
        if key in self.cache:
            old_entry = self.cache[key]
            self.total_size_bytes -= old_entry.size_bytes
            del self.cache[key]
        
        # Create new entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            accessed_at=time.time(),
            ttl_seconds=ttl_seconds,
            size_bytes=size_bytes
        )
        
        self.cache[key] = entry
        self.total_size_bytes += size_bytes
        
        # Evict if necessary
        self._evict_if_needed()
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            entry = self.cache[key]
            self.total_size_bytes -= entry.size_bytes
            del self.cache[key]
            return True
        return False
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.total_size_bytes = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def _evict_if_needed(self):
        """Evict least recently used entries if limits exceeded"""
        # Evict by size
        while len(self.cache) > self.max_size:
            key, entry = self.cache.popitem(last=False)
            self.total_size_bytes -= entry.size_bytes
            self.evictions += 1
        
        # Evict by memory
        while self.total_size_bytes > self.max_memory_bytes and len(self.cache) > 0:
            key, entry = self.cache.popitem(last=False)
            self.total_size_bytes -= entry.size_bytes
            self.evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "memory_mb": round(self.total_size_bytes / 1024 / 1024, 2),
            "max_memory_mb": round(self.max_memory_bytes / 1024 / 1024, 2),
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }


class MultiTierCache:
    """
    Multi-tier caching system with L1 (memory) and L2 (Redis)
    
    Features:
    - L1: Fast in-memory cache
    - L2: Redis persistent cache
    - Automatic promotion from L2 to L1
    - Cache warming
    - Intelligent invalidation
    """
    
    def __init__(
        self,
        l1_max_size: int = 1000,
        l1_max_memory_mb: float = 100,
        l2_enabled: bool = True,
        default_ttl: int = 3600
    ):
        self.l1_cache = LRUCache(max_size=l1_max_size, max_memory_mb=l1_max_memory_mb)
        self.l2_enabled = l2_enabled
        self.default_ttl = default_ttl
        
        # Try to initialize Redis L2 cache
        self.l2_cache = None
        if l2_enabled:
            try:
                from .redis_manager import redis_client
                self.l2_cache = redis_client
                logger.info("L2 cache (Redis) enabled")
            except Exception as e:
                logger.warning(f"L2 cache (Redis) not available: {e}")
                self.l2_enabled = False
        
        logger.info(
            f"MultiTierCache initialized (L1: {l1_max_size} entries/{l1_max_memory_mb}MB, "
            f"L2: {'enabled' if self.l2_enabled else 'disabled'}, default_ttl={default_ttl}s)"
        )
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 then L2)"""
        # Try L1 first
        value = self.l1_cache.get(key)
        if value is not None:
            return value
        
        # Try L2 if enabled
        if self.l2_enabled and self.l2_cache:
            try:
                value = await self.l2_cache.get(key)
                if value is not None:
                    # Promote to L1
                    self.l1_cache.set(key, value, ttl_seconds=self.default_ttl)
                    return value
            except Exception as e:
                logger.error(f"L2 cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in both L1 and L2"""
        ttl = ttl or self.default_ttl
        
        # Set in L1
        self.l1_cache.set(key, value, ttl_seconds=ttl)
        
        # Set in L2 if enabled
        if self.l2_enabled and self.l2_cache:
            try:
                await self.l2_cache.set(key, value, ttl=ttl)
            except Exception as e:
                logger.error(f"L2 cache set error: {e}")
    
    async def delete(self, key: str):
        """Delete key from both L1 and L2"""
        # Delete from L1
        self.l1_cache.delete(key)
        
        # Delete from L2 if enabled
        if self.l2_enabled and self.l2_cache:
            try:
                await self.l2_cache.delete(key)
            except Exception as e:
                logger.error(f"L2 cache delete error: {e}")
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        # L1 doesn't support pattern matching, clear specific keys manually
        keys_to_delete = [k for k in self.l1_cache.cache.keys() if pattern in k]
        for key in keys_to_delete:
            self.l1_cache.delete(key)
        
        # L2 pattern invalidation
        if self.l2_enabled and self.l2_cache:
            try:
                await self.l2_cache.delete_pattern(pattern)
            except Exception as e:
                logger.error(f"L2 cache pattern delete error: {e}")
    
    def clear(self):
        """Clear all caches"""
        self.l1_cache.clear()
        if self.l2_enabled and self.l2_cache:
            try:
                # Note: This is sync, might need async version
                logger.warning("L2 cache clear not implemented (would clear entire Redis)")
            except Exception as e:
                logger.error(f"L2 cache clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from both cache tiers"""
        stats = {
            "l1": self.l1_cache.get_stats(),
            "l2": {"enabled": self.l2_enabled}
        }
        
        if self.l2_enabled and self.l2_cache:
            try:
                # Get L2 stats if available
                stats["l2"]["info"] = "Redis cache active"
            except Exception:
                pass
        
        return stats


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_string = ":".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results
    
    Usage:
        @cached(ttl=3600, key_prefix="user")
        async def get_user(user_id: int):
            return await db.get_user(user_id)
    """
    def decorator(func: Callable) -> Callable:
        cache = get_cache()
        func_name = f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = cache_key(*args, **kwargs)
                
                cache_key_full = f"{key_prefix}:{func_name}:{key}" if key_prefix else f"{func_name}:{key}"
                
                # Try to get from cache
                cached_value = await cache.get(cache_key_full)
                if cached_value is not None:
                    return cached_value
                
                # Call function and cache result
                result = await func(*args, **kwargs)
                await cache.set(cache_key_full, result, ttl=ttl)
                
                return result
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, use sync cache operations
                if key_func:
                    key = key_func(*args, **kwargs)
                else:
                    key = cache_key(*args, **kwargs)
                
                cache_key_full = f"{key_prefix}:{func_name}:{key}" if key_prefix else f"{func_name}:{key}"
                
                # Try L1 cache only for sync functions
                cached_value = cache.l1_cache.get(cache_key_full)
                if cached_value is not None:
                    return cached_value
                
                # Call function and cache in L1
                result = func(*args, **kwargs)
                cache.l1_cache.set(cache_key_full, result, ttl_seconds=ttl)
                
                return result
            
            return sync_wrapper
    
    return decorator


# Singleton instance
_cache_instance: Optional[MultiTierCache] = None


def get_cache(
    l1_max_size: int = 1000,
    l1_max_memory_mb: float = 100,
    l2_enabled: bool = True,
    default_ttl: int = 3600
) -> MultiTierCache:
    """Get singleton cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MultiTierCache(
            l1_max_size=l1_max_size,
            l1_max_memory_mb=l1_max_memory_mb,
            l2_enabled=l2_enabled,
            default_ttl=default_ttl
        )
    return _cache_instance
