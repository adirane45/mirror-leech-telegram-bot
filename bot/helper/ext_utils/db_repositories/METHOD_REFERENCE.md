# Database Repositories - Method Reference

This is a quick reference card for all available methods across all repositories.

## Quick Access

```python
from bot.helper.ext_utils.db_repositories import get_repositories_manager

repos = get_repositories_manager()
```

## Repository Methods Quick Reference

### UserPreferencesRepository
```python
# Sets/gets individual preferences
await repos.user_preferences.update_preference(user_id, key, value)
await repos.user_preferences.get_preference(user_id, key)
await repos.user_preferences.delete_preference(user_id, key)

# Bulk preference operations
await repos.user_preferences.get_all_preferences(user_id)           # All for one user
await repos.user_preferences.get_all_user_preferences()             # All from all users
await repos.user_preferences.delete_all_preferences(user_id)        # Delete all for user
await repos.user_preferences.clear_all_preferences()                # Clear entire collection
```

### DownloadTasksRepository
```python
# Task management
await repos.download_tasks.create_task(task_data)                   # Create new task
await repos.download_tasks.get_task(task_id)                        # Get by ID
await repos.download_tasks.delete_task(task_id)                     # Delete by ID
await repos.download_tasks.get_all_tasks()                          # Get all tasks
await repos.download_tasks.clear_all_tasks()                        # Delete all

# Task status and progress
await repos.download_tasks.update_task_status(task_id, status)      # Update status
await repos.download_tasks.update_task_progress(task_id, progress)  # Update progress (0-100)

# Query operations
await repos.download_tasks.get_user_tasks(user_id)                  # Get user's tasks
await repos.download_tasks.get_tasks_by_status(status)              # Get by status
await repos.download_tasks.delete_user_tasks(user_id)               # Delete user's tasks
```

### RssRepository
```python
# RSS management
await repos.rss.update_all_rss()                                     # Update all feeds
await repos.rss.update_rss(user_id)                                  # Update specific user's
await repos.rss.get_rss(user_id)                                     # Get user's RSS config
await repos.rss.get_all_rss()                                        # Get all RSS configs
await repos.rss.delete_rss(user_id)                                  # Delete user's RSS
await repos.rss.clear_all_rss()                                      # Delete all
```

### UsersRepository
```python
# User account management
await repos.users.update_user(user_id, user_data)                   # Create/update user
await repos.users.get_user(user_id)                                  # Get user data
await repos.users.delete_user(user_id)                               # Delete user
await repos.users.get_all_users()                                    # Get all users
await repos.users.clear_all_users()                                  # Delete all users

# Admin/permission management
await repos.users.is_sudo(user_id)                                   # Check if admin
await repos.users.set_sudo(user_id, is_sudo)                        # Set admin status
await repos.users.get_sudo_users()                                   # Get list of admins
```

### VariablesRepository
```python
# Variable storage
await repos.variables.update_variable(key, value)                    # Set variable
await repos.variables.update_variable(key, value, table="custom")    # Set in custom table
await repos.variables.get_variable(key)                              # Get variable
await repos.variables.get_variable(key, table="custom")              # Get from custom table
await repos.variables.delete_variable(key)                           # Delete variable
await repos.variables.delete_variable(key, table="custom")           # Delete from custom table

# Bulk operations
await repos.variables.update_multiple_variables(dict_of_vars)        # Batch update
await repos.variables.update_multiple_variables(dict, table="custom")# In custom table
await repos.variables.get_all_variables()                            # Get all variables
await repos.variables.get_all_variables(table="custom")              # Get from custom table
await repos.variables.clear_all_variables()                          # Delete all variables
await repos.variables.clear_all_variables(table="custom")            # Delete from custom table
```

### IndexedRepository
```python
# Index management
await repos.indexed.create_index(table, field)                       # Create index on field
await repos.indexed.create_index(table, field, DESCENDING)           # Descending order
await repos.indexed.create_compound_index(table, [(field1, 1), (field2, -1)])
await repos.indexed.drop_index(table, "index_name")                  # Drop by name
await repos.indexed.get_indexes(table)                               # List all indexes

# Search and filter
await repos.indexed.search(table, query)                             # Find documents
await repos.indexed.search(table, query, limit=100)                  # With limit
await repos.indexed.count_documents(table)                           # Count all
await repos.indexed.count_documents(table, query)                    # Count matching

# Advanced queries
await repos.indexed.distinct(table, field)                           # Get unique values
await repos.indexed.distinct(table, field, query)                    # Unique with filter
await repos.indexed.aggregate(table, pipeline)                       # Aggregation pipeline
```

### BulkOperationsRepository
```python
# Bulk insert
await repos.bulk.bulk_insert(table, documents_list)                  # Insert many

# Bulk update
await repos.bulk.bulk_update(table, [(filter, update), ...])        # Update many

# Bulk delete
await repos.bulk.bulk_delete(table, [filter1, filter2, ...])        # Delete many

# Bulk upsert
await repos.bulk.bulk_upsert(table, [(filter, data), ...])          # Insert or update

# Bulk replace
await repos.bulk.bulk_replace(table, [(filter, replacement), ...])  # Replace documents

# Mixed operations
await repos.bulk.bulk_mixed_operations(table, [ops_list])           # Various operations
```

## DatabaseRepositoriesManager

```python
# Access individual repositories
repos.user_preferences
repos.download_tasks
repos.rss
repos.users
repos.variables
repos.indexed
repos.bulk

# Health and status
await repos.health_check()                                           # Check all systems
repos.set_return(True)                                               # Disable temporarily
repos.set_return(False)                                              # Re-enable

# Lifecycle
# Initialize
from bot.helper.ext_utils.db_repositories import initialize_repositories
repos = initialize_repositories(db)

# Shutdown
from bot.helper.ext_utils.db_repositories import close_repositories
await close_repositories()
```

## Common Query Patterns

### MongoDB Query Syntax
```python
# In indexed repository search():
{
    "field": "value"                          # Equals
    "field": {"$gt": 100}                     # Greater than
    "field": {"$lt": 100}                     # Less than
    "field": {"$in": [1, 2, 3]}               # In list
    "status": {"$in": ["completed", "failed"]}
    "$and": [{}, {}]                          # AND condition
    "$or": [{}, {}]                           # OR condition
}
```

### Aggregation Pipeline Example
```python
pipeline = [
    {"$match": {"user_id": 12345}},           # Filter
    {"$group": {                              # Group
        "_id": "$status",
        "count": {"$sum": 1},
        "total": {"$sum": "$size"}
    }},
    {"$sort": {"count": -1}},                 # Sort
    {"$limit": 10}                            # Limit
]
results = await repos.indexed.aggregate("table", pipeline)
```

## Return Values

| Method Type | Success Return | Error Return |
|------------|----------------|-------------|
| Boolean operations | True | False |
| List operations | [results] | [] |
| Dict operations | {results} | {} |
| Count operations | integer | 0 |
| Single value | value | None |

## Error Handling Pattern

```python
success = await repos.users.update_user(user_id, data)
if success:
    # Proceed
    pass
else:
    # Handle error - already logged
    log_error("Failed to update user")
```

## Performance Tips

1. **Use Indexes**: Create indexes on frequently searched fields
   ```python
   await repos.indexed.create_index("downloads", "user_id")
   ```

2. **Use Bulk Operations**: For multiple updates
   ```python
   updates = [(filter, data) for filter, data in items]
   await repos.bulk.bulk_update("table", updates)
   ```

3. **Use Limit**: When searching
   ```python
   results = await repos.indexed.search("table", query, limit=100)
   ```

4. **Check Availability**: Before operations
   ```python
   if repos.users.is_available:
       await repos.users.get_user(user_id)
   ```

## Common Operations Cheat Sheet

```python
# Create/Register User
await repos.users.update_user(user_id, user_data)

# Get User Info
user = await repos.users.get_user(user_id)

# Set User Preference
await repos.user_preferences.update_preference(user_id, "theme", "dark")

# Get User Preference
theme = await repos.user_preferences.get_preference(user_id, "theme")

# Create Download Task
await repos.download_tasks.create_task({
    "_id": task_id,
    "user_id": user_id,
    "file_name": "file.mp4",
    "status": "downloading"
})

# Update Download Progress
await repos.download_tasks.update_task_progress(task_id, 50)

# Get User Downloads
tasks = await repos.download_tasks.get_user_tasks(user_id)

# Make User Admin
await repos.users.set_sudo(user_id, True)

# Get All Admins
admins = await repos.users.get_sudo_users()

# Set Configuration
await repos.variables.update_variable("max_bandwidth", 100)

# Get Configuration
max_bw = await repos.variables.get_variable("max_bandwidth")

# Search Database
results = await repos.indexed.search("downloads", query)

# Get Statistics
stats = await repos.indexed.aggregate("downloads", pipeline)
```

## Collections Used

- `users[TgClient.ID]` - User accounts
- `user_preferences[TgClient.ID]` - User settings
- `downloads[TgClient.ID]` - Download tasks
- `rss[TgClient.ID]` - RSS configurations
- `variables[TgClient.ID]` - Global variables
- Custom tables supported

## Database Availability

```python
# Check if repository is available
if repos.users.is_available:
    # Safe to use
    pass

# Check all systems
health = await repos.health_check()
if health["database"] == "healthy":
    # All systems operational
    pass
```

## Thread Safety

All repositories are async-safe and designed for concurrent use in async applications. Use `await` for all operations.

## Troubleshooting Reference

| Issue | Check |
|-------|-------|
| Method not found | See correct repository in this reference |
| Returns empty/false | Check database connection with health_check() |
| Database unavailable | Verify MongoDB is running |
| Timeout errors | Check network and MongoDB settings |
| Import errors | Verify initialize_repositories() was called |

## Full Method Signatures

See REPOSITORIES_GUIDE.md for complete method signatures with type hints and detailed documentation.

---

**Need more details?** Check REPOSITORIES_GUIDE.md for complete documentation.
**Want examples?** Check EXAMPLES.md for real-world usage.
**Understanding architecture?** Check INDEX.md for full overview.
