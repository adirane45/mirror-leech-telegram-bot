"""
Advanced Caching Strategies for Phase 7

Implements:
- Multi-level caching (memory, Redis, disk)
- Cache invalidation strategies
- Bloom filters for membership testing
- Distributed cache coherence
- Cache warming & prefetching
"""

import asyncio
import hashlib
import json
from typing import Dict, Any, Optional, Callable, TypeVar, Set
from enum import Enum
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import pickle

from .. import LOGGER


T = TypeVar('T')


class CacheLevel(str, Enum):
    """Cache levels"""
    L1 = "l1"  # Memory
    L2 = "l2"  # Redis
    L3 = "l3"  # Disk


class InvalidationStrategy(str, Enum):
    """Cache invalidation strategies"""
    TTL = "ttl"
    LRU = "lru"
    LFU = "lfu"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"


@dataclass
class CacheEntry:
    """Cache entry"""
    key: str
    value: Any
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    ttl_seconds: Optional[int] = None
    access_count: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if not self.ttl_seconds:
            return False
        
        elapsed = (
            datetime.now(timezone.utc) - self.created_at
        ).total_seconds()
        
        return elapsed > self.ttl_seconds
    
    def touch(self) -> None:
        """Update access time"""
        self.last_accessed = datetime.now(timezone.utc)
        self.access_count += 1


class L1MemoryCache:
    """Level 1 Memory Cache"""
    
    def __init__(
        self,
        max_size: int = 10000,
        strategy: InvalidationStrategy = InvalidationStrategy.LRU
    ):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.strategy = strategy
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        entry = self.cache.get(key)
        
        if entry is None:
            return None
        
        if entry.is_expired():
            del self.cache[key]
            return None
        
        entry.touch()
        return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache"""
        # Evict if necessary
        if len(self.cache) >= self.max_size:
            self._evict()
        
        self.cache[key] = CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl_seconds
        )
    
    def _evict(self) -> None:
        """Evict entry based on strategy"""
        if not self.cache:
            return
        
        if self.strategy == InvalidationStrategy.LRU:
            # Remove least recently used
            victim = min(
                self.cache.items(),
                key=lambda x: x[1].last_accessed
            )
        
        elif self.strategy == InvalidationStrategy.LFU:
            # Remove least frequently used
            victim = min(
                self.cache.items(),
                key=lambda x: x[1].access_count
            )
        
        else:
            # TTL-based, remove oldest
            victim = min(
                self.cache.items(),
                key=lambda x: x[1].created_at
            )
        
        del self.cache[victim[0]]
    
    def invalidate(self, key: str) -> None:
        """Invalidate cache entry"""
        self.cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache"""
        self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache stats"""
        total_accesses = sum(e.access_count for e in self.cache.values())
        
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "utilization": len(self.cache) / self.max_size,
            "total_accesses": total_accesses,
        }


class BloomFilter:
    """Bloom filter for membership testing"""
    
    def __init__(self, size: int = 10000, hash_functions: int = 3):
        self.size = size
        self.hash_functions = hash_functions
        self.bits = [False] * size
    
    def _hash(self, item: str, seed: int) -> int:
        """Hash item"""
        hasher = hashlib.md5(f"{item}_{seed}".encode())
        return int(hasher.hexdigest(), 16) % self.size
    
    def add(self, item: str) -> None:
        """Add item to filter"""
        for i in range(self.hash_functions):
            idx = self._hash(item, i)
            self.bits[idx] = True
    
    def might_contain(self, item: str) -> bool:
        """Check if item might be in set"""
        for i in range(self.hash_functions):
            idx = self._hash(item, i)
            if not self.bits[idx]:
                return False
        
        return True
    
    def false_positive_rate(self) -> float:
        """Estimate false positive rate"""
        set_bits = sum(self.bits)
        filled_ratio = set_bits / self.size
        return filled_ratio ** self.hash_functions


class DistributedCacheCoherence:
    """Manage cache coherence across instances"""
    
    def __init__(self):
        self.local_caches: Dict[str, L1MemoryCache] = {}
        self.invalidation_log: list = []
    
    def register_cache(self, instance_id: str, cache: L1MemoryCache) -> None:
        """Register local cache"""
        self.local_caches[instance_id] = cache
    
    async def broadcast_invalidation(self, key: str) -> None:
        """Broadcast invalidation to all caches"""
        for instance_cache in self.local_caches.values():
            instance_cache.invalidate(key)
        
        self.invalidation_log.append({
            "key": key,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def sync_caches(self) -> None:
        """Synchronize caches across instances"""
        LOGGER.info("Syncing distributed caches")
        
        # Implementation specific - could use Redis pubsub
        pass


class CacheWarmer:
    """Preload cache with frequently used data"""
    
    def __init__(self, cache: L1MemoryCache):
        self.cache = cache
        self.warming_functions: Dict[str, Callable] = {}
    
    def register_warmer(
        self,
        name: str,
        func: Callable
    ) -> None:
        """Register warming function"""
        self.warming_functions[name] = func
    
    async def warm_cache(self) -> Dict[str, int]:
        """Warm cache with data"""
        results = {}
        
        for name, func in self.warming_functions.items():
            try:
                if asyncio.iscoroutinefunction(func):
                    items = await func()
                else:
                    items = func()
                
                count = 0
                for key, value, ttl in items:
                    self.cache.set(key, value, ttl)
                    count += 1
                
                results[name] = count
                LOGGER.info(f"Cache warmer '{name}' added {count} items")
            
            except Exception as e:
                results[name] = 0
                LOGGER.error(f"Cache warmer error '{name}': {e}")
        
        return results


@dataclass
class CachePolicy:
    """Cache policy"""
    ttl_seconds: int = 3600
    max_size: int = 10000
    invalidation_strategy: InvalidationStrategy = InvalidationStrategy.LRU
    write_through: bool = False


class MultiLevelCache:
    """Multi-level cache stack"""
    
    def __init__(self, policy: CachePolicy = None):
        self.policy = policy or CachePolicy()
        self.l1 = L1MemoryCache(
            max_size=self.policy.max_size,
            strategy=self.policy.invalidation_strategy
        )
        self.l2_callback: Optional[Callable] = None
        self.l3_callback: Optional[Callable] = None
    
    def set_l2_callback(self, callback: Callable) -> None:
        """Set L2 (Redis) callback"""
        self.l2_callback = callback
    
    def set_l3_callback(self, callback: Callable) -> None:
        """Set L3 (Disk) callback"""
        self.l3_callback = callback
    
    async def get(self, key: str) -> Optional[Any]:
        """Get from cache stack"""
        # Try L1
        value = self.l1.get(key)
        if value is not None:
            return value
        
        # Try L2
        if self.l2_callback:
            if asyncio.iscoroutinefunction(self.l2_callback):
                value = await self.l2_callback("get", key)
            else:
                value = self.l2_callback("get", key)
            
            if value:
                self.l1.set(key, value, self.policy.ttl_seconds)
                return value
        
        # Try L3
        if self.l3_callback:
            if asyncio.iscoroutinefunction(self.l3_callback):
                value = await self.l3_callback("get", key)
            else:
                value = self.l3_callback("get", key)
            
            if value:
                self.l1.set(key, value, self.policy.ttl_seconds)
                return value
        
        return None
    
    async def set(self, key: str, value: Any) -> None:
        """Set in cache stack"""
        self.l1.set(key, value, self.policy.ttl_seconds)
        
        if self.policy.write_through:
            # Write to L2
            if self.l2_callback:
                if asyncio.iscoroutinefunction(self.l2_callback):
                    await self.l2_callback("set", key, value)
                else:
                    self.l2_callback("set", key, value)
            
            # Write to L3
            if self.l3_callback:
                if asyncio.iscoroutinefunction(self.l3_callback):
                    await self.l3_callback("set", key, value)
                else:
                    self.l3_callback("set", key, value)
    
    async def invalidate(self, key: str) -> None:
        """Invalidate across all levels"""
        self.l1.invalidate(key)
        
        if self.l2_callback:
            if asyncio.iscoroutinefunction(self.l2_callback):
                await self.l2_callback("delete", key)
            else:
                self.l2_callback("delete", key)
        
        if self.l3_callback:
            if asyncio.iscoroutinefunction(self.l3_callback):
                await self.l3_callback("delete", key)
            else:
                self.l3_callback("delete", key)


# Global instance
cache = MultiLevelCache()
