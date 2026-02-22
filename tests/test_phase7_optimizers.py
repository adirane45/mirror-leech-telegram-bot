"""
Tests for Phase 7 optimization modules (JIT & Query Optimizer)
"""

import pytest
import asyncio
import time

from bot.core.jit_optimizer import (
    JITOptimizer,
    CythonOptimizationEngine,
    PerformanceMonitor,
    OptimizationType,
    HotSpot
)
from bot.core.advanced_query_optimizer import (
    QueryOptimizer,
    BatchProcessor,
    ConnectionPoolOptimizer,
    QueryType,
    IndexSuggestion
)


# --- JIT OPTIMIZER TESTS ---

def test_jit_optimizer_initialization():
    """Test JIT optimizer initialization"""
    optimizer = JITOptimizer()
    assert optimizer is not None
    assert optimizer.is_profiling is False
    assert len(optimizer.hotspots) == 0


def test_jit_profiling_lifecycle():
    """Test profiling start/stop"""
    optimizer = JITOptimizer()
    
    optimizer.start_profiling()
    assert optimizer.is_profiling is True
    
    # Do some work
    def cpu_bound_work():
        total = 0
        for i in range(10000):
            total += i * i
        return total
    
    cpu_bound_work()
    
    optimizer.stop_profiling()
    assert optimizer.is_profiling is False


def test_jit_hotspot_detection():
    """Test hotspot detection"""
    optimizer = JITOptimizer()
    
    optimizer.start_profiling()
    
    # Simulate CPU-intensive work
    def slow_function():
        return sum(i ** 2 for i in range(1000))
    
    for _ in range(10):
        slow_function()
    
    optimizer.stop_profiling()
    analysis = optimizer.analyze_profile()
    
    assert "total_hotspots" in analysis
    assert isinstance(analysis["total_hotspots"], int)


def test_cython_engine():
    """Test Cython optimization engine"""
    engine = CythonOptimizationEngine()
    
    # Analyze sample function
    def sample_function(data):
        result = 0
        for item in data:
            result += item * 2
        return result
    
    suggestions = engine.analyze_function(sample_function)
    
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0


def test_cython_stub_generation():
    """Test Cython stub generation"""
    engine = CythonOptimizationEngine()
    
    stub = engine.generate_cython_stub("process_data", "bot.core.module")
    
    assert "cython:" in stub
    assert "cdef" in stub
    assert "process_data" in stub.lower()


def test_optimization_report():
    """Test optimization report generation"""
    optimizer = JITOptimizer()
    
    optimizer.start_profiling()
    
    # Some work
    def work():
        return [i ** 2 for i in range(100)]
    
    work()
    
    optimizer.stop_profiling()
    optimizer.analyze_profile()
    
    report = optimizer.get_optimization_report()
    
    assert isinstance(report, str)
    assert "OPTIMIZATION REPORT" in report


def test_performance_monitor():
    """Test performance monitoring"""
    monitor = PerformanceMonitor()
    
    metrics = monitor.get_metrics()
    
    assert "uptime_seconds" in metrics
    assert "memory_mb" in metrics
    assert "cpu_percent" in metrics
    assert metrics["uptime_seconds"] >= 0
    assert metrics["memory_mb"] > 0


# --- QUERY OPTIMIZER TESTS ---

def test_query_optimizer_initialization():
    """Test query optimizer initialization"""
    optimizer = QueryOptimizer()
    
    assert optimizer is not None
    assert optimizer.slow_query_threshold_ms == 1000
    assert len(optimizer.query_cache) == 0


def test_query_classification():
    """Test query type classification"""
    optimizer = QueryOptimizer()
    
    assert optimizer._classify_query("SELECT * FROM users") == QueryType.SELECT
    assert optimizer._classify_query("INSERT INTO users VALUES (1)") == QueryType.INSERT
    assert optimizer._classify_query("UPDATE users SET name='test'") == QueryType.UPDATE
    assert optimizer._classify_query("DELETE FROM users WHERE id=1") == QueryType.DELETE


def test_query_hashing():
    """Test query hashing"""
    optimizer = QueryOptimizer()
    
    hash1 = optimizer._hash_query("SELECT * FROM users", {"id": 1})
    hash2 = optimizer._hash_query("SELECT * FROM users", {"id": 1})
    hash3 = optimizer._hash_query("SELECT * FROM users", {"id": 2})
    
    assert hash1 == hash2
    assert hash1 != hash3


@pytest.mark.asyncio
async def test_query_caching():
    """Test query result caching"""
    optimizer = QueryOptimizer()
    
    async def mock_executor(query, params):
        return [{"id": 1, "name": "test"}]
    
    # First execution - should cache
    result1 = await optimizer.execute_optimized(
        "SELECT * FROM users",
        {"id": 1},
        mock_executor
    )
    
    # Second execution - should use cache
    result2 = await optimizer.execute_optimized(
        "SELECT * FROM users",
        {"id": 1},
        mock_executor
    )
    
    assert result1 == result2
    assert len(optimizer.query_cache) == 1


def test_table_extraction():
    """Test table name extraction"""
    optimizer = QueryOptimizer()
    
    tables = optimizer._extract_tables("SELECT * FROM users WHERE id=1")
    assert "users" in tables
    
    tables2 = optimizer._extract_tables("SELECT * FROM users, orders WHERE users.id=orders.user_id")
    assert len(tables2) == 2


def test_batch_processor():
    """Test batch processor"""
    processor = BatchProcessor(batch_size=10)
    
    # Add queries
    for i in range(5):
        processor.add_query("INSERT", "INSERT INTO users VALUES (?)", {"id": i})
    
    assert len(processor.batches["INSERT"]) == 5
    assert processor.should_flush("INSERT") is False
    
    # Add more to trigger batch
    for i in range(10):
        processor.add_query("INSERT", "INSERT INTO users VALUES (?)", {"id": i})
    
    assert processor.should_flush("INSERT") is True


@pytest.mark.asyncio
async def test_batch_flush():
    """Test batch flushing"""
    processor = BatchProcessor(batch_size=5)
    
    async def mock_executor(query, params=None):
        return True
    
    # Add queries
    for i in range(3):
        processor.add_query("INSERT", "INSERT INTO users VALUES (?)", {"id": i})
    
    # Flush
    count = await processor.flush_batch("INSERT", mock_executor)
    
    assert count == 3
    assert len(processor.batches["INSERT"]) == 0


def test_connection_pool_optimizer():
    """Test connection pool optimizer"""
    pool = ConnectionPoolOptimizer(min_connections=5, max_connections=20)
    
    # Simulate connections
    for _ in range(15):
        pool.record_connection_acquired()
    
    assert pool.active_connections == 15
    assert pool.peak_connections == 15
    
    # Release some
    for _ in range(5):
        pool.record_connection_released()
    
    assert pool.active_connections == 10


def test_pool_recommendations():
    """Test connection pool recommendations"""
    pool = ConnectionPoolOptimizer(min_connections=5, max_connections=10)
    
    # Simulate high load
    for _ in range(9):
        pool.record_connection_acquired()
    
    recommendations = pool.get_pool_recommendations()
    
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0


def test_pool_stats():
    """Test pool statistics"""
    pool = ConnectionPoolOptimizer()
    
    pool.record_connection_acquired()
    pool.record_connection_acquired()
    
    stats = pool.get_stats()
    
    assert "active" in stats
    assert "utilization" in stats
    assert stats["active"] == 2


def test_index_suggestions():
    """Test index suggestions"""
    optimizer = QueryOptimizer()
    
    # Simulate slow query with WHERE clause
    slow_query = "SELECT * FROM users WHERE email = 'test@test.com'"
    optimizer._analyze_slow_query(slow_query, 1500)
    
    assert len(optimizer.index_suggestions) > 0


def test_optimization_report_generation():
    """Test optimization report generation"""
    optimizer = QueryOptimizer()
    
    # Add some metrics
    optimizer._record_metrics("hash1", QueryType.SELECT, 500)
    optimizer._record_metrics("hash2", QueryType.INSERT, 1500)
    
    report = optimizer.get_optimization_report()
    
    assert isinstance(report, str)
    assert "OPTIMIZATION REPORT" in report
    assert "CONNECTION POOL" in report


@pytest.mark.asyncio
async def test_query_metrics_recording():
    """Test query metrics recording"""
    optimizer = QueryOptimizer()
    
    async def mock_executor(query, params):
        await asyncio.sleep(0.01)  # Simulate query time
        return []
    
    # Execute different queries to avoid cache
    for i in range(5):
        await optimizer.execute_optimized(
            f"SELECT * FROM users WHERE id={i}",
            None,
            mock_executor
        )
    
    # Check metrics - should have 5 different queries
    assert len(optimizer.query_metrics) == 5
    
    for metrics in optimizer.query_metrics.values():
        assert metrics.execution_count == 1
        assert metrics.avg_time_ms > 0


def test_slow_query_detection():
    """Test slow query detection"""
    optimizer = QueryOptimizer()
    optimizer.slow_query_threshold_ms = 100
    
    # Record slow query
    optimizer._record_metrics("slow_hash", QueryType.SELECT, 500)
    
    metrics = optimizer.query_metrics["slow_hash"]
    assert metrics.slow_query_count == 1


@pytest.mark.asyncio
async def test_cache_ttl():
    """Test cache TTL expiration"""
    optimizer = QueryOptimizer()
    optimizer.cache_ttl_seconds = 1  # 1 second TTL
    
    # Cache a result
    query_hash = optimizer._hash_query("SELECT * FROM users")
    optimizer._cache_result(query_hash, [{"id": 1}])
    
    # Should be cached
    cached = optimizer._get_cached(query_hash)
    assert cached is not None
    
    # Wait for TTL
    await asyncio.sleep(1.5)
    
    # Should be expired
    cached_after = optimizer._get_cached(query_hash)
    assert cached_after is None
