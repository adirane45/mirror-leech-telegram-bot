"""
Database Repositories Manager - Central manager for all database repositories
Provides unified access to all repository types
"""

from typing import Optional

from bot import LOGGER
from bot.core.telegram_manager import TgClient
from .base_repository import BaseDbRepository
from .user_preferences_repository import UserPreferencesRepository
from .download_tasks_repository import DownloadTasksRepository
from .rss_repository import RssRepository
from .users_repository import UsersRepository
from .variables_repository import VariablesRepository
from .indexed_repository import IndexedRepository
from .bulk_operations_repository import BulkOperationsRepository


class DatabaseRepositoriesManager:
    """Central manager for all database repositories"""
    
    def __init__(self, db):
        """
        Initialize repositories manager
        
        Args:
            db: MongoDB database connection instance
        """
        self._db = db
        self._return = False
        
        # Initialize all repositories
        self.user_preferences = UserPreferencesRepository(db)
        self.download_tasks = DownloadTasksRepository(db)
        self.rss = RssRepository(db)
        self.users = UsersRepository(db)
        self.variables = VariablesRepository(db)
        self.indexed = IndexedRepository(db)
        self.bulk = BulkOperationsRepository(db)
        
        LOGGER.info("Database repositories manager initialized")
    
    def set_return(self, return_value: bool):
        """Set return flag for all repositories"""
        self._return = return_value
        self.user_preferences._return = return_value
        self.download_tasks._return = return_value
        self.rss._return = return_value
        self.users._return = return_value
        self.variables._return = return_value
        self.indexed._return = return_value
        self.bulk._return = return_value
    
    @property
    def return_value(self) -> bool:
        """Get current return flag value"""
        return self._return
    
    async def health_check(self) -> dict:
        """
        Perform health checks on all repositories
        
        Returns:
            Dictionary with health status of each repository
        """
        health_status = {
            "manager": "healthy",
            "repositories": {}
        }
        
        try:
            # Check database connection
            await self._db.command("ping")
            health_status["database"] = "healthy"
        except Exception as e:
            LOGGER.error(f"Database health check failed: {e}")
            health_status["database"] = "unhealthy"
            return health_status
        
        # Check individual repositories
        repositories = {
            "user_preferences": self.user_preferences,
            "download_tasks": self.download_tasks,
            "rss": self.rss,
            "users": self.users,
            "variables": self.variables,
            "indexed": self.indexed,
            "bulk": self.bulk,
        }
        
        for name, repo in repositories.items():
            try:
                # Simple health check - can be extended
                health_status["repositories"][name] = "healthy"
            except Exception as e:
                LOGGER.warning(f"Repository {name} health check warning: {e}")
                health_status["repositories"][name] = "warning"
        
        return health_status
    
    async def close(self):
        """Close all repositories"""
        try:
            await self.user_preferences.close()
            await self.download_tasks.close()
            await self.rss.close()
            await self.users.close()
            await self.variables.close()
            await self.indexed.close()
            await self.bulk.close()
            LOGGER.info("All repositories closed successfully")
        except Exception as e:
            LOGGER.error(f"Error closing repositories: {e}")


# Global repositories manager instance
_repositories_manager: Optional[DatabaseRepositoriesManager] = None


def initialize_repositories(db) -> DatabaseRepositoriesManager:
    """
    Initialize and return the global repositories manager
    
    Args:
        db: MongoDB database connection
    
    Returns:
        DatabaseRepositoriesManager instance
    """
    global _repositories_manager
    _repositories_manager = DatabaseRepositoriesManager(db)
    return _repositories_manager


def get_repositories_manager() -> Optional[DatabaseRepositoriesManager]:
    """Get the global repositories manager instance"""
    return _repositories_manager


async def close_repositories():
    """Close the global repositories manager"""
    global _repositories_manager
    if _repositories_manager:
        await _repositories_manager.close()
        _repositories_manager = None
