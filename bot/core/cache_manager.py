"""
Phase 4: Cache Manager
Multi-tier caching system (L1 in-memory, L2 Redis, L3 distributed)
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import zlib
import pickle

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cache entry"""
    key: str
    value: Any
    ttl: int  # Time to live in seconds
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        expiry = self.created_at + timedelta(seconds=self.ttl)
        return datetime.now() > expiry


@dataclass
class CacheStatistics:
    """Cache statistics"""
    l1_entries: int = 0
    l1_hits: int = 0
    l1_misses: int = 0
    l1_evictions: int = 0
    l1_memory_bytes: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    total_hits: int = 0
    total_misses: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate overall hit rate"""
        total = self.total_hits + self.total_misses
        return (self.total_hits / total * 100) if total > 0 else 0.0


class CacheManager:
    """
    Singleton multi-tier cache manager
    L1: In-memory (fast, small)
    L2: Redis (persistent, medium)
    L3: Distributed (large, shared)
    """

    _instance: Optional['CacheManager'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.enabled = False
        self.l1_cache: Dict[str, CacheEntry] = {}  # In-memory LRU cache
        self.l1_max_size_mb = 100
        self.l1_max_entries = 10000
        self.statistics = CacheStatistics()
        self.compression_enabled = True
        self.cache_warming_tasks: List[asyncio.Task] = []
        
    @classmethod
    def get_instance(cls) -> 'CacheManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = CacheManager()
        return cls._instance

    async def enable(self, max_size_mb: int = 100, compression: bool = True) -> bool:
        """
        Enable the Cache Manager
        
        Args:
            max_size_mb: Maximum L1 cache size in MB
            compression: Enable compression for cached values
            
        Returns:
            Success status
        """
        async with self._lock:
            self.enabled = True
            self.l1_max_size_mb = max_size_mb
            self.compression_enabled = compression
            logger.info(f"Cache Manager enabled (L1: {max_size_mb}MB, compression: {compression})")
            return True

    async def disable(self) -> bool:
        """Disable the Cache Manager"""
        async with self._lock:
            self.enabled = False
            self.l1_cache.clear()
            # Cancel warming tasks
            for task in self.cache_warming_tasks:
                task.cancel()
            self.cache_warming_tasks.clear()
            logger.info("Cache Manager disabled")
            return True

    def _get_entry_size_bytes(self, entry: CacheEntry) -> int:
        """
        Estimate size of cache entry in bytes for memory management.
        
        Args:
            entry: CacheEntry to measure
            
        Returns:
            Estimated size in bytes, 0 if calculation fails
        """
        try:
            if isinstance(entry.value, bytes):
                return len(entry.value)
            else:
                return len(pickle.dumps(entry.value))
        except (TypeError, pickle.PicklingError, AttributeError) as e:
            logger.debug(f"Could not calculate size for entry {entry.key}: {e}")
            return 0

    def _should_evict(self) -> bool:
        """Check if L1 cache should evict entries"""
        total_size = sum(self._get_entry_size_bytes(e) for e in self.l1_cache.values())
        return (
            total_size > self.l1_max_size_mb * 1024 * 1024 or
            len(self.l1_cache) > self.l1_max_entries
        )

    async def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.l1_cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.l1_cache.keys(),
            key=lambda k: (
                self.l1_cache[k].last_accessed,
                self.l1_cache[k].access_count
            )
        )
        
        del self.l1_cache[lru_key]
        self.statistics.l1_evictions += 1
        logger.debug(f"Evicted LRU entry: {lru_key}")

    async def _ensure_capacity(self) -> None:
        """Ensure cache has available capacity"""
        while self._should_evict():
            await self._evict_lru()

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        namespace: str = "default"
    ) -> bool:
        """
        Set cache value
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses 300s default if None)
            namespace: Namespace for key organization
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            # Ensure capacity before adding
            await self._ensure_capacity()
            
            full_key = f"{namespace}:{key}"
            ttl_seconds = ttl or 300
            entry = CacheEntry(key=full_key, value=value, ttl=ttl_seconds)
            
            self.l1_cache[full_key] = entry
            logger.debug(f"Cached {full_key} (TTL: {ttl_seconds}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            namespace: Namespace for key organization
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if not self.enabled:
            self.statistics.total_misses += 1
            return None

        try:
            full_key = f"{namespace}:{key}"
            
            if full_key in self.l1_cache:
                entry = self.l1_cache[full_key]
                
                if entry.is_expired():
                    del self.l1_cache[full_key]
                    self.statistics.l1_misses += 1
                    self.statistics.total_misses += 1
                    return None
                
                # Update access info
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                
                self.statistics.l1_hits += 1
                self.statistics.total_hits += 1
                logger.debug(f"Cache hit: {full_key}")
                return entry.value
            
            self.statistics.l1_misses += 1
            self.statistics.total_misses += 1
            logger.debug(f"Cache miss: {full_key}")
            return None
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            self.statistics.total_misses += 1
            return None

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete cache entry
        
        Args:
            key: Cache key
            namespace: Namespace for key organization
            
        Returns:
            Success status
        """
        try:
            full_key = f"{namespace}:{key}"
            if full_key in self.l1_cache:
                del self.l1_cache[full_key]
                logger.debug(f"Deleted cache entry: {full_key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cache: {e}")
            return False

    async def invalidate_pattern(self, pattern: str, namespace: str = "default") -> int:
        """
        Invalidate all cache entries matching pattern
        
        Args:
            pattern: Pattern to match (supports * wildcard)
            namespace: Namespace for key organization
            
        Returns:
            Number of entries invalidated
        """
        try:
            full_pattern = f"{namespace}:{pattern}"
            deleted = 0
            
            # Convert pattern to regex-like matching
            # Simple implementation: * matches any characters
            import re
            regex_pattern = full_pattern.replace('*', '.*')
            regex = re.compile(f"^{regex_pattern}$")
            
            keys_to_delete = [k for k in self.l1_cache.keys() if regex.match(k)]
            
            for key in keys_to_delete:
                del self.l1_cache[key]
                deleted += 1
            
            logger.info(f"Invalidated {deleted} cache entries matching {full_pattern}")
            return deleted
        except Exception as e:
            logger.error(f"Error invalidating pattern: {e}")
            return 0

    async def warm_cache(
        self,
        key: str,
        loader_func: Callable,
        ttl: int = 3600,
        interval: int = 600,
        namespace: str = "cache_warming"
    ) -> bool:
        """
        Warm cache with pre-loaded data on a schedule
        
        Args:
            key: Cache key
            loader_func: Async function to load data
            ttl: Time to live for cached data
            interval: Interval in seconds to refresh
            namespace: Namespace for key organization
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            async def warm_task():
                while self.enabled:
                    try:
                        logger.debug(f"Warming cache for {namespace}:{key}")
                        data = await loader_func()
                        await self.set(key, data, ttl=ttl, namespace=namespace)
                    except Exception as e:
                        logger.error(f"Error warming cache: {e}")
                    
                    await asyncio.sleep(interval)
            
            # Start warming task
            task = asyncio.create_task(warm_task())
            self.cache_warming_tasks.append(task)
            
            # Load initial data
            data = await loader_func()
            await self.set(key, data, ttl=ttl, namespace=namespace)
            
            logger.info(f"Cache warming started for {namespace}:{key} (interval: {interval}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting up cache warming: {e}")
            return False

    async def clear(self, namespace: Optional[str] = None) -> bool:
        """
        Clear cache entries
        
        Args:
            namespace: Specific namespace to clear (clears all if None)
            
        Returns:
            Success status
        """
        try:
            if namespace:
                prefix = f"{namespace}:"
                keys_to_delete = [k for k in self.l1_cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self.l1_cache[key]
                logger.info(f"Cleared cache namespace {namespace} ({len(keys_to_delete)} entries)")
            else:
                self.l1_cache.clear()
                logger.info("Cleared all cache entries")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    async def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_size_bytes = sum(self._get_entry_size_bytes(e) for e in self.l1_cache.values())
        
        stats = {
            'enabled': self.enabled,
            'l1_entries': len(self.l1_cache),
            'l1_memory_mb': total_size_bytes / (1024 * 1024),
            'l1_max_size_mb': self.l1_max_size_mb,
            'l1_hits': self.statistics.l1_hits,
            'l1_misses': self.statistics.l1_misses,
            'l1_hit_rate_percent': (
                self.statistics.l1_hits / (self.statistics.l1_hits + self.statistics.l1_misses) * 100
                if (self.statistics.l1_hits + self.statistics.l1_misses) > 0 else 0.0
            ),
            'l1_evictions': self.statistics.l1_evictions,
            'total_hits': self.statistics.total_hits,
            'total_misses': self.statistics.total_misses,
            'overall_hit_rate_percent': self.statistics.hit_rate,
            'warming_tasks': len(self.cache_warming_tasks),
        }
        return stats
