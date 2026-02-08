"""
Cache Manager Models
Data structures for cache entries and statistics
"""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timedelta


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
