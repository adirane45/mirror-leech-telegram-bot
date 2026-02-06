"""
Phase 4: Integration Tests
Comprehensive tests for all Phase 4 components
"""

import pytest
import asyncio
from typing import Any, Dict, List
import logging
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'integrations'))

from bot.core.query_optimizer import QueryOptimizer, QueryType, OptimizationResult
from bot.core.cache_manager import CacheManager
from bot.core.connection_pool_manager import ConnectionPoolManager, BackendType
from bot.core.rate_limiter import RateLimiter, RateLimitConfig
from bot.core.batch_processor import BatchProcessor
from bot.core.load_balancer import LoadBalancer, LoadBalancingStrategy
from bot.core.enhanced_startup_phase4 import (
    initialize_phase4_services, 
    shutdown_phase4_services,
    get_phase4_status,
    reset_phase4_services
)

logger = logging.getLogger(__name__)


class TestQueryOptimizer:
    """Test QueryOptimizer component"""
    
    @pytest.mark.asyncio
    async def test_query_optimizer_initialization(self):
        """Test QueryOptimizer can be enabled"""
        optimizer = QueryOptimizer.get_instance()
        assert await optimizer.enable()
        assert optimizer.enabled
        await optimizer.disable()

    @pytest.mark.asyncio
    async def test_query_analysis(self):
        """Test query analysis functionality"""
        optimizer = QueryOptimizer.get_instance()
        await optimizer.enable()
        
        query = "SELECT * FROM users WHERE status = 'active'"
        result = await optimizer.analyze_query(query)
        
        assert result.query == query
        assert result.query_type == QueryType.SELECT
        assert result.cache_suggestion
        assert len(result.recommendations) > 0
        
        await optimizer.disable()

    @pytest.mark.asyncio
    async def test_query_caching(self):
        """Test query result caching"""
        optimizer = QueryOptimizer.get_instance()
        await optimizer.enable()
        
        query = "SELECT * FROM users"
        result_data = {"users": [{"id": 1, "name": "test"}]}
        
        # Cache result
        assert await optimizer.cache_query_result(query, result_data, ttl=300)
        
        # Retrieve from cache
        cached = await optimizer.get_cached_result(query)
        assert cached == result_data
        
        await optimizer.disable()

    @pytest.mark.asyncio
    async def test_query_statistics(self):
        """Test query statistics tracking"""
        optimizer = QueryOptimizer.get_instance()
        await optimizer.enable()
        
        query = "SELECT * FROM users"
        
        # Record execution
        await optimizer.record_execution(query, execution_time_ms=100, result_count=5)
        await optimizer.record_execution(query, execution_time_ms=120, result_count=5)
        
        # Get statistics
        stats = await optimizer.get_statistics()
        assert stats['enabled']
        assert stats['total_executions'] > 0
        assert stats['total_unique_queries'] > 0
        
        await optimizer.disable()


class TestCacheManager:
    """Test CacheManager component"""
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self):
        """Test CacheManager initialization"""
        cache = CacheManager.get_instance()
        assert await cache.enable(max_size_mb=100)
        assert cache.enabled
        await cache.disable()

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Test cache set and get operations"""
        cache = CacheManager.get_instance()
        await cache.enable()
        
        # Set value
        assert await cache.set("test_key", {"value": "test"}, ttl=300)
        
        # Get value
        value = await cache.get("test_key")
        assert value == {"value": "test"}
        
        await cache.disable()

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache entry expiration"""
        cache = CacheManager.get_instance()
        await cache.enable()
        
        # Set with very short TTL
        await cache.set("expire_test", "value", ttl=1)
        
        # Should exist immediately
        assert await cache.get("expire_test") == "value"
        
        # Wait for expiration
        await asyncio.sleep(1.1)
        
        # Should be expired
        assert await cache.get("expire_test") is None
        
        await cache.disable()

    @pytest.mark.asyncio
    async def test_cache_invalidation_pattern(self):
        """Test pattern-based cache invalidation"""
        cache = CacheManager.get_instance()
        await cache.enable()
        
        # Add entries
        await cache.set("user:1", {"id": 1})
        await cache.set("user:2", {"id": 2})
        await cache.set("post:1", {"id": 1})
        
        # Invalidate user:* pattern
        count = await cache.invalidate_pattern("user:*")
        
        assert count == 2
        assert await cache.get("user:1") is None
        assert await cache.get("post:1") is not None
        
        await cache.disable()


class TestConnectionPoolManager:
    """Test ConnectionPoolManager component"""
    
    @pytest.mark.asyncio
    async def test_pool_manager_initialization(self):
        """Test ConnectionPoolManager initialization"""
        manager = ConnectionPoolManager.get_instance()
        assert await manager.enable()
        assert manager.enabled
        await manager.disable()

    @pytest.mark.asyncio
    async def test_create_pool(self):
        """Test pool creation"""
        manager = ConnectionPoolManager.get_instance()
        await manager.enable()
        
        assert await manager.create_pool("test_pool", "mongodb", min_size=2, max_size=5)
        
        await manager.disable()

    @pytest.mark.asyncio
    async def test_acquire_release_connection(self):
        """Test connection acquisition and release"""
        manager = ConnectionPoolManager.get_instance()
        await manager.enable()
        
        await manager.create_pool("test_pool", "mongodb", min_size=2, max_size=5)
        
        # Acquire
        conn = await manager.acquire_connection("test_pool", timeout=5)
        assert conn is not None
        assert conn.is_healthy
        
        # Release
        assert await manager.release_connection("test_pool", conn)
        
        await manager.disable()


class TestRateLimiter:
    """Test RateLimiter component"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization"""
        limiter = RateLimiter.get_instance()
        assert await limiter.enable()
        assert limiter.enabled
        await limiter.disable()

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test basic rate limiting"""
        limiter = RateLimiter.get_instance()
        await limiter.enable()
        
        config = RateLimitConfig(requests_per_second=1.0, burst_size=2)
        
        # First requests should succeed (burst)
        allowed1, _ = await limiter.is_allowed("client1", config)
        assert allowed1
        
        allowed2, _ = await limiter.is_allowed("client1", config)
        assert allowed2
        
        # Third should be blocked
        allowed3, status = await limiter.is_allowed("client1", config)
        assert not allowed3
        assert status.retry_after > 0
        
        await limiter.disable()

    @pytest.mark.asyncio
    async def test_rate_limit_tier_config(self):
        """Test tier-specific rate limiting"""
        limiter = RateLimiter.get_instance()
        await limiter.enable()
        
        # Set tier limit
        tier_limit = RateLimitConfig(requests_per_second=2.0, burst_size=5)
        assert limiter.set_tier_limit("premium", tier_limit)
        
        await limiter.disable()


class TestBatchProcessor:
    """Test BatchProcessor component"""
    
    @pytest.mark.asyncio
    async def test_batch_processor_initialization(self):
        """Test BatchProcessor initialization"""
        processor = BatchProcessor.get_instance()
        
        async def dummy_handler(items):
            return {"processed": len(items)}
        
        assert await processor.enable(dummy_handler, max_batch_size=10)
        assert processor.enabled
        await processor.disable()

    @pytest.mark.asyncio
    async def test_submit_item(self):
        """Test submitting items to batch processor"""
        processor = BatchProcessor.get_instance()
        
        async def dummy_handler(items):
            return {"processed": len(items)}
        
        await processor.enable(dummy_handler)
        
        # Submit item
        success, item_id, batch_id = await processor.submit_item({"data": "test"})
        assert success
        assert item_id
        
        await processor.disable()

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing with handler"""
        processor = BatchProcessor.get_instance()
        
        items_processed = []
        
        async def test_handler(items):
            items_processed.extend(items)
            return {"count": len(items)}
        
        await processor.enable(test_handler, max_batch_size=2, batch_timeout=0.5)
        
        # Submit items
        for i in range(3):
            await processor.submit_item({"value": i})
        
        # Wait for processing
        await asyncio.sleep(1)
        
        await processor.disable()


class TestLoadBalancer:
    """Test LoadBalancer component"""
    
    @pytest.mark.asyncio
    async def test_load_balancer_initialization(self):
        """Test LoadBalancer initialization"""
        lb = LoadBalancer.get_instance()
        assert await lb.enable(LoadBalancingStrategy.ROUND_ROBIN)
        assert lb.enabled
        await lb.disable()

    @pytest.mark.asyncio
    async def test_add_instances(self):
        """Test adding instances to load balancer"""
        lb = LoadBalancer.get_instance()
        await lb.enable()
        
        assert await lb.add_instance("bot-1", "localhost", 8001, weight=1.0)
        assert await lb.add_instance("bot-2", "localhost", 8002, weight=1.0)
        
        assert len(lb.instances) == 2
        
        await lb.disable()

    @pytest.mark.asyncio
    async def test_instance_selection(self):
        """Test instance selection strategies"""
        lb = LoadBalancer.get_instance()
        await lb.enable(LoadBalancingStrategy.ROUND_ROBIN)
        
        await lb.add_instance("bot-1", "localhost", 8001)
        await lb.add_instance("bot-2", "localhost", 8002)
        
        # Should cycle through instances
        instance1 = lb._select_next_instance()
        instance2 = lb._select_next_instance()
        
        assert instance1 and instance2
        
        await lb.disable()


class TestPhase4Integration:
    """Integration tests for all Phase 4 components"""
    
    @pytest.mark.asyncio
    async def test_phase4_initialization(self):
        """Test complete Phase 4 initialization"""
        config = {
            'ENABLE_QUERY_OPTIMIZER': True,
            'ENABLE_RATE_LIMITER': True,
        }
        
        status = await initialize_phase4_services(config)
        
        assert status['success']
        assert 'QueryOptimizer' in status['services_initialized']
        assert 'RateLimiter' in status['services_initialized']
        
        # Cleanup
        await shutdown_phase4_services()

    @pytest.mark.asyncio
    async def test_phase4_status(self):
        """Test getting Phase 4 status"""
        # Initialize with minimal config
        await initialize_phase4_services({
            'ENABLE_QUERY_OPTIMIZER': True,
            'ENABLE_RATE_LIMITER': True,
        })
        
        # Get status
        status = await get_phase4_status()
        
        assert 'timestamp' in status
        assert 'services' in status
        
        # Cleanup
        await shutdown_phase4_services()

    @pytest.mark.asyncio
    async def test_phase4_shutdown(self):
        """Test Phase 4 graceful shutdown"""
        # Initialize
        await initialize_phase4_services({
            'ENABLE_QUERY_OPTIMIZER': True,
            'ENABLE_RATE_LIMITER': True,
        })
        
        # Shutdown
        assert await shutdown_phase4_services()

    @pytest.mark.asyncio
    async def test_phase4_reset(self):
        """Test resetting Phase 4 services"""
        await initialize_phase4_services({
            'ENABLE_QUERY_OPTIMIZER': True,
        })
        
        # Reset
        assert await reset_phase4_services()
        
        await shutdown_phase4_services()


# Load testing class (optional)
class TestPhase4Performance:
    """Performance tests for Phase 4 components"""
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test cache hit rate under load"""
        cache = CacheManager.get_instance()
        await cache.enable()
        
        # Fill cache
        for i in range(100):
            await cache.set(f"key_{i}", f"value_{i}")
        
        # Test hits
        hits = 0
        for i in range(100):
            result = await cache.get(f"key_{i}")
            if result:
                hits += 1
        
        assert hits == 100
        
        stats = await cache.get_statistics()
        assert stats['l1_hit_rate_percent'] > 0
        
        await cache.disable()

    @pytest.mark.asyncio
    async def test_rate_limiter_throughput(self):
        """Test rate limiter throughput"""
        limiter = RateLimiter.get_instance()
        await limiter.enable()
        
        config = RateLimitConfig(requests_per_second=100.0, burst_size=100)
        
        allowed_count = 0
        for _ in range(100):
            allowed, _ = await limiter.is_allowed("perf_test", config)
            if allowed:
                allowed_count += 1
        
        assert allowed_count > 90  # Should allow most requests
        
        await limiter.disable()


@pytest.fixture(autouse=True)
def cleanup_phase4():
    """Cleanup Phase 4 services between tests"""
    yield
    # Run cleanup in event loop if needed
    try:
        from bot.core.query_optimizer import QueryOptimizer
        from bot.core.cache_manager import CacheManager
        from bot.core.connection_pool_manager import ConnectionPoolManager
        from bot.core.rate_limiter import RateLimiter
        from bot.core.batch_processor import BatchProcessor
        from bot.core.load_balancer import LoadBalancer
        
        # Disable all services
        loop = asyncio.get_event_loop()
        
        for service_class in [QueryOptimizer, CacheManager, ConnectionPoolManager, 
                             RateLimiter, BatchProcessor, LoadBalancer]:
            instance = service_class.get_instance()
            if instance.enabled:
                try:
                    loop.run_until_complete(instance.disable())
                except:
                    pass
    except:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
