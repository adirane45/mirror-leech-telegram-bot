"""
Session Repository - Handles user session management
Focused on session data storage and retrieval
"""

from typing import Optional
from redis.exceptions import RedisError

from bot import LOGGER
from . import BaseRepository


class SessionRepository(BaseRepository):
    """Manages user session data"""
    
    async def create_session(self, session_id: str, data: dict, ttl: int = 3600) -> bool:
        """
        Create a user session
        
        Args:
            session_id: Unique session identifier
            data: Session data dictionary
            ttl: Time to live in seconds (default: 1 hour)
        
        Returns:
            True if session created successfully
        """
        if not self.is_enabled:
            return False
        
        try:
            key = f"session:{session_id}"
            import pickle
            pickled_data = pickle.dumps(data)
            await self._client.setex(key, ttl, pickled_data)
            LOGGER.debug(f"Session created: {session_id}")
            return True
        except RedisError as e:
            self._log_error("CREATE_SESSION", e)
            return False
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session data
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session data dict if found, None otherwise
        """
        if not self.is_enabled:
            return None
        
        try:
            key = f"session:{session_id}"
            value = await self._client.get(key)
            
            if value is None:
                return None
            
            import pickle
            try:
                return pickle.loads(value)
            except (pickle.UnpicklingError, EOFError, TypeError) as e:
                LOGGER.debug(f"Could not unpickle session {session_id}: {e}")
                return None
                
        except RedisError as e:
            self._log_error("GET_SESSION", e)
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if deleted, False otherwise
        """
        if not self.is_enabled:
            return False
        
        try:
            key = f"session:{session_id}"
            deleted = await self._client.delete(key)
            if deleted > 0:
                LOGGER.debug(f"Session deleted: {session_id}")
            return deleted > 0
        except RedisError as e:
            self._log_error("DELETE_SESSION", e)
            return False
    
    async def update_session(self, session_id: str, data: dict, ttl: int = 3600) -> bool:
        """
        Update existing session data
        
        Args:
            session_id: Session identifier
            data: New session data
            ttl: Time to live in seconds
        
        Returns:
            True if updated successfully
        """
        if not self.is_enabled:
            return False
        
        try:
            key = f"session:{session_id}"
            import pickle
            pickled_data = pickle.dumps(data)
            await self._client.setex(key, ttl, pickled_data)
            return True
        except RedisError as e:
            self._log_error("UPDATE_SESSION", e)
            return False
    
    async def session_exists(self, session_id: str) -> bool:
        """Check if a session exists"""
        if not self.is_enabled:
            return False
        
        try:
            key = f"session:{session_id}"
            return await self._client.exists(key) > 0
        except RedisError:
            return False
    
    async def close(self):
        """Cleanup session repository"""
        pass
