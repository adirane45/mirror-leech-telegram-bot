# Database Repositories - Getting Started Guide

## 🚀 Quick Start (5 minutes)

### 1. Initialize Repositories
In your bot's startup code:
```python
from bot.helper.ext_utils.db_repositories import initialize_repositories, get_repositories_manager

# During bot initialization
db = ...  # your MongoDB instance
repos_manager = initialize_repositories(db)
```

### 2. Use in Your Code
Anywhere in your bot:
```python
from bot.helper.ext_utils.db_repositories import get_repositories_manager

repos = get_repositories_manager()

# Update user data
await repos.users.update_user(user_id, {"name": "John"})

# Create download task
await repos.download_tasks.create_task(task_data)

# Get user preferences
prefs = await repos.user_preferences.get_all_preferences(user_id)
```

### 3. Shutdown Cleanup
In your bot's shutdown code:
```python
from bot.helper.ext_utils.db_repositories import close_repositories

await close_repositories()
```

## 📚 Documentation Map

Choose your starting point based on your needs:

### For Learning (First Time)
1. **[START HERE] README.md** (~5 min read)
   - What is this?
   - Why use it?
   - Basic examples
   - Quick reference

2. **EXAMPLES.md** (~20 min read)
   - Real-world examples
   - Copy-paste ready code
   - Common patterns
   - Error handling

### For Implementation (Building Features)
1. **REPOSITORIES_GUIDE.md** (~30 min read)
   - Complete API reference
   - Every method documented
   - Detailed examples
   - Best practices

### For Understanding
1. **INDEX.md** (~30 min read)
   - Full architecture overview
   - Design patterns used
   - Integration points
   - Performance considerations

### For Deep Dive
1. **IMPLEMENTATION_SUMMARY.md**
   - What was built
   - Why it was built
   - How it works
   - Future extensions

## 🏗️ Architecture at a Glance

```
Your Code (Handlers, Commands, etc.)
    ↓
get_repositories_manager()
    ↓
DatabaseRepositoriesManager
    ├─ user_preferences
    ├─ download_tasks
    ├─ rss
    ├─ users
    ├─ variables
    ├─ indexed
    └─ bulk
    ↓
MongoDB Database
```

## 📦 Available Repositories

| Repository | Purpose | Key Methods |
|------------|---------|------------|
| **UserPreferencesRepository** | User settings | update_preference, get_preference, get_all_preferences |
| **DownloadTasksRepository** | Download tracking | create_task, update_task_status, get_user_tasks |
| **RssRepository** | RSS feeds | update_rss, get_rss, get_all_rss |
| **UsersRepository** | User data | update_user, get_user, set_sudo, get_sudo_users |
| **VariablesRepository** | Global config | update_variable, get_variable, update_multiple_variables |
| **IndexedRepository** | Search & analytics | search, count_documents, aggregate, create_index |
| **BulkOperationsRepository** | Batch ops | bulk_insert, bulk_update, bulk_delete, bulk_upsert |

## 💡 Common Use Cases

### Add User
```python
repos = get_repositories_manager()
await repos.users.update_user(user_id, {
    "name": "John",
    "email": "john@example.com",
    "is_sudo": False
})
```

### Track Download
```python
task_id = str(uuid.uuid4())
await repos.download_tasks.create_task({
    "_id": task_id,
    "user_id": user_id,
    "file_name": "video.mp4",
    "status": "downloading",
    "progress": 0
})
```

### Get User Stats
```python
tasks = await repos.download_tasks.get_user_tasks(user_id)
completed = len([t for t in tasks if t["status"] == "completed"])
```

### Admin Operations
```python
# Add admin
await repos.users.set_sudo(user_id, True)

# List admins
admins = await repos.users.get_sudo_users()
```

### Configuration
```python
# Set config
await repos.variables.update_variable("max_bandwidth", 100)

# Get config
max_bw = await repos.variables.get_variable("max_bandwidth")
```

### Search Downloads
```python
# Find completed downloads
completed = await repos.indexed.search(
    "downloads",
    {"status": "completed"},
    limit=50
)

# Statistics
pipeline = [
    {"$match": {"status": "completed"}},
    {"$group": {"_id": "$user_id", "count": {"$sum": 1}}}
]
stats = await repos.indexed.aggregate("downloads", pipeline)
```

## 🛠️ Troubleshooting

### "Cannot find repositories"
Make sure you've called `initialize_repositories(db)` during startup.

### "Database unavailable" errors
Check MongoDB connection:
```python
repos = get_repositories_manager()
health = await repos.health_check()
print(health)  # Shows what's available
```

### "All methods return empty/false"
Repository might not be available. Check:
```python
if repos.users.is_available:
    # Safe to use
    user = await repos.users.get_user(user_id)
else:
    print("Database temporarily unavailable")
```

### "Method not found"
Check REPOSITORIES_GUIDE.md for correct method names and parameters.

## 📖 Reading Guide

### 5-Minute Quick Overview
```
README.md (Quick start section)
```

### 20-Minute Getting Started
```
README.md (complete)
  +
EXAMPLES.md (first 3-4 examples)
```

### 1-Hour Full Understanding
```
README.md
  +
REPOSITORIES_GUIDE.md (one or two repositories)
  +
EXAMPLES.md (relevant examples)
```

### 2-Hour Deep Dive
```
Read all documentation files in order:
1. README.md
2. REPOSITORIES_GUIDE.md
3. EXAMPLES.md
4. INDEX.md
5. IMPLEMENTATION_SUMMARY.md
```

## 🎯 Next Steps

1. **Read README.md** - Get overview (5 min)
2. **Check EXAMPLES.md** - Find your use case (10 min)
3. **Review REPOSITORIES_GUIDE.md** - Learn the API (10 min)
4. **Start coding** - Use get_repositories_manager() in your code
5. **Check health** - Verify with health_check() at startup
6. **Monitor logs** - Check LOGGER output for any issues

## 🔗 File Navigation

```
📂 db_repositories/
├── 📄 README.md
│   ├─ Purpose: Quick start guide
│   └─ Read when: First time setup
│
├── 📄 REPOSITORIES_GUIDE.md
│   ├─ Purpose: Complete API reference
│   └─ Read when: Implementing features
│
├── 📄 EXAMPLES.md
│   ├─ Purpose: Real-world code examples
│   └─ Read when: Building specific features
│
├── 📄 INDEX.md
│   ├─ Purpose: Architecture overview
│   └─ Read when: Understanding system design
│
├── 📄 IMPLEMENTATION_SUMMARY.md
│   ├─ Purpose: What was built and why
│   └─ Read when: Reviewing implementation
│
├── 📄 QUICK_START.md
│   ├─ Purpose: This file
│   └─ Read when: Finding where to start
│
└── 🐍 Python Files
    ├─ manager.py (DatabaseRepositoriesManager)
    ├─ user_preferences_repository.py
    ├─ download_tasks_repository.py
    ├─ rss_repository.py
    ├─ users_repository.py
    ├─ variables_repository.py
    ├─ indexed_repository.py
    └─ bulk_operations_repository.py
```

## ✅ Checklist for Integration

- [ ] Read README.md
- [ ] Review EXAMPLES.md for your use cases
- [ ] Call initialize_repositories(db) in bot startup
- [ ] Replace direct database access with repositories
- [ ] Add health_check() to startup verification
- [ ] Update error handling to use repository returns
- [ ] Call close_repositories() on shutdown
- [ ] Test with health monitoring
- [ ] Update documentation for your team

## 🤝 Getting Help

1. **Check REPOSITORIES_GUIDE.md** - Most common questions answered
2. **Review EXAMPLES.md** - Find similar code to your need
3. **Check logs** - LOGGER provides detailed error messages
4. **Call health_check()** - Verify database connection
5. **Review INDEX.md** - Understand architecture

## 📞 Support Resources

- REPOSITORIES_GUIDE.md - Complete API documentation
- EXAMPLES.md - Copy-paste ready code
- INDEX.md - Architecture and design overview
- IMPLEMENTATION_SUMMARY.md - What and why
- __init__.py - See all exports
- manager.py - Central coordination

---

**Ready to start?** → Open README.md →  Read the quick start section → Use get_repositories_manager() → Done!

**Need detailed info?** → Open REPOSITORIES_GUIDE.md → Find your repository → Copy example → Adapt to your code

**Integration done?** → Check EXAMPLES.md → Find similar pattern → Implement in your handler
