"""
Test Suite Configuration
Foundation for comprehensive testing
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

import sys
from pathlib import Path

import pytest

# Add project root, src, config, and integrations directories to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'integrations'))


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
async def redis_client(request):
    """Mock Redis client for testing"""
    from typing import Any, Optional

    from bot.core.redis_manager import RedisManager

    client = RedisManager()

    class _InMemoryCache:
        def __init__(self):
            self._store = {}

        async def get(self, key: str, default: Any = None) -> Optional[Any]:
            return self._store.get(key, default)

        async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
            self._store[key] = value
            return True

        async def delete(self, *keys: str) -> int:
            deleted = 0
            for key in keys:
                if key in self._store:
                    del self._store[key]
                    deleted += 1
            return deleted

        async def exists(self, key: str) -> bool:
            return key in self._store

        async def close(self):
            self._store.clear()

    if request.node.get_closest_marker("redis"):
        # Enable in-memory cache for redis-marked tests
        client._client = object()
        client._enabled = True
        client._cache = _InMemoryCache()
    else:
        # Default to disabled for non-redis tests
        client._client = None
        client._enabled = False
        client._cache = None

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


# Configure pytest and register markers
def pytest_configure(config):
    """Configure pytest"""
    config.option.asyncio_mode = "auto"
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "redis: Tests requiring Redis")
    config.addinivalue_line("markers", "celery: Tests requiring Celery")
    config.addinivalue_line("markers", "benchmark: Performance benchmark tests")
