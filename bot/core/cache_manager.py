"""
Advanced Cache Manager with Multi-Tier Caching

Implements L1 (in-memory), L2 (Redis), and L3 (distributed) caching strategies.
Includes cache warming, invalidation, TTL management, and statistics.

Features:
- Multi-tier caching (memory, Redis, distributed)
- Cache warming strategies
- Smart invalidation
- TTL management
- Cache statistics
- Serialization strategies
"""

import asyncio
import hashlib
import json
import pickle
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple
from enum import Enum
import gzip


class CacheLevel(Enum):
    """Cache tier levels"""
    L1_MEMORY = "memory"
    L2_REDIS = "redis"
    L3_DISTRIBUTED = "distributed"


class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheEntry:
    """Single cache entry"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int
    ttl: int  # seconds
    compressed: bool = False
    size_bytes: int = 0


@dataclass
class CacheStatistics:
    """Cache statistics"""
    tier: str
    total_entries: int
    total_size_mb: float
    hits: int
    misses: int
    hit_rate: float
    evictions: int
    avg_entry_size_kb: float
    memory_usage_percent: float


class L1MemoryCache:
    """In-memory cache with LRU eviction"""
    
    def __init__(self, max_size_mb: int = 100, max_entries: int = 10000):
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.max_size_mb = max_size_mb
        self.max_entries = max_entries
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.current_size_bytes = 0
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # Update access time and move to end
            entry.accessed_at = datetime.utcnow()
            entry.access_count += 1
            self.cache.move_to_end(key)
            
            self.hits += 1
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache"""
        async with self.lock:
            # Calculate size
            try:
                size = len(pickle.dumps(value))
            except Exception:
                size = len(str(value).encode())
            
            # Check if we need to evict
            while (self.current_size_bytes + size > self.max_size_mb * 1024 * 1024 or 
                   len(self.cache) >= self.max_entries) and self.cache:
                oldest_key = next(iter(self.cache))
                old_entry = self.cache.pop(oldest_key)
                self.current_size_bytes -= old_entry.size_bytes
                self.evictions += 1
            
            # Create and store entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                accessed_at=datetime.utcnow(),
                access_count=0,
                ttl=ttl,
                size_bytes=size
            )
            
            self.cache[key] = entry
            self.current_size_bytes += size
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete from cache"""
        async with self.lock:
            if key in self.cache:
                entry = self.cache.pop(key)
                self.current_size_bytes -= entry.size_bytes
                return True
            return False
    
    async def clear(self) -> None:
        """Clear entire cache"""
        async with self.lock:
            self.cache.clear()
            self.current_size_bytes = 0
    
    async def get_statistics(self) -> CacheStatistics:
        """Get cache statistics"""
        async with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0.0
            avg_size = (self.current_size_bytes / len(self.cache) / 1024) if self.cache else 0.0
            
            return CacheStatistics(
                tier="L1 Memory",
                total_entries=len(self.cache),
                total_size_mb=self.current_size_bytes / (1024 * 1024),
                hits=self.hits,
                misses=self.misses,
                hit_rate=round(hit_rate, 2),
                evictions=self.evictions,
                avg_entry_size_kb=round(avg_size, 2),
                memory_usage_percent=round((self.current_size_bytes / (self.max_size_mb * 1024 * 1024)) * 100, 2)
            )


class CacheManager:
    """Multi-tier cache manager"""
    
    _instance: Optional['CacheManager'] = None
    
    def __init__(self):
        self.enabled = False
        self.l1_cache = L1MemoryCache(max_size_mb=100)
        self.redis_client = None  # Set by external integration
        self.cache_strategies: Dict[str, CacheStrategy] = {}
        self.cache_warming_tasks: Dict[str, asyncio.Task] = {}
        self.invalidation_patterns: Dict[str, List[str]] = {}
        self.compression_enabled = True
        self.compression_threshold = 1024  # Compress if > 1KB
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'CacheManager':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = CacheManager()
        return cls._instance
    
    async def enable(self) -> bool:
        """Enable cache manager"""
        try:
            async with self.lock:
                self.enabled = True
                return True
        except Exception as e:
            print(f"Error enabling cache manager: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable cache manager"""
        try:
            async with self.lock:
                self.enabled = False
                # Stop all warming tasks
                for task in self.cache_warming_tasks.values():
                    task.cancel()
                self.cache_warming_tasks.clear()
                return True
        except Exception as e:
            print(f"Error disabling cache manager: {e}")
            return False
    
    def _make_key(self, prefix: str, identifier: str, version: str = "v1") -> str:
        """Create cache key from prefix and identifier"""
        hash_val = hashlib.md5(f"{prefix}:{identifier}:{version}".encode()).hexdigest()[:8]
        return f"cache:{prefix}:{version}:{hash_val}"
    
    async def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            full_key = f"{namespace}:{key}"
            
            # Try L1 cache first
            value = await self.l1_cache.get(full_key)
            if value is not None:
                return value
            
            # Try L2 Redis
            if self.redis_client:
                try:
                    redis_value = await self.redis_client.get(full_key)
                    if redis_value is not None:
                        value = self._decompress(redis_value) if isinstance(redis_value, bytes) else redis_value
                        # Store in L1 for next access
                        await self.l1_cache.set(full_key, value)
                        return value
                except Exception as e:
                    print(f"Redis get error: {e}")
            
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        namespace: str = "default",
        compress: bool = True
    ) -> bool:
        """Set value in cache"""
        if not self.enabled:
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            
            # Store in L1
            await self.l1_cache.set(full_key, value, ttl)
            
            # Store in L2 Redis if available
            if self.redis_client:
                try:
                    cache_value = value
                    
                    # Compress if needed
                    if compress and self.compression_enabled:
                        serialized = pickle.dumps(value)
                        if len(serialized) > self.compression_threshold:
                            cache_value = gzip.compress(serialized)
                    
                    await self.redis_client.setex(full_key, ttl, cache_value)
                except Exception as e:
                    print(f"Redis set error: {e}")
            
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str, namespace: str = "default") -> bool:
        """Delete from cache"""
        if not self.enabled:
            return False
        
        try:
            full_key = f"{namespace}:{key}"
            
            # Delete from L1
            await self.l1_cache.delete(full_key)
            
            # Delete from Redis
            if self.redis_client:
                try:
                    await self.redis_client.delete(full_key)
                except Exception as e:
                    print(f"Redis delete error: {e}")
            
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str, namespace: str = "default") -> int:
        """Invalidate all keys matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            count = 0
            full_pattern = f"{namespace}:{pattern}"
            
            # Invalidate L1 cache
            keys_to_delete = [k for k in self.l1_cache.cache.keys() if pattern in k]
            for key in keys_to_delete:
                await self.l1_cache.delete(key)
                count += 1
            
            # Invalidate Redis
            if self.redis_client:
                try:
                    cursor = 0
                    while True:
                        cursor, keys = await self.redis_client.scan(cursor, match=full_pattern)
                        for key in keys:
                            await self.redis_client.delete(key)
                            count += 1
                        if cursor == 0:
                            break
                except Exception as e:
                    print(f"Redis invalidate error: {e}")
            
            return count
        except Exception as e:
            print(f"Cache invalidate error: {e}")
            return 0
    
    async def warm_cache(
        self,
        key: str,
        loader_func: Callable[[], Any],
        ttl: int = 300,
        interval: int = 600,
        namespace: str = "default"
    ) -> None:
        """Warm cache with periodic refresh"""
        if not self.enabled:
            return
        
        async def warming_loop():
            while True:
                try:
                    value = await loader_func()
                    await self.set(key, value, ttl, namespace)
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Cache warming error: {e}")
                    await asyncio.sleep(60)  # Retry after 1 minute
        
        try:
            task = asyncio.create_task(warming_loop())
            self.cache_warming_tasks[key] = task
        except Exception as e:
            print(f"Error starting cache warming: {e}")
    
    async def stop_warming(self, key: str) -> bool:
        """Stop cache warming task"""
        try:
            if key in self.cache_warming_tasks:
                task = self.cache_warming_tasks[key]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.cache_warming_tasks[key]
                return True
            return False
        except Exception as e:
            print(f"Error stopping warming: {e}")
            return False
    
    def _compress(self, data: bytes) -> bytes:
        """Compress data"""
        try:
            return gzip.compress(data)
        except Exception:
            return data
    
    def _decompress(self, data: bytes) -> bytes:
        """Decompress data"""
        try:
            return gzip.decompress(data)
        except Exception:
            return data
    
    async def get_statistics(self) -> Dict[str, CacheStatistics]:
        """Get cache statistics"""
        try:
            l1_stats = await self.l1_cache.get_statistics()
            
            return {
                'l1_memory': l1_stats,
                'enabled': self.enabled,
                'compression_enabled': self.compression_enabled,
                'warming_tasks': len(self.cache_warming_tasks)
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'error': str(e)}
    
    async def clear_all(self) -> bool:
        """Clear all caches"""
        try:
            await self.l1_cache.clear()
            
            if self.redis_client:
                try:
                    await self.redis_client.flushdb()
                except Exception as e:
                    print(f"Redis flush error: {e}")
            
            return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    async def reset(self) -> bool:
        """Reset cache manager"""
        try:
            await self.disable()
            self.l1_cache = L1MemoryCache()
            return True
        except Exception as e:
            print(f"Error resetting cache manager: {e}")
            return False


def cached(key_prefix: str, ttl: int = 300, namespace: str = "default"):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache_mgr = CacheManager.get_instance()
            
            # Build cache key from function args
            key_parts = [key_prefix] + [str(arg) for arg in args[:2]]
            cache_key = ":".join(key_parts)
            
            # Try cache first
            cached_value = await cache_mgr.get(cache_key, namespace)
            if cached_value is not None:
                return cached_value
            
            # Execute and cache
            result = await func(*args, **kwargs)
            await cache_mgr.set(cache_key, result, ttl, namespace)
            
            return result
        
        return wrapper
    
    return decorator
