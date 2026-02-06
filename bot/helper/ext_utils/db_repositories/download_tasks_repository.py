"""
Download Tasks Repository - Handles download task storage and management
Manages download tracking, progress, and status
"""

from pymongo.errors import PyMongoError

from bot import LOGGER
from bot.core.telegram_manager import TgClient
from . import BaseDbRepository


class DownloadTasksRepository(BaseDbRepository):
    """Manages download task data in database"""
    
    async def create_task(self, task_data: dict) -> bool:
        """
        Create a new download task
        
        Args:
            task_data: Dictionary containing task information
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            task_id = task_data.get("_id")
            if task_id:
                await self._db.downloads[TgClient.ID].replace_one(
                    {"_id": task_id}, task_data, upsert=True
                )
            return True
        except PyMongoError as e:
            self._log_error("CREATE_TASK", e)
            return False
    
    async def get_task(self, task_id: str) -> dict:
        """Get a download task by ID"""
        if self._return:
            return {}
        
        try:
            task = await self._db.downloads[TgClient.ID].find_one({"_id": task_id})
            return task if task else {}
        except PyMongoError as e:
            self._log_error("GET_TASK", e)
            return {}
    
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """
        Update download task status
        
        Args:
            task_id: Task ID
            status: New status (pending, downloading, paused, completed, failed, cancelled)
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            await self._db.downloads[TgClient.ID].update_one(
                {"_id": task_id},
                {"$set": {"status": status}},
                upsert=False
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_TASK_STATUS", e)
            return False
    
    async def update_task_progress(self, task_id: str, progress: int) -> bool:
        """
        Update download task progress
        
        Args:
            task_id: Task ID
            progress: Progress percentage (0-100)
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            await self._db.downloads[TgClient.ID].update_one(
                {"_id": task_id},
                {"$set": {"progress": min(100, max(0, progress))}},
                upsert=False
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_TASK_PROGRESS", e)
            return False
    
    async def get_user_tasks(self, user_id: int) -> list:
        """Get all download tasks for a user"""
        if self._return:
            return []
        
        try:
            tasks = []
            async for task in self._db.downloads[TgClient.ID].find({"user_id": user_id}):
                tasks.append(task)
            return tasks
        except PyMongoError as e:
            self._log_error("GET_USER_TASKS", e)
            return []
    
    async def get_tasks_by_status(self, status: str) -> list:
        """Get all tasks with a specific status"""
        if self._return:
            return []
        
        try:
            tasks = []
            async for task in self._db.downloads[TgClient.ID].find({"status": status}):
                tasks.append(task)
            return tasks
        except PyMongoError as e:
            self._log_error("GET_TASKS_BY_STATUS", e)
            return []
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a download task"""
        if self._return:
            return False
        
        try:
            result = await self._db.downloads[TgClient.ID].delete_one({"_id": task_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            self._log_error("DELETE_TASK", e)
            return False
    
    async def delete_user_tasks(self, user_id: int) -> int:
        """Delete all tasks for a user"""
        if self._return:
            return 0
        
        try:
            result = await self._db.downloads[TgClient.ID].delete_many({"user_id": user_id})
            return result.deleted_count
        except PyMongoError as e:
            self._log_error("DELETE_USER_TASKS", e)
            return 0
    
    async def get_all_tasks(self) -> list:
        """Get all download tasks"""
        if self._return:
            return []
        
        try:
            tasks = []
            async for task in self._db.downloads[TgClient.ID].find({}):
                tasks.append(task)
            return tasks
        except PyMongoError as e:
            self._log_error("GET_ALL_TASKS", e)
            return []
    
    async def clear_all_tasks(self) -> bool:
        """Clear all download tasks"""
        if self._return:
            return False
        
        try:
            await self._db.downloads[TgClient.ID].delete_many({})
            return True
        except PyMongoError as e:
            self._log_error("CLEAR_ALL_TASKS", e)
            return False
    
    async def close(self):
        """Cleanup download tasks repository"""
        pass
