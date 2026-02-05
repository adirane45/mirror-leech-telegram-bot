"""
Query Optimizer for GraphQL and Database Queries

Analyzes, optimizes, and caches query execution plans to improve performance.
Detects N+1 query problems, suggests indexes, and applies auto-optimization.

Features:
- Query analysis and optimization
- N+1 query detection
- Index suggestion
- Query rewriting
- Execution plan caching
- Performance statistics
"""

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps


@dataclass
class QueryStatistics:
    """Query execution statistics"""
    query_hash: str
    query_string: str
    execution_time: float
    executed_at: datetime
    result_count: int
    cache_hit: bool = False
    optimization_level: int = 0
    suggested_index: Optional[str] = None


@dataclass
class OptimizationResult:
    """Result of query optimization"""
    original_query: str
    optimized_query: str
    estimated_improvement: float  # percentage
    recommendations: List[str]
    suggested_indexes: List[str]
    n_plus_one_detected: bool


class QueryOptimizer:
    """Thread-safe query optimizer with analysis and caching"""
    
    _instance: Optional['QueryOptimizer'] = None
    
    def __init__(self):
        self.enabled = False
        self.query_cache: Dict[str, Any] = {}
        self.query_stats: List[QueryStatistics] = []
        self.n_plus_one_patterns: Dict[str, int] = defaultdict(int)
        self.execution_times: Dict[str, List[float]] = defaultdict(list)
        self.optimization_suggestions: Dict[str, List[str]] = defaultdict(list)
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_ttl = 300  # 5 minutes default
        self.max_stats_history = 10000
        self.slow_query_threshold = 1.0  # 1 second
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'QueryOptimizer':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = QueryOptimizer()
        return cls._instance
    
    async def enable(self) -> bool:
        """Enable query optimizer"""
        try:
            async with self.lock:
                self.enabled = True
                self.query_cache.clear()
                self.query_stats.clear()
                self.execution_times.clear()
                self.n_plus_one_patterns.clear()
            return True
        except Exception as e:
            print(f"Error enabling query optimizer: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable query optimizer"""
        try:
            async with self.lock:
                self.enabled = False
                self.query_cache.clear()
            return True
        except Exception as e:
            print(f"Error disabling query optimizer: {e}")
            return False
    
    def _hash_query(self, query: str) -> str:
        """Generate hash for query"""
        return hashlib.sha256(query.encode()).hexdigest()[:16]
    
    async def analyze_query(self, query: str) -> OptimizationResult:
        """Analyze and optimize a query"""
        if not self.enabled:
            return OptimizationResult(
                original_query=query,
                optimized_query=query,
                estimated_improvement=0.0,
                recommendations=[],
                suggested_indexes=[],
                n_plus_one_detected=False
            )
        
        try:
            async with self.lock:
                recommendations = []
                suggested_indexes = []
                optimized_query = query
                n_plus_one_detected = False
                improvement = 0.0
                
                # Detect N+1 patterns
                if self._detect_n_plus_one(query):
                    n_plus_one_detected = True
                    recommendations.append("N+1 query detected - consider batch loading")
                    improvement += 20.0
                    suggested_indexes.append("Add batch_id index")
                
                # Suggest indexes
                index_suggestions = self._suggest_indexes(query)
                if index_suggestions:
                    suggested_indexes.extend(index_suggestions)
                    improvement += 10.0 * len(index_suggestions)
                
                # Simple query rewrites
                if "SELECT *" in query.upper():
                    recommendations.append("Avoid SELECT * - specify needed columns")
                    improvement += 15.0
                    optimized_query = self._rewrite_select_star(query)
                
                # Add JOIN optimization
                if "JOIN" in query.upper():
                    recommendations.append("Consider query parallelization for JOINs")
                    improvement += min(5.0 * query.count("JOIN"), 25.0)
                
                # Add ORDER BY optimization
                if "ORDER BY" in query.upper() and "LIMIT" in query.upper():
                    recommendations.append("ORDER BY with LIMIT - ensure index exists")
                
                # Cap improvement estimate
                improvement = min(improvement, 95.0)
                
                return OptimizationResult(
                    original_query=query,
                    optimized_query=optimized_query,
                    estimated_improvement=improvement,
                    recommendations=recommendations,
                    suggested_indexes=suggested_indexes,
                    n_plus_one_detected=n_plus_one_detected
                )
        except Exception as e:
            print(f"Error analyzing query: {e}")
            return OptimizationResult(
                original_query=query,
                optimized_query=query,
                estimated_improvement=0.0,
                recommendations=[],
                suggested_indexes=[],
                n_plus_one_detected=False
            )
    
    def _detect_n_plus_one(self, query: str) -> bool:
        """Detect N+1 query patterns"""
        query_upper = query.upper()
        # Simple heuristic: repeated similar queries in a loop
        query_hash = self._hash_query(query)
        self.n_plus_one_patterns[query_hash] += 1
        return self.n_plus_one_patterns[query_hash] > 5
    
    def _suggest_indexes(self, query: str) -> List[str]:
        """Suggest indexes for query"""
        suggestions = []
        query_upper = query.upper()
        
        # WHERE clause indexes
        if "WHERE" in query_upper:
            suggestions.append("Add index on WHERE clause columns")
        
        # JOIN indexes
        if "JOIN" in query_upper:
            suggestions.append("Add index on JOIN keys")
        
        # GROUP BY indexes
        if "GROUP BY" in query_upper:
            suggestions.append("Add index on GROUP BY columns")
        
        return suggestions
    
    def _rewrite_select_star(self, query: str) -> str:
        """Rewrite SELECT * query"""
        try:
            # Simple replacement - in production, use SQL parser
            if "SELECT *" in query.upper():
                return query.replace("SELECT *", "SELECT id, name, created_at, updated_at")
            return query
        except Exception:
            return query
    
    async def cache_query_result(
        self, 
        query: str, 
        result: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache query result"""
        if not self.enabled:
            return False
        
        try:
            async with self.lock:
                query_hash = self._hash_query(query)
                self.query_cache[query_hash] = {
                    'result': result,
                    'timestamp': time.time(),
                    'ttl': ttl or self.cache_ttl,
                    'query': query
                }
                return True
        except Exception as e:
            print(f"Error caching query: {e}")
            return False
    
    async def get_cached_result(self, query: str) -> Optional[Any]:
        """Get cached query result"""
        if not self.enabled:
            return None
        
        try:
            async with self.lock:
                query_hash = self._hash_query(query)
                
                if query_hash not in self.query_cache:
                    self.cache_misses += 1
                    return None
                
                cached = self.query_cache[query_hash]
                age = time.time() - cached['timestamp']
                
                if age > cached['ttl']:
                    del self.query_cache[query_hash]
                    self.cache_misses += 1
                    return None
                
                self.cache_hits += 1
                return cached['result']
        except Exception as e:
            print(f"Error retrieving cached query: {e}")
            return None
    
    async def record_execution(
        self,
        query: str,
        execution_time: float,
        result_count: int,
        cache_hit: bool = False
    ) -> None:
        """Record query execution statistics"""
        if not self.enabled:
            return
        
        try:
            async with self.lock:
                query_hash = self._hash_query(query)
                
                stats = QueryStatistics(
                    query_hash=query_hash,
                    query_string=query[:200],  # Limit string length
                    execution_time=execution_time,
                    executed_at=datetime.utcnow(),
                    result_count=result_count,
                    cache_hit=cache_hit,
                    optimization_level=2 if execution_time < 0.1 else 1 if execution_time < 1.0 else 0
                )
                
                self.query_stats.append(stats)
                self.execution_times[query_hash].append(execution_time)
                
                # Keep history size manageable
                if len(self.query_stats) > self.max_stats_history:
                    self.query_stats = self.query_stats[-self.max_stats_history:]
        except Exception as e:
            print(f"Error recording execution: {e}")
    
    async def get_slow_queries(self, threshold: Optional[float] = None) -> List[QueryStatistics]:
        """Get slow queries"""
        threshold = threshold or self.slow_query_threshold
        
        try:
            async with self.lock:
                return [
                    stat for stat in self.query_stats 
                    if stat.execution_time > threshold
                ]
        except Exception as e:
            print(f"Error getting slow queries: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get optimizer statistics"""
        try:
            async with self.lock:
                if not self.query_stats:
                    return {
                        'enabled': self.enabled,
                        'total_queries': 0,
                        'cache_hits': 0,
                        'cache_misses': 0,
                        'hit_rate': 0.0,
                        'avg_execution_time': 0.0,
                        'slow_queries': 0,
                        'n_plus_one_patterns': len(self.n_plus_one_patterns)
                    }
                
                total_queries = len(self.query_stats)
                avg_time = sum(s.execution_time for s in self.query_stats) / total_queries
                slow_count = len([s for s in self.query_stats if s.execution_time > self.slow_query_threshold])
                hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0.0
                
                return {
                    'enabled': self.enabled,
                    'total_queries': total_queries,
                    'cache_hits': self.cache_hits,
                    'cache_misses': self.cache_misses,
                    'hit_rate': round(hit_rate * 100, 2),
                    'avg_execution_time': round(avg_time, 3),
                    'cached_results': len(self.query_cache),
                    'slow_queries': slow_count,
                    'n_plus_one_patterns': len(self.n_plus_one_patterns),
                    'most_common_patterns': dict(list(sorted(
                        self.n_plus_one_patterns.items(),
                        key=lambda x: x[1],
                        reverse=True
                    ))[:5])
                }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {'enabled': self.enabled, 'error': str(e)}
    
    async def clear_cache(self) -> bool:
        """Clear query cache"""
        try:
            async with self.lock:
                self.query_cache.clear()
                return True
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    async def reset(self) -> bool:
        """Reset all statistics"""
        try:
            async with self.lock:
                self.query_cache.clear()
                self.query_stats.clear()
                self.execution_times.clear()
                self.n_plus_one_patterns.clear()
                self.cache_hits = 0
                self.cache_misses = 0
                return True
        except Exception as e:
            print(f"Error resetting optimizer: {e}")
            return False


def optimize_query(func):
    """Decorator to apply query optimization"""
    @wraps(func)
    async def wrapper(query: str, *args, **kwargs):
        optimizer = QueryOptimizer.get_instance()
        
        # Check cache first
        cached = await optimizer.get_cached_result(query)
        if cached is not None:
            return cached
        
        # Execute and cache
        start = time.time()
        result = await func(query, *args, **kwargs)
        execution_time = time.time() - start
        
        # Record and cache
        result_count = len(result) if isinstance(result, (list, tuple)) else 1
        await optimizer.record_execution(query, execution_time, result_count)
        await optimizer.cache_query_result(query, result)
        
        return result
    
    return wrapper
