# Database Repositories Guide

This guide explains how to use the database repositories layer in the Mirror Leech Telegram Bot.

## Overview

The database repositories provide a clean, organized data access layer (DAO pattern) for all database operations. Each repository is responsible for a specific domain of data.

## Architecture

```
DatabaseRepositoriesManager (central manager)
├── UserPreferencesRepository (user settings)
├── DownloadTasksRepository (download tracking)
├── RssRepository (RSS subscriptions)
├── UsersRepository (user data)
├── VariablesRepository (global variables)
├── IndexedRepository (search operations)
└── BulkOperationsRepository (batch operations)
```

## Repository Types

### 1. UserPreferencesRepository

Manages user-specific preferences and settings.

```python
repos = get_repositories_manager()

# Update user preference
await repos.user_preferences.update_preference(
    user_id=12345,
    key="download_path",
    value="/home/user/downloads"
)

# Get specific preference
value = await repos.user_preferences.get_preference(12345, "download_path")

# Get all preferences for a user
prefs = await repos.user_preferences.get_all_preferences(12345)

# Delete a preference
await repos.user_preferences.delete_preference(12345, "download_path")
```

### 2. DownloadTasksRepository

Tracks and manages download tasks and their status.

```python
# Create new download task
task = {
    "_id": "task_123",
    "user_id": 12345,
    "file_name": "video.mp4",
    "size": 1024000,
    "status": "downloading",
    "progress": 45
}
await repos.download_tasks.create_task(task)

# Get task by ID
task = await repos.download_tasks.get_task("task_123")

# Update task status
await repos.download_tasks.update_task_status("task_123", "completed")

# Get tasks by user
user_tasks = await repos.download_tasks.get_user_tasks(12345)

# Get tasks by status
active_tasks = await repos.download_tasks.get_tasks_by_status("downloading")
```

### 3. RssRepository

Manages RSS feed subscriptions.

```python
# Update all RSS feeds
await repos.rss.update_all_rss()

# Get RSS for specific user
rss_config = await repos.rss.get_rss(12345)

# Get all RSS configurations
all_rss = await repos.rss.get_all_rss()

# Delete user's RSS
await repos.rss.delete_rss(12345)

# Clear all RSS data
await repos.rss.clear_all_rss()
```

### 4. UsersRepository

Manages user data and permissions.

```python
# Update user data
user = {
    "name": "John Doe",
    "email": "john@example.com",
    "is_sudo": False
}
await repos.users.update_user(12345, user)

# Check if user is sudo
is_admin = await repos.users.is_sudo(12345)

# Set sudo status
await repos.users.set_sudo(12345, True)

# Get all sudo users
admins = await repos.users.get_sudo_users()

# Get specific user
user = await repos.users.get_user(12345)

# Get all users
all_users = await repos.users.get_all_users()
```

### 5. VariablesRepository

Stores and manages global variables and configuration values.

```python
# Update single variable
await repos.variables.update_variable("max_bandwidth", 100)

# Get variable value
max_bw = await repos.variables.get_variable("max_bandwidth")

# Update multiple variables at once
vars_to_update = {
    "max_bandwidth": 100,
    "max_concurrent_downloads": 5,
    "announce_mode": "silent"
}
await repos.variables.update_multiple_variables(vars_to_update)

# Get all variables
all_vars = await repos.variables.get_all_variables()

# Use different table
await repos.variables.update_variable("setting1", "value1", table="custom_table")

# Delete variable
await repos.variables.delete_variable("max_bandwidth")
```

### 6. IndexedRepository

Performs advanced searching and indexing operations.

```python
# Create index for faster searches
await repos.indexed.create_index("downloads", "user_id")

# Create compound index
await repos.indexed.create_compound_index(
    "downloads",
    [("user_id", 1), ("status", 1)]
)

# Search documents
results = await repos.indexed.search(
    "downloads",
    {"user_id": 12345, "status": "completed"},
    limit=50
)

# Count documents
count = await repos.indexed.count_documents(
    "downloads",
    {"status": "completed"}
)

# Get distinct values
statuses = await repos.indexed.distinct("downloads", "status")

# Run aggregation pipeline
pipeline = [
    {"$match": {"user_id": 12345}},
    {"$group": {"_id": "$status", "count": {"$sum": 1}}}
]
results = await repos.indexed.aggregate("downloads", pipeline)

# Get indexes
indexes = await repos.indexed.get_indexes("downloads")

# Drop index
await repos.indexed.drop_index("downloads", "user_id_1")
```

### 7. BulkOperationsRepository

Handles batch operations for efficiency.

```python
# Bulk insert
documents = [
    {"user_id": 1, "name": "User1"},
    {"user_id": 2, "name": "User2"}
]
inserted = await repos.bulk.bulk_insert("users", documents)

# Bulk update
updates = [
    ({"user_id": 1}, {"name": "UpdatedUser1"}),
    ({"user_id": 2}, {"name": "UpdatedUser2"})
]
modified = await repos.bulk.bulk_update("users", updates)

# Bulk delete
filters = [
    {"user_id": 1},
    {"user_id": 2}
]
deleted = await repos.bulk.bulk_delete("users", filters)

# Bulk upsert
upserts = [
    ({"user_id": 1}, {"name": "User1", "active": True}),
    ({"user_id": 2}, {"name": "User2", "active": False})
]
upserted = await repos.bulk.bulk_upsert("users", upserts)

# Bulk replace
replacements = [
    ({"user_id": 1}, {"user_id": 1, "data": "new_data"}),
]
replaced = await repos.bulk.bulk_replace("users", replacements)
```

## Initialization and Cleanup

### Initialize Repositories

```python
from bot.helper.ext_utils.db_repositories import initialize_repositories, get_repositories_manager

# In your bot startup code:
db = ... # your MongoDB database instance
repos_manager = initialize_repositories(db)

# Later, access via:
repos = get_repositories_manager()
```

### Health Check

```python
repos = get_repositories_manager()
health = await repos.health_check()
print(health)
# Output:
# {
#     "manager": "healthy",
#     "database": "healthy",
#     "repositories": {
#         "user_preferences": "healthy",
#         "download_tasks": "healthy",
#         ...
#     }
# }
```

### Cleanup

```python
from bot.helper.ext_utils.db_repositories import close_repositories

# In your bot shutdown code:
await close_repositories()
```

## Error Handling

All repositories return default values on error:
- `bool` operations return `False`
- List operations return `[]`
- Dict operations return `{}`
- Single value operations return `None`

Errors are automatically logged.

```python
result = await repos.users.update_user(12345, user_data)
if not result:
    # Handle error (already logged)
    pass
```

## Database Availability

Repositories check database availability automatically:

```python
repo = repos.user_preferences
if repo.is_available:
    # Safe to use
    await repo.update_preference(...)
else:
    # Database is down
    print("Database unavailable")
```

## Best Practices

1. **Always use await**: All repository methods are async
2. **Check return values**: Verify success or failure
3. **Use bulk operations**: For multiple updates, use bulk methods
4. **Close properly**: Always call `close_repositories()` on shutdown
5. **Error handling**: Wrap operations in try-catch if needed
6. **Manager access**: Use `get_repositories_manager()` instead of creating new instances

## Common Patterns

### Conditional Update

```python
repos = get_repositories_manager()

# Only update if user exists
user = await repos.users.get_user(12345)
if user:
    user["last_activity"] = time.time()
    await repos.users.update_user(12345, user)
```

### Safe Get with Default

```python
repos = get_repositories_manager()

# Get or use default
value = await repos.variables.get_variable("setting") or "default_value"
```

### Batch Processing

```python
# Process many users efficiently
users = await repos.users.get_all_users()
for user_id, user_data in users.items():
    # Process user
    pass
```

## Adding New Repositories

To add a new repository:

1. Create `new_repository.py` extending `BaseDbRepository`
2. Implement required methods
3. Add to imports in `__init__.py`
4. Add to `DatabaseRepositoriesManager.__init__`
5. Add to manager's `health_check()` method

Example:

```python
# new_repository.py
class NewRepository(BaseDbRepository):
    async def custom_operation(self):
        if self._return:
            return None
        try:
            # implementation
            pass
        except PyMongoError as e:
            self._log_error("CUSTOM_OPERATION", e)
            return None
    
    async def close(self):
        pass
```

## Testing

When testing:

```python
from unittest.mock import AsyncMock, MagicMock
from bot.helper.ext_utils.db_repositories import get_repositories_manager

# Mock the database
mock_db = MagicMock()
repos = initialize_repositories(mock_db)

# Set return status to indicate DB failure for testing error handling
repos.set_return(True)  # Simulates DB unavailable

# Your test code
```

## See Also

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Motor Documentation](https://motor.readthedocs.io/)
- [Repository Pattern](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/infrastructure-persistence-layer-design)
