"""
Database Repositories Usage Examples
Real-world examples of how to use the repositories
"""

# Example 1: Initialize repositories in bot startup
# ===================================================

async def initialize_bot():
    """Initialize bot with database repositories"""
    from bot.helper.ext_utils.db_repositories import initialize_repositories
    from bot.core.telegram_manager import TgClient
    
    # Setup MongoDB connection
    db = ...  # Your MongoDB instance
    
    # Initialize repositories manager
    repos_manager = initialize_repositories(db)
    
    # Perform health check
    health = await repos_manager.health_check()
    if health["database"] == "healthy":
        print("✓ Database repositories initialized successfully")
    else:
        print("✗ Database connection failed")
        raise Exception("Cannot initialize repositories")


# Example 2: User management
# ==========================

async def handle_new_user(user_id: int, user_info: dict):
    """Handle new user registration"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    # Store user data
    user_data = {
        "_id": user_id,
        "name": user_info.get("name"),
        "email": user_info.get("email"),
        "is_sudo": False,
        "created_at": time.time()
    }
    
    success = await repos.users.update_user(user_id, user_data)
    
    if success:
        # Initialize user preferences
        await repos.user_preferences.update_preference(
            user_id, "download_path", "/downloads"
        )
        await repos.user_preferences.update_preference(
            user_id, "theme", "dark"
        )
        return True
    else:
        print(f"Failed to register user {user_id}")
        return False


async def get_user_settings(user_id: int) -> dict:
    """Retrieve all user data and preferences"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    # Get user info
    user = await repos.users.get_user(user_id)
    
    # Get preferences
    preferences = await repos.user_preferences.get_all_preferences(user_id)
    
    # Combine and return
    return {
        "user": user,
        "preferences": preferences,
        "is_admin": user.get("is_sudo", False)
    }


# Example 3: Download task management
# ====================================

async def create_download_task(user_id: int, file_info: dict) -> str:
    """Create a new download task"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    import uuid
    
    repos = get_repositories_manager()
    
    task_id = str(uuid.uuid4())
    task = {
        "_id": task_id,
        "user_id": user_id,
        "file_name": file_info["name"],
        "size": file_info["size"],
        "url": file_info["url"],
        "status": "pending",
        "progress": 0,
        "created_at": time.time(),
        "started_at": None,
        "completed_at": None
    }
    
    success = await repos.download_tasks.create_task(task)
    
    if success:
        return task_id
    else:
        return None


async def update_download_progress(task_id: str, progress: int):
    """Update download task progress"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    await repos.download_tasks.update_task_progress(task_id, progress)


async def complete_download(task_id: str):
    """Mark download task as completed"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    await repos.download_tasks.update_task_status(task_id, "completed")


async def get_user_downloads(user_id: int, limit: int = 50) -> list:
    """Get all downloads for a user"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    # Get completed downloads
    downloads = await repos.indexed.search(
        "downloads",
        {"user_id": user_id, "status": "completed"},
        limit=limit
    )
    
    return downloads


# Example 4: RSS management
# =========================

async def add_rss_feed(user_id: int, rss_url: str):
    """Add RSS feed for user"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    # Get existing RSS config
    rss_config = await repos.rss.get_rss(user_id) or {}
    
    # Add new feed
    if "feeds" not in rss_config:
        rss_config["feeds"] = []
    
    rss_config["feeds"].append({
        "url": rss_url,
        "added_at": time.time(),
        "enabled": True
    })
    
    # Update in database
    await repos.rss.update_rss(user_id)


async def get_all_rss_feeds() -> dict:
    """Get all RSS feeds from all users"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    all_rss = await repos.rss.get_all_rss()
    return all_rss


# Example 5: Global configuration
# ===============================

async def setup_global_config():
    """Setup global configuration variables"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    config_defaults = {
        "max_bandwidth": 100,
        "max_concurrent_downloads": 5,
        "notification_mode": "quiet",
        "enable_compression": True,
        "maintenance_mode": False,
        "api_rate_limit": 100
    }
    
    # Update all at once
    success = await repos.variables.update_multiple_variables(config_defaults)
    
    return success


async def get_config_value(key: str, default=None):
    """Get a configuration value"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    value = await repos.variables.get_variable(key)
    return value if value is not None else default


async def update_config_value(key: str, value):
    """Update a configuration value"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    success = await repos.variables.update_variable(key, value)
    return success


# Example 6: Admin operations
# ===========================

async def promote_to_admin(user_id: int):
    """Promote user to admin"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    success = await repos.users.set_sudo(user_id, True)
    return success


async def get_all_admins() -> list:
    """Get list of all admin users"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    admins = await repos.users.get_sudo_users()
    return admins


# Example 7: Analytics and reporting
# ==================================

async def get_download_statistics() -> dict:
    """Get download statistics"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    # Aggregation pipeline
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_size": {"$sum": "$size"}
            }
        },
        {
            "$sort": {"count": -1}
        }
    ]
    
    stats = await repos.indexed.aggregate("downloads", pipeline)
    
    result = {}
    for stat in stats:
        result[stat["_id"]] = {
            "count": stat["count"],
            "total_size": stat["total_size"]
        }
    
    return result


async def get_user_statistics(user_id: int) -> dict:
    """Get statistics for a specific user"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    # Count user downloads by status
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "total_size": {"$sum": "$size"}
            }
        }
    ]
    
    stats = await repos.indexed.aggregate("downloads", pipeline)
    
    result = {}
    for stat in stats:
        result[stat["_id"]] = {
            "count": stat["count"],
            "total_size": stat["total_size"]
        }
    
    return result


# Example 8: Bulk operations
# ==========================

async def migrate_users_batch(users_list: list):
    """Migrate multiple users to new schema"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    # Prepare documents
    upserts = [
        ({"_id": user["id"]}, {
            "_id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "status": "active",
            "is_sudo": False,
            "migrated": True,
            "migration_time": time.time()
        })
        for user in users_list
    ]
    
    # Bulk upsert
    count = await repos.bulk.bulk_upsert("users", upserts)
    print(f"Migrated {count} users")


async def delete_inactive_users(user_ids: list):
    """Delete multiple inactive users"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    # Prepare filters
    filters = [{"_id": user_id} for user_id in user_ids]
    
    # Bulk delete
    count = await repos.bulk.bulk_delete("users", filters)
    print(f"Deleted {count} users")


# Example 9: Error handling
# =========================

async def safe_update_user(user_id: int, data: dict):
    """Update user with error handling"""
    from bot.helper.ext_utils.db_repositories import get_repositories_manager
    
    repos = get_repositories_manager()
    
    # Check if database is available
    if not repos.users.is_available:
        print("Database is currently unavailable")
        return False
    
    try:
        success = await repos.users.update_user(user_id, data)
        
        if success:
            print(f"User {user_id} updated successfully")
            return True
        else:
            print(f"Failed to update user {user_id}")
            return False
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


# Example 10: Shutdown cleanup
# ============================

async def shutdown_bot():
    """Properly shutdown bot and close repositories"""
    from bot.helper.ext_utils.db_repositories import close_repositories
    
    try:
        print("Closing database repositories...")
        await close_repositories()
        print("✓ Repositories closed successfully")
    except Exception as e:
        print(f"✗ Error closing repositories: {e}")


if __name__ == "__main__":
    import asyncio
    
    # Run examples
    asyncio.run(initialize_bot())
    
    # More examples would run here...
    
    asyncio.run(shutdown_bot())
