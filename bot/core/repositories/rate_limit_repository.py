"""
Rate Limit Repository - Handles rate limiting operations
Focused on checking and enforcing rate limits
"""

from redis.exceptions import RedisError

from bot import LOGGER
from . import BaseRepository


class RateLimitRepository(BaseRepository):
    """Manages rate limiting for users and actions"""
    
    async def check_rate_limit(
        self, 
        user_id: int, 
        action: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, int]:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: User ID
            action: Action name (e.g., 'download', 'upload')
            limit: Maximum actions per window
            window: Time window in seconds
        
        Returns:
            (allowed: bool, remaining: int)
            - allowed: True if user can perform action, False if limit exceeded
            - remaining: Number of remaining actions in current window
        """
        if not self.is_enabled:
            return True, limit  # No rate limiting if Redis disabled
        
        try:
            key = f"ratelimit:{user_id}:{action}"
            current = await self._client.get(key)
            
            if current is None:
                # First request in this window
                await self._client.setex(key, window, 1)
                return True, limit - 1
            
            count = int(current)
            if count >= limit:
                # Limit exceeded
                return False, 0
            
            # Increment counter and allow
            await self._client.incr(key)
            return True, limit - count - 1
            
        except RedisError as e:
            self._log_error("CHECK_RATE_LIMIT", e)
            return True, limit  # Allow on error (fail open)
    
    async def reset_rate_limit(self, user_id: int, action: str) -> bool:
        """
        Reset rate limit for a specific user and action
        
        Args:
            user_id: User ID
            action: Action name
        
        Returns:
            True if reset successfully
        """
        if not self.is_enabled:
            return False
        
        try:
            key = f"ratelimit:{user_id}:{action}"
            deleted = await self._client.delete(key)
            return deleted > 0
        except RedisError as e:
            self._log_error("RESET_RATE_LIMIT", e)
            return False
    
    async def reset_user_rate_limits(self, user_id: int) -> int:
        """
        Reset all rate limits for a user
        
        Args:
            user_id: User ID
        
        Returns:
            Number of rate limit entries deleted
        """
        if not self.is_enabled:
            return 0
        
        try:
            pattern = f"ratelimit:{user_id}:*"
            keys = []
            async for key in self._client.scan_iter(match=pattern, count=100):
                keys.append(key)
            
            if keys:
                return await self._client.delete(*keys)
            return 0
        except RedisError as e:
            self._log_error("RESET_USER_RATE_LIMITS", e)
            return 0
    
    async def get_rate_limit_status(
        self, 
        user_id: int, 
        action: str, 
        limit: int
    ) -> dict:
        """
        Get detailed rate limit status for a user and action
        
        Args:
            user_id: User ID
            action: Action name
            limit: Total limit for this action
        
        Returns:
            Dictionary with rate limit status information
        """
        if not self.is_enabled:
            return {"enabled": False, "used": 0, "remaining": limit}
        
        try:
            key = f"ratelimit:{user_id}:{action}"
            current = await self._client.get(key)
            ttl = await self._client.ttl(key)
            
            used = int(current) if current else 0
            remaining = max(0, limit - used)
            
            return {
                "enabled": True,
                "used": used,
                "remaining": remaining,
                "limit": limit,
                "reset_in_seconds": ttl if ttl > 0 else 0
            }
        except RedisError as e:
            self._log_error("GET_RATE_LIMIT_STATUS", e)
            return {"enabled": True, "error": str(e)}
    
    async def close(self):
        """Cleanup rate limit repository"""
        pass
