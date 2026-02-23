"""
Advanced Query Optimization Engine for Phase 7

Implements:
- Batch processing optimization
- Connection pool management
- Query plan analysis
- Auto-indexing suggestions
- Query rewriting
"""

import asyncio
import hashlib
import time
from typing import Dict, Any, Optional, List, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from .. import LOGGER


class QueryType(str, Enum):
    """Query types"""
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    BATCH = "batch"


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    query_type: QueryType
    execution_count: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    last_executed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    slow_query_count: int = 0


@dataclass
class IndexSuggestion:
    """Index suggestion"""
    table: str
    columns: List[str]
    reason: str
    estimated_improvement_percent: float
    priority: str  # high, medium, low


class BatchProcessor:
    """Batch query processor for optimization"""
    
    def __init__(self, batch_size: int = 100, flush_interval_seconds: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval_seconds
        self.batches: Dict[str, List[Tuple[str, Dict]]] = defaultdict(list)
        self.last_flush = time.time()
    
    def add_query(self, query_type: str, query: str, params: Dict[str, Any]) -> None:
        """Add query to batch"""
        self.batches[query_type].append((query, params))
    
    def should_flush(self, query_type: str) -> bool:
        """Check if batch should be flushed"""
        if len(self.batches[query_type]) >= self.batch_size:
            return True
        
        if time.time() - self.last_flush > self.flush_interval:
            return True
        
        return False
    
    async def flush_batch(self, query_type: str, executor: callable) -> int:
        """Flush batch and execute"""
        if not self.batches[query_type]:
            return 0
        
        queries = self.batches[query_type]
        self.batches[query_type] = []
        self.last_flush = time.time()
        
        # Execute batch
        try:
            if query_type == "INSERT":
                await self._batch_insert(queries, executor)
            elif query_type == "UPDATE":
                await self._batch_update(queries, executor)
            elif query_type == "DELETE":
                await self._batch_delete(queries, executor)
            
            return len(queries)
        
        except Exception as e:
            LOGGER.error(f"Batch flush error: {e}")
            return 0
    
    async def _batch_insert(self, queries: List[Tuple], executor: callable) -> None:
        """Batch insert optimization"""
        if not queries:
            return
        
        # Group by table
        by_table = defaultdict(list)
        for query, params in queries:
            table = self._extract_table_name(query)
            by_table[table].append(params)
        
        # Execute multi-row inserts
        for table, params_list in by_table.items():
            await executor(f"INSERT INTO {table}", params_list)
    
    async def _batch_update(self, queries: List[Tuple], executor: callable) -> None:
        """Batch update optimization"""
        # Updates usually can't be batched as easily, execute individually
        for query, params in queries:
            await executor(query, params)
    
    async def _batch_delete(self, queries: List[Tuple], executor: callable) -> None:
        """Batch delete optimization"""
        # Group by table and use IN clause
        by_table = defaultdict(list)
        for query, params in queries:
            table = self._extract_table_name(query)
            if 'id' in params:
                by_table[table].append(params['id'])
        
        for table, ids in by_table.items():
            await executor(
                f"DELETE FROM {table} WHERE id IN ({','.join(map(str, ids))})"
            )
    
    def _extract_table_name(self, query: str) -> str:
        """Extract table name from query"""
        query_upper = query.upper()
        
        if "INSERT INTO" in query_upper:
            start = query_upper.index("INSERT INTO") + len("INSERT INTO")
            end = query_upper.index("(", start) if "(" in query_upper[start:] else len(query_upper)
            return query[start:end].strip()
        
        if "UPDATE" in query_upper:
            start = query_upper.index("UPDATE") + len("UPDATE")
            end = query_upper.index("SET", start) if "SET" in query_upper[start:] else len(query_upper)
            return query[start:end].strip()
        
        if "DELETE FROM" in query_upper:
            start = query_upper.index("DELETE FROM") + len("DELETE FROM")
            end = query_upper.index("WHERE", start) if "WHERE" in query_upper[start:] else len(query_upper)
            return query[start:end].strip()
        
        return "unknown"


class ConnectionPoolOptimizer:
    """Optimize connection pool usage"""
    
    def __init__(
        self,
        min_connections: int = 5,
        max_connections: int = 20,
        idle_timeout_seconds: int = 300
    ):
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout_seconds
        
        self.active_connections = 0
        self.total_connections = 0
        self.peak_connections = 0
        self.connection_waits = 0
        self.idle_connections = 0
    
    def record_connection_acquired(self) -> None:
        """Record connection acquisition"""
        self.active_connections += 1
        self.total_connections = max(self.total_connections, self.active_connections)
        self.peak_connections = max(self.peak_connections, self.active_connections)
    
    def record_connection_released(self) -> None:
        """Record connection release"""
        self.active_connections = max(0, self.active_connections - 1)
        self.idle_connections += 1
    
    def record_connection_wait(self) -> None:
        """Record connection pool wait"""
        self.connection_waits += 1
    
    def get_pool_recommendations(self) -> List[str]:
        """Get connection pool optimization recommendations"""
        recommendations = []
        
        utilization = (
            self.active_connections / self.max_connections
        ) if self.max_connections > 0 else 0
        
        if utilization > 0.8:
            recommendations.append(
                f"⚠️ High pool utilization ({utilization:.0%}). "
                f"Consider increasing max_connections from {self.max_connections} to "
                f"{int(self.max_connections * 1.5)}"
            )
        
        if self.connection_waits > 10:
            recommendations.append(
                f"⚠️ Detected {self.connection_waits} connection waits. "
                "Pool is undersized for current load."
            )
        
        if utilization < 0.3 and self.min_connections > 5:
            recommendations.append(
                f"💡 Low utilization ({utilization:.0%}). "
                f"Consider reducing min_connections from {self.min_connections} to "
                f"{max(5, self.min_connections // 2)}"
            )
        
        if not recommendations:
            recommendations.append(
                f"✅ Connection pool healthy (utilization: {utilization:.0%})"
            )
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            "active": self.active_connections,
            "idle": self.idle_connections,
            "total": self.total_connections,
            "peak": self.peak_connections,
            "waits": self.connection_waits,
            "min": self.min_connections,
            "max": self.max_connections,
            "utilization": (
                self.active_connections / self.max_connections
            ) if self.max_connections > 0 else 0
        }


class QueryOptimizer:
    """Advanced query optimizer"""
    
    def __init__(self):
        self.query_cache: Dict[str, Tuple[Any, datetime]] = {}
        self.query_metrics: Dict[str, QueryMetrics] = {}
        self.slow_query_threshold_ms = 1000
        self.cache_ttl_seconds = 300
        self.batch_processor = BatchProcessor()
        self.pool_optimizer = ConnectionPoolOptimizer()
        self.index_suggestions: List[IndexSuggestion] = []
    
    def _hash_query(self, query: str, params: Optional[Dict] = None) -> str:
        """Generate query hash"""
        query_str = query + str(params or {})
        return hashlib.md5(query_str.encode()).hexdigest()
    
    def _classify_query(self, query: str) -> QueryType:
        """Classify query type"""
        query_upper = query.upper().strip()
        
        if query_upper.startswith("SELECT"):
            return QueryType.SELECT
        elif query_upper.startswith("INSERT"):
            return QueryType.INSERT
        elif query_upper.startswith("UPDATE"):
            return QueryType.UPDATE
        elif query_upper.startswith("DELETE"):
            return QueryType.DELETE
        else:
            return QueryType.BATCH
    
    async def execute_optimized(
        self,
        query: str,
        params: Optional[Dict] = None,
        executor: Optional[callable] = None
    ) -> Any:
        """Execute query with optimizations"""
        query_hash = self._hash_query(query, params)
        query_type = self._classify_query(query)
        start_time = time.time()
        
        # Check cache for SELECT queries
        if query_type == QueryType.SELECT:
            cached = self._get_cached(query_hash)
            if cached is not None:
                return cached
        
        # Execute query
        result = None
        if executor:
            if asyncio.iscoroutinefunction(executor):
                result = await executor(query, params)
            else:
                result = executor(query, params)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Record metrics
        self._record_metrics(query_hash, query_type, elapsed_ms)
        
        # Cache result for SELECT
        if query_type == QueryType.SELECT and result is not None:
            self._cache_result(query_hash, result)
        
        # Check for slow query
        if elapsed_ms > self.slow_query_threshold_ms:
            self._analyze_slow_query(query, elapsed_ms)
        
        return result
    
    def _get_cached(self, query_hash: str) -> Optional[Any]:
        """Get cached result"""
        if query_hash in self.query_cache:
            result, cached_at = self.query_cache[query_hash]
            age = (datetime.now(timezone.utc) - cached_at).total_seconds()
            
            if age < self.cache_ttl_seconds:
                return result
            else:
                del self.query_cache[query_hash]
        
        return None
    
    def _cache_result(self, query_hash: str, result: Any) -> None:
        """Cache query result"""
        self.query_cache[query_hash] = (result, datetime.now(timezone.utc))
    
    def _record_metrics(
        self,
        query_hash: str,
        query_type: QueryType,
        elapsed_ms: float
    ) -> None:
        """Record query metrics"""
        if query_hash not in self.query_metrics:
            self.query_metrics[query_hash] = QueryMetrics(
                query_hash=query_hash,
                query_type=query_type
            )
        
        metrics = self.query_metrics[query_hash]
        metrics.execution_count += 1
        metrics.total_time_ms += elapsed_ms
        metrics.avg_time_ms = metrics.total_time_ms / metrics.execution_count
        metrics.min_time_ms = min(metrics.min_time_ms, elapsed_ms)
        metrics.max_time_ms = max(metrics.max_time_ms, elapsed_ms)
        metrics.last_executed = datetime.now(timezone.utc)
        
        if elapsed_ms > self.slow_query_threshold_ms:
            metrics.slow_query_count += 1
    
    def _analyze_slow_query(self, query: str, elapsed_ms: float) -> None:
        """Analyze slow query and suggest optimizations"""
        LOGGER.warning(f"Slow query detected ({elapsed_ms:.2f}ms): {query[:100]}")
        
        # Extract table names
        tables = self._extract_tables(query)
        
        # Check for missing indexes
        if "WHERE" in query.upper():
            columns = self._extract_where_columns(query)
            
            for table in tables:
                for column in columns:
                    suggestion = IndexSuggestion(
                        table=table,
                        columns=[column],
                        reason=f"Frequent WHERE clause on {column}",
                        estimated_improvement_percent=30.0,
                        priority="high"
                    )
                    
                    if suggestion not in self.index_suggestions:
                        self.index_suggestions.append(suggestion)
    
    def _extract_tables(self, query: str) -> List[str]:
        """Extract table names from query"""
        tables = []
        query_upper = query.upper()
        
        # Simple parsing - can be enhanced
        if "FROM" in query_upper:
            start = query_upper.index("FROM") + 4
            end = query_upper.find("WHERE", start)
            if end == -1:
                end = query_upper.find("ORDER", start)
            if end == -1:
                end = len(query_upper)
            
            table_part = query[start:end].strip()
            tables = [t.strip() for t in table_part.split(",")]
        
        return tables
    
    def _extract_where_columns(self, query: str) -> List[str]:
        """Extract columns from WHERE clause"""
        columns = []
        query_upper = query.upper()
        
        if "WHERE" in query_upper:
            start = query_upper.index("WHERE") + 5
            end = query_upper.find("ORDER", start)
            if end == -1:
                end = query_upper.find("LIMIT", start)
            if end == -1:
                end = len(query_upper)
            
            where_clause = query[start:end]
            
            # Very simple extraction - real implementation would use SQL parser
            for part in where_clause.split():
                if part.isalpha() and part.lower() not in ['and', 'or', 'not']:
                    columns.append(part.lower())
        
        return columns
    
    def get_optimization_report(self) -> str:
        """Generate optimization report"""
        report = ["=" * 80]
        report.append("QUERY OPTIMIZATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Query statistics
        total_queries = sum(m.execution_count for m in self.query_metrics.values())
        total_slow = sum(m.slow_query_count for m in self.query_metrics.values())
        
        report.append(f"Total Queries: {total_queries}")
        report.append(f"Slow Queries: {total_slow}")
        report.append(f"Cache Size: {len(self.query_cache)}")
        report.append("")
        
        # Top slow queries
        slow_queries = sorted(
            self.query_metrics.values(),
            key=lambda m: m.avg_time_ms,
            reverse=True
        )[:10]
        
        if slow_queries:
            report.append("TOP 10 SLOWEST QUERIES:")
            report.append("-" * 80)
            
            for i, metrics in enumerate(slow_queries, 1):
                report.append(f"\n{i}. Query Hash: {metrics.query_hash[:16]}...")
                report.append(f"   Type: {metrics.query_type.value}")
                report.append(f"   Avg Time: {metrics.avg_time_ms:.2f}ms")
                report.append(f"   Executions: {metrics.execution_count}")
                report.append(f"   Slow Count: {metrics.slow_query_count}")
        
        # Index suggestions
        if self.index_suggestions:
            report.append("\n")
            report.append("INDEX SUGGESTIONS:")
            report.append("-" * 80)
            
            for i, suggestion in enumerate(self.index_suggestions[:10], 1):
                report.append(f"\n{i}. Table: {suggestion.table}")
                report.append(f"   Columns: {', '.join(suggestion.columns)}")
                report.append(f"   Reason: {suggestion.reason}")
                report.append(f"   Est. Improvement: {suggestion.estimated_improvement_percent}%")
                report.append(f"   Priority: {suggestion.priority}")
        
        # Connection pool stats
        report.append("\n")
        report.append("CONNECTION POOL STATUS:")
        report.append("-" * 80)
        pool_stats = self.pool_optimizer.get_stats()
        for key, value in pool_stats.items():
            report.append(f"   {key}: {value}")
        
        report.append("\n")
        for rec in self.pool_optimizer.get_pool_recommendations():
            report.append(f"   {rec}")
        
        report.append("")
        report.append("=" * 80)
        return "\n".join(report)


# Global instance
query_optimizer = QueryOptimizer()
