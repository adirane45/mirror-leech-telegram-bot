"""
Unit Tests for Redis Manager
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

import pytest
from bot.core.redis_manager import RedisManager


@pytest.mark.unit
@pytest.mark.asyncio
class TestRedisManager:
    """Test Redis Manager functionality"""
    
    async def test_initialization_disabled(self, redis_client):
        """Test Redis initialization when disabled"""
        assert redis_client.is_enabled == False
        assert redis_client._client is None
    
    async def test_get_returns_default_when_disabled(self, redis_client):
        """Test get() returns default when Redis is disabled"""
        result = await redis_client.get("test_key", default="default_value")
        assert result == "default_value"
    
    async def test_set_returns_false_when_disabled(self, redis_client):
        """Test set() returns False when Redis is disabled"""
        result = await redis_client.set("test_key", "test_value")
        assert result == False
    
    async def test_exists_returns_false_when_disabled(self, redis_client):
        """Test exists() returns False when Redis is disabled"""
        result = await redis_client.exists("test_key")
        assert result == False
    
    async def test_delete_returns_zero_when_disabled(self, redis_client):
        """Test delete() returns 0 when Redis is disabled"""
        result = await redis_client.delete("test_key")
        assert result == 0
    
    async def test_rate_limit_allows_when_disabled(self, redis_client):
        """Test rate limiting allows all when Redis is disabled"""
        allowed, remaining = await redis_client.check_rate_limit(
            user_id=12345,
            action="download",
            limit=10,
            window=60
        )
        assert allowed == True
        assert remaining == 10


@pytest.mark.unit
class TestRedisManagerSync:
    """Synchronous tests for Redis Manager"""
    
    def test_singleton_pattern(self):
        """Test that RedisManager follows singleton pattern"""
        client1 = RedisManager()
        client2 = RedisManager()
        assert client1 is client2
    
    def test_is_enabled_property(self, redis_client):
        """Test is_enabled property"""
        assert isinstance(redis_client.is_enabled, bool)
        assert redis_client.is_enabled == False
