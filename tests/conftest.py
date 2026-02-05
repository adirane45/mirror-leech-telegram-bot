"""
Test Suite Configuration
Foundation for comprehensive testing
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

import pytest
import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    class MockConfig:
        ENABLE_REDIS_CACHE = False
        ENABLE_CELERY = False
        ENABLE_METRICS = False
        BOT_TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        OWNER_ID = 12345678
        DATABASE_URL = ""
    
    return MockConfig


@pytest.fixture
async def redis_client():
    """Mock Redis client for testing"""
    from bot.core.redis_manager import RedisManager
    
    client = RedisManager()
    # Don't actually connect in tests
    client._enabled = False
    
    yield client
    
    if client._client:
        await client.close()


@pytest.fixture
def metrics_collector():
    """Mock metrics collector for testing"""
    from bot.core.metrics import MetricsCollector
    
    collector = MetricsCollector()
    collector._enabled = False
    
    return collector


# Test marks 
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "redis: Tests requiring Redis"
    )
    config.addinivalue_line(
        "markers", "celery: Tests requiring Celery"
    )
