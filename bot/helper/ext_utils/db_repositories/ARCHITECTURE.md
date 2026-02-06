# Database Repositories - Architecture & Design

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│             Application Layer (Handlers, Commands)          │
│                                                              │
│  - Telegram message handlers                               │
│  - Admin commands                                           │
│  - Download management commands                            │
│  - Configuration commands                                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                    get_repositories_manager()
                            │
┌───────────────────────────▼─────────────────────────────────┐
│         DatabaseRepositoriesManager (Central Manager)       │
│                                                              │
│   - Coordinates all repositories                           │
│   - Handles initialization                                 │
│   - Provides health checking                               │
│   - Manages lifecycle                                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ User Data Layer  │ │Download Data Lay │ │Config Data Layer │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ UsersRepository  │ │DownloadTasks     │ │VariablesRep      │
│ UserPreferences  │ │RssRepository     │ │IndexedRepository │
│ Permissions      │ │Progress tracking │ │BulkOperations    │
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                    BaseDbRepository (Abstract Base)
                    - Error handling
                    - Logging
                    - DB checking
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌──────────────────────────┐            ┌──────────────────────┐
│    MongoDB Collections   │            │  Motor Async Driver  │
│                          │            │                      │
│  - users[ID]            │            │  - Connection Pool   │
│  - user_preferences[ID] │            │  - Async Operations  │
│  - downloads[ID]        │            │  - Error Handling    │
│  - rss[ID]              │            │                      │
│  - variables[ID]        │            │                      │
└──────────────┬───────────┘            └──────────────────────┘
               │
               ▼
        ┌─────────────┐
        │  MongoDB    │
        │  Database   │
        └─────────────┘
```

## Data Flow

### Write Operation Example
```
Handler
  │
  ├─► get_repositories_manager()
  │
  ├─► repos.users.update_user(user_id, data)
  │
  ├─► UserRepository.update_user()
  │        │
  │        ├─► Check: self._return (DB available?)
  │        │
  │        ├─► Try: database operation
  │        │      await db.users[ID].replace_one()
  │        │
  │        ├─► Return: boolean
  │        │
  │        └─► Catch: Log error, return False
  │
  └─► Use result for response
```

### Read Operation Example
```
Handler
  │
  ├─► repos.users.get_user(user_id)
  │
  ├─► UserRepository.get_user()
  │        │
  │        ├─► Check: DB available
  │        │
  │        ├─► Try: await db.users[ID].find_one()
  │        │
  │        ├─► Return: dict with user data
  │        │        or {} if not found
  │        │
  │        └─► Catch: Log error, return {}
  │
  └─► Use returned data
```

## Repository Relationships

```
UserPreferencesRepository
├─ Stores: user-specific settings
├─ Key: user_id
└─ Used for: personalization

DownloadTasksRepository
├─ Stores: active/completed downloads
├─ Key: task_id
├─ Related to: UserRepository (user_id field)
└─ Used for: tracking

RssRepository
├─ Stores: RSS subscriptions
├─ Key: user_id
├─ Related to: UserRepository
└─ Used for: feed management

UsersRepository
├─ Stores: user accounts
├─ Key: user_id (Telegram ID)
├─ Related to: UserPreferencesRepository
├─ Related to: DownloadTasksRepository
├─ Related to: RssRepository
└─ Used for: auth/permissions

VariablesRepository
├─ Stores: global config
├─ Key: variable name
├─ Supports: multiple tables
└─ Used for: system configuration

IndexedRepository
├─ Provides: search/query interface
├─ Works with: any table
├─ Supports: indexes, aggregation
└─ Used for: analytics

BulkOperationsRepository
├─ Provides: batch operations
├─ Works with: any repository operations
├─ Optimizes: multi-document changes
└─ Used for: performance
```

## Initialization Sequence

```
1. Application Startup
   │
2. Create MongoDB connection
   │
3. Call initialize_repositories(db)
   │
   ├─► Create DatabaseRepositoriesManager
   │
   ├─► Initialize all repositories:
   │   ├─ UserPreferencesRepository(db)
   │   ├─ DownloadTasksRepository(db)
   │   ├─ RssRepository(db)
   │   ├─ UsersRepository(db)
   │   ├─ VariablesRepository(db)
   │   ├─ IndexedRepository(db)
   │   └─ BulkOperationsRepository(db)
   │
   ├─► Perform health_check()
   │
   └─► Store as global instance
   │
4. get_repositories_manager() available throughout app
   │
5. Application running (can use repositories)
   │
6. Shutdown received
   │
7. Call close_repositories()
   │
   ├─► Close all repositories
   ├─► Clean up resources
   └─► Disconnect from database
   │
8. Application exits
```

## Error Handling Flow

```
Repository Method Called
   │
   ├─► Check: self._return (DB available?)
   │
   ├─► IF DB unavailable:
   │   └─► Return safe default (False, [], {}, None)
   │
   ├─► TRY: Execute database operation
   │   │
   │   └─► Use Motor async operation
   │
   ├─► CATCH: PyMongoError
   │   │
   │   ├─► Log error via self._log_error()
   │   │
   │   └─► Return safe default
   │
   └─► Always return (no exceptions leak out)
```

## Database Schema

### Users Collection
```json
{
    "_id": 12345,           // Telegram user ID
    "name": "John",
    "email": "john@example.com",
    "is_sudo": false,
    "created_at": 1234567890,
    "custom_field": "value"
}
```

### User Preferences Collection
```json
{
    "_id": 12345,           // User ID
    "theme": "dark",
    "download_path": "/downloads",
    "notification_mode": "silent",
    "max_downloads": 5
}
```

### Downloads Collection
```json
{
    "_id": "task_uuid",
    "user_id": 12345,
    "file_name": "video.mp4",
    "size": 1024000,
    "url": "https://...",
    "status": "downloading",   // pending, downloading, completed, failed
    "progress": 45,            // 0-100
    "created_at": 1234567890,
    "started_at": 1234567891,
    "completed_at": null
}
```

### RSS Collection
```json
{
    "_id": 12345,           // User ID
    "feeds": [
        {
            "url": "https://example.com/feed",
            "added_at": 1234567890,
            "enabled": true
        }
    ]
}
```

### Variables Collection
```json
{
    "_id": "max_bandwidth",
    "value": 100
}
```

## Design Patterns Used

### 1. Repository Pattern
```
Business Logic
    ↓
Repository Interface (abstract methods)
    ↓
Repository Implementation (specific logic)
    ↓
Data Source (MongoDB)
```

**Benefits**:
- Abstracts data source
- Centralizes data access
- Easy to test (mock repository)
- Easy to change database

### 2. Manager Pattern
```
Multiple Repositories
    ↓
Manager (coordinates)
    ↓
Single Interface
    ↓
Client Code
```

**Benefits**:
- Single entry point
- Centralized lifecycle management
- Simplified client code

### 3. Async/Await Pattern
```
async def operation():
    result = await non_blocking_io()
    return result
```

**Benefits**:
- Non-blocking I/O
- Better concurrency
- Responsive application

### 4. Error Handling Pattern
```
try:
    result = database_operation()
except DatabaseError:
    log_error()
    return safe_default()
```

**Benefits**:
- Consistent error handling
- Automatic logging
- No exception propagation

### 5. Factory Pattern
```
initialize_repositories(db)  # Creates instance
    ↓
get_repositories_manager()   # Retrieves singleton
    ↓
close_repositories()         # Cleans up
```

**Benefits**:
- Controlled instantiation
- Singleton pattern
- Lifecycle management

## Method Resolution Order

When calling a method:

```
repos.users.update_user(user_id, data)
   │
   └─► UserRepository (specific)
       │
       └─► BaseDbRepository (abstract base)
           │
           └─► Database operation
               │
               └─► MongoDB
```

## Performance Characteristics

### Single Operations
```
Time: ~1-2ms per operation
Network: 1 database call
Optimization: Best for individual records
```

### Bulk Operations
```
Time: ~5-10ms for 100 items (vs 100-200ms individual)
Network: 1 database call
Optimization: 10-20x faster than individual ops
```

### Indexed Queries
```
Without index: ~100ms (full collection scan)
With index:    ~1-2ms (index lookup)
Savings:       50-100x faster
```

### Aggregation Pipeline
```
Simple aggregation: ~2-5ms
Complex pipeline:   ~5-20ms
Network: 1 database call (all processing on server)
```

## Security Considerations

### 1. User ID Isolation
```python
# Each user can only access their own data
user_prefs = await repos.user_preferences.get_all_preferences(user_id)
# Returns only this user's preferences
```

### 2. Admin Checks
```python
is_admin = await repos.users.is_sudo(user_id)
if is_admin:
    # Only admins can perform this action
```

### 3. Error Logging
```python
# Errors are logged but details not exposed to users
_log_error("OPERATION", exception)
```

### 4. Database Isolation
```python
# All operations use TgClient.ID for multi-tenancy
db.users[TgClient.ID]  # Scoped to this bot instance
```

## Scalability Considerations

### Horizontal Scaling
- Multiple bot instances can share same MongoDB
- Each uses TgClient.ID for isolation
- No conflicts between instances

### Vertical Scaling
- Connection pooling handled by Motor
- Async operations allow high concurrency
- Bulk operations reduce database load

### Query Optimization
- Create indexes on frequently searched fields
- Use aggregation for complex analytics
- Use bulk operations for batch changes

## Integration Points

```
Telegram Bot Framework
    ├─► Message Handlers
    │   └─► repos.users.get_user()
    │
    ├─► Command Handlers
    │   └─► repos.users.update_user()
    │
    └─► Callbacks
        └─► repos.download_tasks.update_task_status()

Download Manager
    ├─► create_task()
    │   └─► repos.download_tasks.create_task()
    │
    ├─► on_progress()
    │   └─► repos.download_tasks.update_task_progress()
    │
    └─► on_complete()
        └─► repos.download_tasks.update_task_status()

Task Scheduler
    ├─► rss_update_job()
    │   └─► repos.rss.get_all_rss()
    │
    └─► cleanup_job()
        └─► repos.download_tasks.clear_old_tasks()

Admin Dashboard
    ├─► stats()
    │   └─► repos.indexed.aggregate()
    │
    └─► user_management()
        └─► repos.users.set_sudo()
```

## Monitoring and Health

### Health Check Points
```python
health = await repos.health_check()
{
    "manager": "healthy",
    "database": "healthy",
    "repositories": {
        "user_preferences": "healthy",
        "download_tasks": "healthy",
        "rss": "healthy",
        "users": "healthy",
        "variables": "healthy",
        "indexed": "healthy",
        "bulk": "healthy"
    }
}
```

### Availability Check
```python
if repos.users.is_available:
    # Safe to use
```

### Error Monitoring
```python
# All errors logged via LOGGER
# Check logs for: "Database {OPERATION} error"
```

## Future Architecture

The repositories pattern is designed for extensibility:

```
Current: 7 repositories
├─ Core data management
├─ Search and analytics
└─ Batch operations

Future additions could include:
├─ CacheRepository (Redis integration)
├─ AuditRepository (Activity logging)
├─ SessionRepository (User sessions)
├─ NotificationRepository (Message queue)
└─ MetricsRepository (Performance data)

All following same pattern:
├─ Extend BaseDbRepository
├─ Implement required methods
├─ Add to DatabaseRepositoriesManager
└─ Use same error handling
```

---

For more details, see:
- REPOSITORIES_GUIDE.md - Complete API
- EXAMPLES.md - Real-world code
- METHOD_REFERENCE.md - Quick method lookup
