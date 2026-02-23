# Database Repositories Module

A clean, organized data access layer (DAO pattern) for managing all database operations in the Mirror Leech Telegram Bot.

## Quick Start

```python
from bot.helper.ext_utils.db_repositories import (
    initialize_repositories,
    get_repositories_manager
)

# Initialize (usually in bot startup)
db = ...  # MongoDB instance
repos_manager = initialize_repositories(db)

# Use repositories
repos = get_repositories_manager()
await repos.users.update_user(12345, {"name": "John"})
await repos.download_tasks.create_task(task_data)
```

## Repositories Included

| Repository | Purpose |
|------------|---------|
| `UserPreferencesRepository` | User settings and preferences |
| `DownloadTasksRepository` | Download task tracking |
| `RssRepository` | RSS feed subscriptions |
| `UsersRepository` | User account data |
| `VariablesRepository` | Global variables and config |
| `IndexedRepository` | Advanced search and indexing |
| `BulkOperationsRepository` | Batch operations |

## Key Features

- **Consistent Interface**: All repositories follow the same pattern
- **Error Handling**: Automatic error logging and sensible defaults
- **Async/Await**: Full async support using Motor
- **Database Availability Check**: Automatic DB status tracking
- **Clean Separation**: Different concerns in different repositories
- **Bulk Operations**: Efficient batch processing
- **Aggregation**: Support for MongoDB aggregation pipelines
- **Health Checks**: Monitor repository and database health

## Benefits Over Direct DB Access

```python
# ❌ Direct database access (old way)
result = await db.users[TgClient.ID].find_one({"_id": user_id})
# Scattered throughout code, inconsistent error handling

# ✅ Repository pattern (new way)
repos = get_repositories_manager()
user = await repos.users.get_user(user_id)
# Centralized, consistent, easier to test, maintain
```

## File Structure

```
db_repositories/
├── __init__.py                           # Base repository + imports
├── base_repository.py                    # Abstract base class
├── manager.py                            # Central manager
├── user_preferences_repository.py        # User settings
├── download_tasks_repository.py          # Download tracking
├── rss_repository.py                     # RSS management
├── users_repository.py                   # User data
├── variables_repository.py               # Global variables
├── indexed_repository.py                 # Search operations
├── bulk_operations_repository.py         # Batch operations
├── README.md                             # This file
└── REPOSITORIES_GUIDE.md                 # Detailed guide
```

## Common Operations

### Get Data
```python
repos = get_repositories_manager()

user = await repos.users.get_user(12345)
all_users = await repos.users.get_all_users()
```

### Update Data
```python
await repos.users.update_user(12345, {"name": "John"})
await repos.variables.update_variable("setting", "value")
```

### Delete Data
```python
await repos.users.delete_user(12345)
await repos.rss.delete_rss(12345)
```

### Search Data
```python
results = await repos.indexed.search("downloads", {"status": "completed"})
count = await repos.indexed.count_documents("downloads")
```

### Bulk Operations
```python
await repos.bulk.bulk_insert("users", documents)
await repos.bulk.bulk_update("users", updates)
```

## Error Handling

All methods return safe defaults on error:

```python
# Returns False on error
success = await repos.users.update_user(12345, data)

# Returns [] on error
results = await repos.indexed.search("table", {})

# Returns None on error
value = await repos.variables.get_variable("key")

# Errors are automatically logged to LOGGER
```

## Lifecycle

### Startup
```python
# In your bot's startup code
from bot.helper.ext_utils.db_repositories import initialize_repositories

db = ...  # MongoDB instance
repos_manager = initialize_repositories(db)
```

### Runtime
```python
# Access anywhere in your code
from bot.helper.ext_utils.db_repositories import get_repositories_manager

repos = get_repositories_manager()
await repos.users.get_user(12345)
```

### Shutdown
```python
# In your bot's shutdown code
from bot.helper.ext_utils.db_repositories import close_repositories

await close_repositories()
```

## Health Monitoring

```python
repos = get_repositories_manager()
health = await repos.health_check()

if health["database"] == "healthy":
    # Safe to perform operations
    pass
else:
    # Database is down, handle gracefully
    pass
```

## Database Connectivity

Each repository checks database availability:

```python
repo = repos.user_preferences

if repo.is_available:
    # Database is available
    await repo.update_preference(...)
else:
    # Database connection lost
    log_warning("Database temporarily unavailable")
```

## Testing

Mock the repositories for testing:

```python
from unittest.mock import AsyncMock

# Create mock repositories
mock_repos = MagicMock()
mock_repos.users.get_user = AsyncMock(return_value={"name": "Test"})

# Use in tests
user = await mock_repos.users.get_user(12345)
assert user["name"] == "Test"
```

## Integration with Bot

The repositories integrate seamlessly with the existing bot code:

```python
# In handlers or commands
async def handle_user_settings(user_id):
    repos = get_repositories_manager()
    
    # Get user preferences
    prefs = await repos.user_preferences.get_all_preferences(user_id)
    
    # Update preference
    await repos.user_preferences.update_preference(
        user_id, "theme", "dark"
    )
    
    # Check download tasks
    tasks = await repos.download_tasks.get_user_tasks(user_id)
    
    # Reduce boilerplate, consistent error handling
```

## Documentation

- **REPOSITORIES_GUIDE.md**: Complete API reference and examples
- **Base Repository**: See `base_repository.py` for base class
- **Manager**: See `manager.py` for central coordination

## Support

For issues or questions:
1. Check REPOSITORIES_GUIDE.md for detailed examples
2. Review the specific repository implementation
3. Check error logs (LOGGER output)
4. Check MongoDB connection and permissions

## Version

Compatible with:
- Python 3.8+
- Motor (async MongoDB driver)
- PyMongo 3.11+

## Related

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Motor Documentation](https://motor.readthedocs.io/)
- [Repository Pattern](https://en.wikipedia.org/wiki/Repository_pattern)
