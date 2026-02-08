# God Object Refactoring Guide

## Overview

"God Objects" are classes that know too much and do too much. They violate the Single Responsibility Principle and make the code harder to test, maintain, and extend.

**Identified God Objects**: 4 classes with 21-26 methods each

---

## Pattern 1: Repository Pattern for RedisManager

### Current Problem

`RedisManager` handles 21 different types of operations:
- Connection pooling
- Cache get/set/delete
- Session tokens
- User data
- Configuration caching

### Refactoring Approach: Repository Pattern

```python
# BEFORE: God Object
class RedisManager:
    async def get_cache(self, key): ...
    async def set_cache(self, key, value, ttl): ...
    async def delete_cache(self, key): ...
    async def get_session(self, user_id): ...
    async def set_session(self, user_id, data): ...
    async def delete_session(self, user_id): ...
    async def get_token(self, token_id): ...
    async def set_token(self, token_id, data): ...
    async def delete_token(self, token_id): ...
    async def get_config(self, key): ...
    async def set_config(self, key, value): ...
    # ... 10 more methods

# AFTER: Separated Repositories
class RedisConnectionManager:
    """Manages Redis connection pool"""
    async def connect(self): ...
    async def disconnect(self): ...
    async def ping(self): ...
    async def healthcheck(self): ...

class CacheRepository:
    """Handles cache-related operations"""
    async def get(self, key): ...
    async def set(self, key, value, ttl=3600): ...
    async def delete(self, key): ...
    async def increment(self, key): ...
    async def clear_pattern(self, pattern): ...

class SessionRepository:
    """Manages user sessions"""
    async def create(self, user_id): ...
    async def get(self, user_id): ...
    async def update(self, user_id, data): ...
    async def delete(self, user_id): ...
    async def expire(self, user_id): ...

class TokenRepository:
    """Manages authentication tokens"""
    async def store(self, token_id, data): ...
    async def retrieve(self, token_id): ...
    async def revoke(self, token_id): ...
    async def validate(self, token_id): ...

class ConfigRepository:
    """Manages configuration key-value pairs"""
    async def get(self, key): ...
    async def set(self, key, value): ...
    async def delete(self, key): ...
    async def get_all(self): ...
```

### Implementation Steps

**Step 1**: Create base repository interface
```python
# bot/core/repositories/base.py
from abc import ABC, abstractmethod
from typing import Any, Optional

class Repository(ABC):
    """Base repository interface for data access"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, **options) -> bool:
        pass
    
    @abstractmethod  
    async def delete(self, key: str) -> bool:
        pass
```

**Step 2**: Extract first repository (CacheRepository)
```python
# bot/core/repositories/cache_repository.py
from .base import Repository
from ..redis_manager import redis_client

class CacheRepository(Repository):
    async def get(self, key: str):
        """Retrieve value from cache"""
        return await redis_client.get(key)
    
    async def set(self, key: str, value, ttl: int = 3600):
        """Store value in cache with TTL"""
        return await redis_client.setex(key, ttl, value)
    
    async def delete(self, key: str):
        """Delete cache entry"""
        return await redis_client.delete(key)
```

**Step 3**: Update dependent code
```python
# BEFORE
redis_manager = RedisManager()
value = await redis_manager.get_cache("user:settings")

# AFTER
cache_repo = CacheRepository()
value = await cache_repo.get("user:settings")
```

**Step 4**: Add backward compatibility layer (optional, during transition)
```python
class RedisManager:
    """Backward-compatible wrapper during transition"""
    def __init__(self):
        self.cache = CacheRepository()
        self.sessions = SessionRepository()
        self.tokens = TokenRepository()
        self.config = ConfigRepository()
    
    # Legacy methods delegate to new repositories
    async def get_cache(self, key):
        return await self.cache.get(key)
    
    async def set_cache(self, key, value, ttl):
        return await self.cache.set(key, value, ttl)
```

**Step 5**: Migrate callers incrementally
```python
# Phase 1: Add deprecation warnings
async def get_cache(self, key):
    warnings.warn(
        "Use cache_repo.get() instead",
        DeprecationWarning
    )
    return await self.cache.get(key)

# Phase 2: Remove deprecated methods after migration complete
```

### Testing the Refactored Code

```python
# tests/test_cache_repository.py
import pytest
from bot.core.repositories import CacheRepository
from unittest.mock import AsyncMock, patch

@pytest.fixture
async def cache_repo():
    return CacheRepository()

@pytest.mark.asyncio
async def test_cache_get(cache_repo):
    with patch('bot.core.redis_client.get') as mock_get:
        mock_get.return_value = "test_value"
        result = await cache_repo.get("test_key")
        assert result == "test_value"
        mock_get.assert_called_once_with("test_key")

@pytest.mark.asyncio
async def test_cache_set_with_ttl(cache_repo):
    with patch('bot.core.redis_client.setex') as mock_set:
        mock_set.return_value = True
        result = await cache_repo.set("key", "value", 3600)
        assert result is True
        mock_set.assert_called_once_with("key", 3600, "value")

@pytest.mark.asyncio
async def test_cache_delete(cache_repo):
    with patch('bot.core.redis_client.delete') as mock_del:
        mock_del.return_value = 1
        result = await cache_repo.delete("key")
        assert result == 1
        mock_del.assert_called_once_with("key")
```

---

## Pattern 2: Domain-Driven Repository Pattern for DbManager

### Current Problem

`DbManager` mixes different concerns:
- User data access
- Activity logging
- Configuration storage
- Token management

### Refactoring Approach

```python
# Directory structure
bot/core/repositories/
├── __init__.py
├── base.py
├── user_repository.py
├── log_repository.py
├── config_repository.py
└── token_repository.py
```

### Implementation

```python
# bot/core/repositories/user_repository.py
class UserRepository:
    """Manages user data in database"""
    
    async def get_user(self, user_id: int):
        """Retrieve user by ID"""
        pass
    
    async def create_user(self, user_data: dict):
        """Create new user"""
        pass
    
    async def update_user(self, user_id: int, updates: dict):
        """Update user information"""
        pass
    
    async def delete_user(self, user_id: int):
        """Delete user and associated data"""
        pass
    
    async def list_users(self, skip: int = 0, limit: int = 100):
        """List users with pagination"""
        pass
    
    async def get_user_stats(self, user_id: int):
        """Get user statistics"""
        pass
    
    async def is_user_active(self, user_id: int) -> bool:
        """Check if user is active"""
        pass
    
    async def grant_permission(self, user_id: int, permission: str):
        """Grant permission to user"""
        pass
```

### Benefits of This Refactoring

1. **Single Responsibility**: Each class does one thing
2. **Testability**: Easy to mock and test repositories independently
3. **Reusability**: Repositories can be used by multiple services
4. **Maintainability**: Clear boundaries make code easier to understand
5. **Scalability**: Easy to swap implementations (e.g., Redis cache layer)

### Dependency Injection Example

```python
# bot/core/services/user_service.py
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def get_user_profile(self, user_id: int):
        user = await self.user_repo.get_user(user_id)
        stats = await self.user_repo.get_user_stats(user_id)
        return {
            "user": user,
            "stats": stats
        }

# main.py
user_repo = UserRepository()
user_service = UserService(user_repo)
profile = await user_service.get_user_profile(12345)
```

---

## Pattern 3: Service Locator Pattern for JobFunctions

### Current Problem

`JobFunctions` in sabnzbdapi mixes job operations with querying logic.

### Refactoring Approach

Create specialized job managers:

```python
# integrations/sabnzbdapi/managers/
├── job_status_manager.py     # Status queries
├── job_history_manager.py    # Historical data
├── job_queue_manager.py      # Queue operations
└── job_config_manager.py     # Configuration
```

### Example Implementation

```python
# integrations/sabnzbdapi/managers/job_status_manager.py
class JobStatusManager:
    """Manages job status queries and updates"""
    
    def __init__(self, api_client: SABnzbdAPIClient):
        self.api = api_client
    
    async def get_job_status(self, job_id: str):
        """Get current job status"""
        pass
    
    async def get_all_jobs(self):
        """Retrieve all active jobs"""
        pass
    
    async def get_job_details(self, job_id: str):
        """Get detailed job information"""
        pass
    
    async def is_job_running(self, job_id: str) -> bool:
        """Check if job is currently running"""
        pass
    
    async def get_job_progress(self, job_id: str) -> float:
        """Get job completion percentage"""
        pass
```

---

## Checklist for God Object Refactoring

- [ ] **Analyze**: Map all methods and group by responsibility
- [ ] **Design**: Create new class structure using repository/service pattern
- [ ] **Create**: Implement new focused classes
- [ ] **Test**: Write unit tests for each new class  
- [ ] **Migrate**: Update all call sites to use new classes
- [ ] **Deprecate**: Add deprecation warnings to old methods
- [ ] **Remove**: Delete old class after transition period
- [ ] **Document**: Update API documentation
- [ ] **Verify**: Run CodeScene analysis again to confirm improvement

---

## Tools & Commands

```bash
# Run CodeScene analysis
bash scripts/codescene_analyze.sh full

# Check for remaining god objects
python3 scripts/analyze_complexity.py | grep "God object"

# Run tests after refactoring
pytest tests/ -v --cov=bot/core/repositories

# Generate coverage report
pytest tests/ --cov=bot/core --cov-report=html
```

---

## Expected Outcome

After refactoring:
- ✅ RedisManager reduced from 21 to 4-5 focused classes
- ✅ DbManager reduced from 22 to 4-5 repository classes
- ✅ Each class has single responsibility
- ✅ Code coverage increases
- ✅ Technical debt decreases by ~32 hours
- ✅ Maintenance effort reduces significantly
