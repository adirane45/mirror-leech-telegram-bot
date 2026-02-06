"""
Database Repository Pattern - Base Class and Manager for MongoDB repositories
Provides organized data access layer for the bot
"""

from abc import ABC, abstractmethod
from pymongo.errors import PyMongoError

from bot import LOGGER
from bot.core.telegram_manager import TgClient


class BaseDbRepository(ABC):
    """Base class for all database repositories"""
    
    def __init__(self, db=None):
        """
        Args:
            db: MongoDB database instance
        """
        self._db = db
        self._return = True  # Indicates if DB is unavailable
    
    @property
    def is_available(self) -> bool:
        """Check if database connection is available"""
        return not self._return and self._db is not None
    
    def set_db(self, db):
        """Update the database instance"""
        self._db = db
        self._return = db is None
    
    def set_return_status(self, status: bool):
        """Set the return (unavailable) status"""
        self._return = status
    
    @abstractmethod
    async def close(self):
        """Close repository resources"""
        pass
    
    def _log_error(self, operation: str, error: Exception):
        """Log database errors consistently"""
        LOGGER.error(f"Database {operation} error: {error}")


# Import all repositories for easy access
from .user_preferences_repository import UserPreferencesRepository
from .download_tasks_repository import DownloadTasksRepository
from .rss_repository import RssRepository
from .users_repository import UsersRepository
from .variables_repository import VariablesRepository
from .indexed_repository import IndexedRepository
from .bulk_operations_repository import BulkOperationsRepository
from .manager import (
    DatabaseRepositoriesManager,
    initialize_repositories,
    get_repositories_manager,
    close_repositories,
)

__all__ = [
    "BaseDbRepository",
    "UserPreferencesRepository",
    "DownloadTasksRepository",
    "RssRepository",
    "UsersRepository",
    "VariablesRepository",
    "IndexedRepository",
    "BulkOperationsRepository",
    "DatabaseRepositoriesManager",
    "initialize_repositories",
    "get_repositories_manager",
    "close_repositories",
]
