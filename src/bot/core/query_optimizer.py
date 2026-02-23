"""
Phase 4: Query Optimizer
Performance optimization through query analysis, caching, and suggestions
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import hashlib
import logging

from .query_optimizer_models import QueryType, OptimizationResult, QueryStatistics

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Singleton Query Optimizer for analyzing and optimizing database queries
    """

    _instance: Optional['QueryOptimizer'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.enabled = False
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.query_statistics: Dict[str, QueryStatistics] = {}
        self.slow_query_threshold = 1.0  # 1 second
        self.cache_ttl = 300  # 5 minutes
        self.n_plus_one_detector_enabled = True

    @classmethod
    def get_instance(cls) -> 'QueryOptimizer':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = QueryOptimizer()
        return cls._instance

    async def enable(self) -> bool:
        """
        Enable the Query Optimizer for performance analysis.
        
        This activates query analysis, caching, N+1 detection, and
        performance recommendations.
        
        Returns:
            bool: True if successfully enabled
            
        Example:
            >>> optimizer = QueryOptimizer.get_instance()
            >>> await optimizer.enable()
            True
        """
        async with self._lock:
            self.enabled = True
            logger.info("Query Optimizer enabled")
            return True

    async def disable(self) -> bool:
        """
        Disable the Query Optimizer and clear caches.
        
        This stops all query analysis and clears the query cache.
        Statistics are preserved.
        
        Returns:
            bool: True if successfully disabled
        """
        async with self._lock:
            self.enabled = False
            self.query_cache.clear()
            logger.info("Query Optimizer disabled")
            return True

    def _parse_query_type(self, query: str) -> QueryType:
        """Determine query type from query string"""
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return QueryType.SELECT
        elif query_upper.startswith("INSERT"):
            return QueryType.INSERT
        elif query_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        elif query_upper.startswith("DELETE"):
            return QueryType.DELETE
        elif "{" in query and "query" in query.lower():
            return QueryType.GRAPHQL
        return QueryType.UNKNOWN

    def _generate_query_hash(self, query: str) -> str:
        """
        Generate MD5 hash for query caching and deduplication.
        
        Args:
            query: SQL or GraphQL query string
            
        Returns:
            32-character hex hash of the query
        """
        return hashlib.md5(query.encode()).hexdigest()

    async def analyze_query(self, query: str) -> OptimizationResult:
        """
        Analyze query for optimization opportunities
        
        Args:
            query: SQL or GraphQL query string
            
        Returns:
            OptimizationResult with analysis and recommendations
        """
        if not self.enabled:
            return OptimizationResult(query=query, query_type=QueryType.UNKNOWN)

        try:
            query_type = self._parse_query_type(query)
            result = OptimizationResult(query=query, query_type=query_type)

            # Detect N+1 queries
            if self.n_plus_one_detector_enabled:
                await self._detect_n_plus_one(query, result)

            # Suggest caching
            if query_type == QueryType.SELECT:
                result.cache_suggestion = True
                result.recommendations.append("Consider caching SELECT query results")
                result.estimated_improvement_percent = 30.0

            # Suggest indexes based on common patterns
            await self._suggest_indexes(query, result)

            # Check for inefficient patterns
            await self._detect_inefficiencies(query, result)

            return result
        except Exception as e:
            logger.error(f"Query analysis error: {e}")
            return OptimizationResult(query=query, query_type=QueryType.UNKNOWN)

    async def _detect_n_plus_one(self, query: str, result: OptimizationResult) -> None:
        """
        Detect potential N+1 query anti-patterns.
        
        N+1 queries occur when an initial query is followed by N additional
        queries in a loop. This causes severe performance degradation.
        
        Args:
            query: Query to analyze
            result: OptimizationResult to update with findings
            
        Example:
            Instead of:
                users = SELECT * FROM users
                for user in users:
                    posts = SELECT * FROM posts WHERE user_id = {user.id}  # N queries!
            
            Use:
                users = SELECT * FROM users
                posts = SELECT * FROM posts WHERE user_id IN (user_ids)  # 1 query
        """
        # Check for repeated similar queries pattern
        similar_queries = [
            q for q in self.query_statistics.keys()
            if self._query_similarity(query, q) > 0.8
        ]

        if len(similar_queries) > 3:
            result.n_plus_one_detected = True
            result.recommendations.append("Possible N+1 query pattern detected - consider batch loading")
            result.estimated_improvement_percent = max(result.estimated_improvement_percent, 50.0)

    def _query_similarity(self, q1: str, q2: str) -> float:
        """Calculate similarity between two queries (0-1)"""
        # Simple heuristic: compare query structure
        q1_words = set(q1.upper().split())
        q2_words = set(q2.upper().split())
        
        if not q1_words or not q2_words:
            return 0.0
        
        intersection = len(q1_words & q2_words)
        union = len(q1_words | q2_words)
        return intersection / union if union > 0 else 0.0

    async def _suggest_indexes(self, query: str, result: OptimizationResult) -> None:
        """
        Suggest database indexes based on query patterns.
        
        Indexes dramatically improve query performance by allowing the
        database to locate rows without scanning the entire table.
        
        Args:
            query: SQL query to analyze
            result: OptimizationResult to update with index suggestions
            
        Note:
            These are heuristic suggestions. Actual index strategy should
            consider query frequency, table size, and write performance.
        """
        query_upper = query.upper()
        
        # Suggest indexes for WHERE clauses
        if "WHERE" in query_upper:
            result.index_suggestions.append("Consider index on WHERE clause columns")
        
        # Suggest indexes for JOIN conditions
        if "JOIN" in query_upper:
            result.index_suggestions.append("Consider index on JOIN columns")
        
        # Suggest indexes for ORDER BY
        if "ORDER BY" in query_upper:
            result.index_suggestions.append("Consider index on ORDER BY columns")

    async def _detect_inefficiencies(self, query: str, result: OptimizationResult) -> None:
        """Detect inefficient query patterns"""
        query_upper = query.upper()
        
        # Detect SELECT * (usually inefficient)
        if "SELECT *" in query_upper:
            result.recommendations.append("Avoid SELECT * - specify needed columns")
            result.estimated_improvement_percent += 10.0
        
        # Detect missing LIMIT in SELECT
        if "SELECT" in query_upper and "LIMIT" not in query_upper:
            if "ORDER BY" in query_upper:
                result.recommendations.append("Consider adding LIMIT clause")

    async def cache_query_result(
        self,
        query: str,
        result: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache query result
        
        Args:
            query: Query string
            result: Query result to cache
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            query_hash = self._generate_query_hash(query)
            expiry = datetime.now() + timedelta(seconds=ttl or self.cache_ttl)
            self.query_cache[query_hash] = (result, expiry)
            
            # Update statistics
            if query_hash not in self.query_statistics:
                self.query_statistics[query_hash] = QueryStatistics(
                    query_hash=query_hash,
                    query=query
                )
            
            return True
        except Exception as e:
            logger.error(f"Error caching query result: {e}")
            return False

    async def get_cached_result(self, query: str) -> Optional[Any]:
        """
        Get cached query result if available and not expired
        
        Args:
            query: Query string
            
        Returns:
            Cached result if found and valid, None otherwise
        """
        if not self.enabled:
            return None

        try:
            query_hash = self._generate_query_hash(query)
            
            if query_hash in self.query_cache:
                result, expiry = self.query_cache[query_hash]
                
                # Check if expired
                if datetime.now() < expiry:
                    # Update statistics
                    if query_hash in self.query_statistics:
                        self.query_statistics[query_hash].cache_hits += 1
                    return result
                else:
                    # Remove expired entry
                    del self.query_cache[query_hash]
            
            # Record cache miss
            if query_hash in self.query_statistics:
                self.query_statistics[query_hash].cache_misses += 1
            
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached result: {e}")
            return None

    async def record_execution(
        self,
        query: str,
        execution_time_ms: float,
        result_count: int = 0,
        cache_hit: bool = False
    ) -> bool:
        """
        Record query execution statistics
        
        Args:
            query: Query string
            execution_time_ms: Execution time in milliseconds
            result_count: Number of results returned
            cache_hit: Whether this was served from cache
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False

        try:
            query_hash = self._generate_query_hash(query)
            
            if query_hash not in self.query_statistics:
                self.query_statistics[query_hash] = QueryStatistics(
                    query_hash=query_hash,
                    query=query
                )
            
            stats = self.query_statistics[query_hash]
            stats.execution_count += 1
            stats.total_execution_time_ms += execution_time_ms
            stats.avg_execution_time_ms = stats.total_execution_time_ms / stats.execution_count
            stats.min_execution_time_ms = min(stats.min_execution_time_ms, execution_time_ms)
            stats.max_execution_time_ms = max(stats.max_execution_time_ms, execution_time_ms)
            stats.last_executed = datetime.now()
            
            if cache_hit:
                stats.cache_hits += 1
            
            return True
        except Exception as e:
            logger.error(f"Error recording execution: {e}")
            return False

    async def get_slow_queries(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Get queries slower than threshold
        
        Args:
            threshold: Threshold in seconds (uses default if None)
            
        Returns:
            List of slow queries with statistics
        """
        threshold_ms = (threshold or self.slow_query_threshold) * 1000
        
        slow = []
        for query_hash, stats in self.query_statistics.items():
            if stats.avg_execution_time_ms > threshold_ms:
                slow.append({
                    'query': stats.query,
                    'avg_execution_time_ms': stats.avg_execution_time_ms,
                    'max_execution_time_ms': stats.max_execution_time_ms,
                    'execution_count': stats.execution_count,
                    'cache_hit_rate': (
                        stats.cache_hits / (stats.cache_hits + stats.cache_misses)
                        if (stats.cache_hits + stats.cache_misses) > 0 else 0.0
                    )
                })
        
        return sorted(slow, key=lambda x: x['avg_execution_time_ms'], reverse=True)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get overall statistics about query optimization"""
        total_queries = len(self.query_statistics)
        total_hits = sum(s.cache_hits for s in self.query_statistics.values())
        total_misses = sum(s.cache_misses for s in self.query_statistics.values())
        total_executions = sum(s.execution_count for s in self.query_statistics.values())
        
        hit_rate = (total_hits / (total_hits + total_misses) * 100) if (total_hits + total_misses) > 0 else 0.0
        
        avg_execution_time = (
            sum(s.avg_execution_time_ms for s in self.query_statistics.values()) / total_queries
            if total_queries > 0 else 0.0
        )
        
        return {
            'enabled': self.enabled,
            'total_unique_queries': total_queries,
            'total_executions': total_executions,
            'cache_hits': total_hits,
            'cache_misses': total_misses,
            'cache_hit_rate_percent': hit_rate,
            'avg_execution_time_ms': avg_execution_time,
            'cached_results_count': len(self.query_cache),
            'slow_query_threshold_seconds': self.slow_query_threshold,
        }

    async def clear_cache(self) -> bool:
        """Clear all cached query results"""
        try:
            self.query_cache.clear()
            logger.info("Query cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    async def clear_statistics(self) -> bool:
        """Clear all statistics"""
        try:
            self.query_statistics.clear()
            logger.info("Query statistics cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing statistics: {e}")
            return False
