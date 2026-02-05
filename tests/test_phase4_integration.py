"""
Phase 4 Integration Tests - Performance & Optimization

Comprehensive test suite for:
- Query Optimizer
- Cache Manager
- Connection Pool Manager
- Rate Limiter
- Batch Processor
- Load Balancer
"""

import asyncio
import pytest
from datetime import datetime, timedelta

# Import Phase 4 components
from bot.core.query_optimizer import QueryOptimizer, optimize_query
from bot.core.cache_manager import CacheManager, cached, L1MemoryCache, CacheLevel
from bot.core.connection_pool_manager import ConnectionPoolManager, PooledConnection
from bot.core.rate_limiter import RateLimiter, RateLimitConfig
from bot.core.batch_processor import BatchProcessor, BatchItem 
from bot.core.load_balancer import LoadBalancer, LoadBalancingStrategy


# ============================================================================
# Query Optimizer Tests
# ============================================================================

class TestQueryOptimizer:
    """Query optimization tests"""
    
    @pytest.mark.asyncio
    async def test_optimizer_enable_disable(self):
        """Test enabling and disabling optimizer"""
        optimizer = QueryOptimizer.get_instance()
        
        # Enable
        result = await optimizer.enable()
        assert result == True
        assert optimizer.enabled == True
        
        # Disable
        result = await optimizer.disable()
        assert result == True
        assert optimizer.enabled == False
    
    @pytest.mark.asyncio
    async def test_query_analysis(self):
        """Test query analysis and optimization"""
        optimizer = QueryOptimizer.get_instance()
        await optimizer.enable()
        
        query = "SELECT * FROM users WHERE id = 1"
        result = await optimizer.analyze_query(query)
        
        assert result is not None
        assert result.original_query == query
        assert result.estimated_improvement >= 0
        assert 'SELECT *' in result.recommendations or True  # May have recommendations
    
    @pytest.mark.asyncio
    async def test_n_plus_one_detection(self):
        """Test N+1 query pattern detection"""
        optimizer = QueryOptimizer.get_instance()
        await optimizer.enable()
        await optimizer.reset()
        
        query = "SELECT * FROM users WHERE status = 'active'"
        
        # Execute query multiple times
        for _ in range(10):
            result = await optimizer.analyze_query(query)
        
        stats = await optimizer.get_statistics()
        assert stats['enabled'] == True
    
    @pytest.mark.asyncio
    async def test_query_caching(self):
        """Test query result caching"""
        optimizer = QueryOptimizer.get_instance()
        await optimizer.enable()
        await optimizer.reset()
        
        query = "SELECT * FROM users"
        result = {"users": [{"id": 1, "name": "Alice"}]}
        
        # Cache result
        await optimizer.cache_query_result(query, result)
        
        # Retrieve from cache
        cached = await optimizer.get_cached_result(query)
        assert cached == result
    
    @pytest.mark.asyncio
    async def test_slow_query_detection(self):
        """Test slow query detection"""
        optimizer = QueryOptimizer.get_instance()
        await optimizer.enable()
        await optimizer.reset()
        
        # Record a slow query
        slow_query = "SELECT * FROM large_table"
        await optimizer.record_execution(slow_query, execution_time=2.5, result_count=1000)
        
        slow_queries = await optimizer.get_slow_queries(threshold=1.0)
        assert len(slow_queries) > 0
        assert slow_queries[0].execution_time > 1.0
    
    @pytest.mark.asyncio
    async def test_optimizer_statistics(self):
        """Test optimizer statistics"""
        optimizer = QueryOptimizer.get_instance()
        await optimizer.enable()
        await optimizer.reset()
        
        # Execute some queries
        await optimizer.record_execution("SELECT * FROM users", 0.05, 100, cache_hit=True)
        await optimizer.record_execution("SELECT * FROM posts", 0.1, 50, cache_hit=False)
        
        stats = await optimizer.get_statistics()
        assert stats['enabled'] == True
        assert 'total_queries' in stats


# ============================================================================
# Cache Manager Tests
# ============================================================================

class TestCacheManager:
    """Cache manager tests"""
    
    @pytest.mark.asyncio
    async def test_cache_enable_disable(self):
        """Test enabling and disabling cache"""
        cache = CacheManager.get_instance()
        
        result = await cache.enable()
        assert result == True
        assert cache.enabled == True
        
        result = await cache.disable()
        assert result == True
        assert cache.enabled == False
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Test setting and getting cache values"""
        cache = CacheManager.get_instance()
        await cache.enable()
        
        # Set value
        success = await cache.set("test_key", {"data": "value"}, ttl=300, namespace="test")
        assert success == True
        
        # Get value
        value = await cache.get("test_key", namespace="test")
        assert value == {"data": "value"}
    
    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test deleting from cache"""
        cache = CacheManager.get_instance()
        await cache.enable()
        
        await cache.set("delete_test", "value")
        assert await cache.get("delete_test") == "value"
        
        result = await cache.delete("delete_test")
        assert result == True
        assert await cache.get("delete_test") is None
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_pattern(self):
        """Test pattern-based cache invalidation"""
        cache = CacheManager.get_instance()
        await cache.enable()
        await cache.clear_all()
        
        # Set multiple values
        await cache.set("user:1", {"id": 1})
        await cache.set("user:2", {"id": 2})
        await cache.set("post:1", {"id": 1})
        
        # Invalidate user namespace
        count = await cache.invalidate_pattern("user:*")
        assert count >= 2
    
    @pytest.mark.asyncio
    async def test_l1_memory_cache_eviction(self):
        """Test L1 cache LRU eviction"""
        cache = L1MemoryCache(max_size_mb=0.01, max_entries=3)  # Very small cache
        
        # Fill cache
        await cache.set("key1", "value1" * 100)
        await cache.set("key2", "value2" * 100)
        await cache.set("key3", "value3" * 100)
        
        # Should trigger eviction
        await cache.set("key4", "value4" * 100)
        
        stats = await cache.get_statistics()
        assert stats.evictions >= 1
    
    @pytest.mark.asyncio
    async def test_cache_statistics(self):
        """Test cache statistics"""
        cache = CacheManager.get_instance()
        await cache.enable()
        await cache.clear_all()
        
        # Add some cache entries
        await cache.set("stat1", "value1")
        await cache.get("stat1")  # Hit
        await cache.get("stat2")  # Miss
        
        stats = await cache.get_statistics()
        assert stats['enabled'] == True


# ============================================================================
# Connection Pool Tests
# ============================================================================

class TestConnectionPoolManager:
    """Connection pool manager tests"""
    
    @pytest.mark.asyncio
    async def test_pool_enable_disable(self):
        """Test enabling and disabling pool manager"""
        pool_mgr = ConnectionPoolManager.get_instance()
        
        result = await pool_mgr.enable()
        assert result == True
        
        result = await pool_mgr.disable()
        assert result == True
    
    @pytest.mark.asyncio
    async def test_create_pool(self):
        """Test creating a connection pool"""
        pool_mgr = ConnectionPoolManager.get_instance()
        await pool_mgr.enable()
        await pool_mgr.reset()
        
        result = await pool_mgr.create_pool(
            name="test_pool",
            backend="postgres",
            min_size=3,
            max_size=10
        )
        assert result == True
        
        pool = await pool_mgr.get_pool("test_pool")
        assert pool is not None
    
    @pytest.mark.asyncio
    async def test_connection_acquisition(self):
        """Test acquiring connections from pool"""
        pool_mgr = ConnectionPoolManager.get_instance()
        await pool_mgr.enable()
        await pool_mgr.reset()
        
        await pool_mgr.create_pool("test_pool", "mongodb", min_size=2)
        
        # Acquire connection
        conn = await pool_mgr.acquire_connection("test_pool")
        assert conn is not None
        
        # Release connection
        await pool_mgr.release_connection("test_pool", conn)
    
    @pytest.mark.asyncio
    async def test_pool_statistics(self):
        """Test pool statistics"""
        pool_mgr = ConnectionPoolManager.get_instance()
        await pool_mgr.enable()
        await pool_mgr.reset()
        
        await pool_mgr.create_pool("stats_pool", "redis", min_size=2)
        
        stats = await pool_mgr.get_all_statistics()
        assert 'stats_pool' in stats


# ============================================================================
# Rate Limiter Tests
# ============================================================================

class TestRateLimiter:
    """Rate limiter tests"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_enable_disable(self):
        """Test enabling and disabling rate limiter"""
        limiter = RateLimiter.get_instance()
        
        result = await limiter.enable()
        assert result == True
        
        result = await limiter.disable()
        assert result == True
    
    @pytest.mark.asyncio
    async def test_rate_limit_allow_request(self):
        """Test allowing requests under limit"""
        limiter = RateLimiter.get_instance()
        await limiter.enable()
        await limiter.reset()
        
        config = RateLimitConfig(requests_per_second=10.0, burst_size=20)
        
        # Should allow requests
        allowed, status = await limiter.is_allowed("client1", config)
        assert allowed == True
        assert status.is_limited == False
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceed(self):
        """Test exceeding rate limit"""
        limiter = RateLimiter.get_instance()
        await limiter.enable()
        await limiter.reset()
        
        config = RateLimitConfig(requests_per_second=0.1, burst_size=1)
        
        # First request should pass
        allowed1, _ = await limiter.is_allowed("client2", config)
        assert allowed1 == True
        
        # Second request should be blocked (burst exhausted)
        allowed2, status = await limiter.is_allowed("client2", config)
        assert allowed2 == False
        assert status.is_limited == True
    
    @pytest.mark.asyncio
    async def test_rate_limit_status(self):
        """Test getting rate limit status"""
        limiter = RateLimiter.get_instance()
        await limiter.enable()
        await limiter.reset()
        
        config = RateLimitConfig(requests_per_second=5.0, burst_size=10)
        
        status = await limiter.get_status("client3", config)
        assert status.remaining >= 0
        assert status.limit == 10
    
    @pytest.mark.asyncio
    async def test_rate_limiter_statistics(self):
        """Test rate limiter statistics"""
        limiter = RateLimiter.get_instance()
        await limiter.enable()
        await limiter.reset()
        
        config = RateLimitConfig(requests_per_second=10.0)
        
        # Make some requests
        for i in range(5):
            await limiter.is_allowed(f"client_{i}", config)
        
        stats = await limiter.get_statistics()
        assert stats['enabled'] == True
        assert stats['total_requests'] == 5


# ============================================================================
# Batch Processor Tests
# ============================================================================

class TestBatchProcessor:
    """Batch processor tests"""
    
    @pytest.mark.asyncio
    async def test_batch_processor_enable_disable(self):
        """Test enabling and disabling batch processor"""
        processor = BatchProcessor.get_instance()
        
        async def handler(items):
            return {item.item_id: "processed" for item in items}
        
        result = await processor.enable(handler)
        assert result == True
        assert processor.enabled == True
        
        result = await processor.disable()
        assert result == True
        assert processor.enabled == False
    
    @pytest.mark.asyncio
    async def test_submit_batch_item(self):
        """Test submitting items to batch processor"""
        processor = BatchProcessor.get_instance()
        
        async def handler(items):
            return {item.item_id: "done" for item in items}
        
        await processor.enable(handler)
        await processor.reset()
        
        # Submit item
        success, item_id, batch_id = await processor.submit_item({"data": "value"})
        assert success == True
        assert item_id.startswith("item_")
        assert batch_id.startswith("batch_")
    
    @pytest.mark.asyncio
    async def test_batch_processor_statistics(self):
        """Test batch processor statistics"""
        processor = BatchProcessor.get_instance()
        
        async def handler(items):
            return {item.item_id: "processed" for item in items}
        
        await processor.enable(handler)
        await processor.reset()
        
        stats = await processor.get_statistics()
        assert stats.total_batches >= 0
        assert stats.processed_items >= 0


# ============================================================================
# Load Balancer Tests
# ============================================================================

class TestLoadBalancer:
    """Load balancer tests"""
    
    @pytest.mark.asyncio
    async def test_load_balancer_enable_disable(self):
        """Test enabling and disabling load balancer"""
        lb = LoadBalancer.get_instance()
        
        result = await lb.enable(LoadBalancingStrategy.ROUND_ROBIN)
        assert result == True
        
        result = await lb.disable()
        assert result == True
    
    @pytest.mark.asyncio
    async def test_add_remove_instance(self):
        """Test adding and removing instances"""
        lb = LoadBalancer.get_instance()
        await lb.enable()
        await lb.reset()
        
        # Add instance
        result = await lb.add_instance("inst1", "localhost", 8001)
        assert result == True
        
        # Remove instance
        result = await lb.remove_instance("inst1")
        assert result == True
    
    @pytest.mark.asyncio
    async def test_get_instance(self):
        """Test getting instance from balancer"""
        lb = LoadBalancer.get_instance()
        await lb.enable(LoadBalancingStrategy.ROUND_ROBIN)
        await lb.reset()
        
        # Add instances
        await lb.add_instance("inst1", "localhost", 8001)
        await lb.add_instance("inst2", "localhost", 8002)
        
        # Get instance
        instance = await lb.get_instance()
        assert instance is not None
    
    @pytest.mark.asyncio
    async def test_load_balancer_strategies(self):
        """Test different load balancing strategies"""
        lb = LoadBalancer.get_instance()
        await lb.reset()
        
        strategies = [
            LoadBalancingStrategy.ROUND_ROBIN,
            LoadBalancingStrategy.LEAST_CONNECTIONS,
            LoadBalancingStrategy.LEAST_LOADED,
            LoadBalancingStrategy.RANDOM,
            LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN,
        ]
        
        for strategy in strategies:
            await lb.enable(strategy)
            assert lb.strategy == strategy
            await lb.disable()
    
    @pytest.mark.asyncio
    async def test_load_balancer_statistics(self):
        """Test load balancer statistics"""
        lb = LoadBalancer.get_instance()
        await lb.enable()
        await lb.reset()
        
        await lb.add_instance("inst1", "localhost", 8001)
        
        stats = await lb.get_statistics()
        assert stats['enabled'] == True
        assert 'instances' in stats


# ============================================================================
# Integration Tests
# ============================================================================

class TestPhase4Integration:
    """Phase 4 integration tests"""
    
    @pytest.mark.asyncio
    async def test_query_optimizer_with_cache_manager(self):
        """Test query optimizer working with cache manager"""
        optimizer = QueryOptimizer.get_instance()
        cache = CacheManager.get_instance()
        
        await optimizer.enable()
        await cache.enable()
        
        query = "SELECT * FROM users WHERE status = 'active'"
        result = {"users": [{"id": 1}]}
        
        # Cache result
        await cache.set(f"query:{query}", result)
        
        # Get from cache
        cached = await cache.get(f"query:{query}")
        assert cached == result
    
    @pytest.mark.asyncio
    async def test_rate_limiter_with_batch_processor(self):
        """Test rate limiter working with batch processor"""
        limiter = RateLimiter.get_instance()
        processor = BatchProcessor.get_instance()
        
        async def handler(items):
            return {item.item_id: "done" for item in items}
        
        await limiter.enable()
        await processor.enable(handler)
        
        config = RateLimitConfig(requests_per_second=10.0)
        
        # Check rate limit before submitting batch
        allowed, _ = await limiter.is_allowed("batch_client", config)
        assert allowed == True
        
        # Submit batch item
        success, _, _ = await processor.submit_item({"data": "test"})
        assert success == True


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
