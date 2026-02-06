"""
Task Status Repository - Handles task status caching
Focused on task-specific caching operations
"""

from typing import Optional
from redis.exceptions import RedisError

from bot import LOGGER
from . import BaseRepository


class TaskStatusRepository(BaseRepository):
    """Manages cached task status data"""
    
    async def cache_task_status(self, task_id: str, status: dict, ttl: int = 300) -> bool:
        """
        Cache task status for fast retrieval
        
        Args:
            task_id: Task identifier
            status: Status dictionary
            ttl: Time to live in seconds (default: 5 minutes)
        
        Returns:
            True if cached successfully, False otherwise
        """
        if not self.is_enabled:
            return False
        
        try:
            key = f"task:status:{task_id}"
            import pickle
            data = pickle.dumps(status)
            await self._client.setex(key, ttl, data)
            return True
        except RedisError as e:
            self._log_error("CACHE_TASK_STATUS", e)
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """
        Get cached task status
        
        Args:
            task_id: Task identifier
        
        Returns:
            Task status dict if found, None otherwise
        """
        if not self.is_enabled:
            return None
        
        try:
            key = f"task:status:{task_id}"
            value = await self._client.get(key)
            
            if value is None:
                return None
            
            import pickle
            try:
                return pickle.loads(value)
            except (pickle.UnpicklingError, EOFError, TypeError) as e:
                LOGGER.debug(f"Could not unpickle task status for {task_id}: {e}")
                return None
                
        except RedisError as e:
            self._log_error("GET_TASK_STATUS", e)
            return None
    
    async def invalidate_task_status(self, task_id: str) -> bool:
        """
        Remove task from cache when status changes
        
        Args:
            task_id: Task identifier
        
        Returns:
            True if deleted, False otherwise
        """
        if not self.is_enabled:
            return False
        
        try:
            key = f"task:status:{task_id}"
            deleted = await self._client.delete(key)
            return deleted > 0
        except RedisError as e:
            self._log_error("INVALIDATE_TASK_STATUS", e)
            return False
    
    async def get_task_batch(self, *task_ids: str) -> dict:
        """
        Get status for multiple tasks efficiently
        
        Args:
            task_ids: One or more task IDs
        
        Returns:
            Dictionary mapping task_id to status
        """
        if not self.is_enabled:
            return {}
        
        try:
            keys = [f"task:status:{tid}" for tid in task_ids]
            values = await self._client.mget(*keys)
            
            result = {}
            import pickle
            for task_id, value in zip(task_ids, values):
                if value:
                    try:
                        result[task_id] = pickle.loads(value)
                    except (pickle.UnpicklingError, EOFError, TypeError):
                        pass
            
            return result
        except RedisError as e:
            self._log_error("GET_TASK_BATCH", e)
            return {}
    
    async def close(self):
        """Cleanup task status repository"""
        pass
