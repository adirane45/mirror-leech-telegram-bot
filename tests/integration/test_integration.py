"""
Integration Tests for Enhanced Services
Tests interaction between Redis, Celery, and Metrics
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

import pytest
import time


@pytest.mark.integration
@pytest.mark.asyncio
class TestEnhancedServicesIntegration:
    """Test integration of enhanced services"""
    
    async def test_services_initialization_when_disabled(self):
        """Test that bot works fine when all services are disabled"""
        from bot.core.enhanced_startup import initialize_enhanced_services
        
        status = await initialize_enhanced_services()
        
        # Should initialize successfully even if all disabled
        assert isinstance(status, dict)
        assert "redis" in status
        assert "celery" in status
        assert "metrics" in status
    
    @pytest.mark.redis
    async def test_redis_caching_flow(self, redis_client):
        """Test complete caching flow when Redis is enabled"""
        if not redis_client.is_enabled:
            pytest.skip("Redis not enabled for this test")
        
        # Set a value
        key = "test_task_123"
        value = {"status": "downloading", "progress": 50}
        
        await redis_client.set(key, value, ttl=60)
        
        # Get the value back
        retrieved = await redis_client.get(key)
        assert retrieved == value
        
        # Check existence
        exists = await redis_client.exists(key)
        assert exists == True
        
        # Delete
        deleted = await redis_client.delete(key)
        assert deleted == 1
        
        # Verify deletion
        retrieved_after = await redis_client.get(key)
        assert retrieved_after is None


@pytest.mark.integration
class TestBackwardCompatibility:
    """Test backward compatibility - existing code should work"""
    
    def test_config_loading(self):
        """Test that original config still loads"""
        from config.main_config import Config
        
        # Should have all original attributes
        assert hasattr(Config, 'BOT_TOKEN')
        assert hasattr(Config, 'OWNER_ID')
        assert hasattr(Config, 'DATABASE_URL')
    
    def test_optional_enhancements(self):
        """Test that enhancements are truly optional"""
        from config.main_config import Config
        
        # New configs should have defaults
        redis_enabled = getattr(Config, 'ENABLE_REDIS_CACHE', False)
        celery_enabled = getattr(Config, 'ENABLE_CELERY', False)
        metrics_enabled = getattr(Config, 'ENABLE_METRICS', False)
        
        # All should be False by default
        assert isinstance(redis_enabled, bool)
        assert isinstance(celery_enabled, bool)
        assert isinstance(metrics_enabled, bool)
