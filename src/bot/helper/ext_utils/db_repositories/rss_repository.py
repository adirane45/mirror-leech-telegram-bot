"""
RSS Repository - Handles RSS feed storage and management
Manages user RSS subscriptions and configurations
"""

from pymongo.errors import PyMongoError

from bot import LOGGER, rss_dict
from bot.core.telegram_manager import TgClient
from . import BaseDbRepository


class RssRepository(BaseDbRepository):
    """Manages RSS feed data in database"""
    
    async def update_all_rss(self) -> bool:
        """
        Update all RSS feeds in database
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            for user_id in list(rss_dict.keys()):
                await self._db.rss[TgClient.ID].replace_one(
                    {"_id": user_id}, rss_dict[user_id], upsert=True
                )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_ALL_RSS", e)
            return False
    
    async def update_rss(self, user_id: int) -> bool:
        """
        Update RSS feed for a specific user
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            if user_id in rss_dict:
                await self._db.rss[TgClient.ID].replace_one(
                    {"_id": user_id}, rss_dict[user_id], upsert=True
                )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_RSS", e)
            return False
    
    async def delete_rss(self, user_id: int) -> bool:
        """
        Delete RSS feed for a user
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            result = await self._db.rss[TgClient.ID].delete_one({"_id": user_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            self._log_error("DELETE_RSS", e)
            return False
    
    async def get_rss(self, user_id: int) -> dict:
        """Get RSS configuration for a user"""
        if self._return:
            return {}
        
        try:
            rss = await self._db.rss[TgClient.ID].find_one({"_id": user_id})
            return rss if rss else {}
        except PyMongoError as e:
            self._log_error("GET_RSS", e)
            return {}
    
    async def get_all_rss(self) -> dict:
        """Get all RSS configurations"""
        if self._return:
            return {}
        
        try:
            rss_data = {}
            async for rss in self._db.rss[TgClient.ID].find({}):
                user_id = rss.get("_id")
                if user_id:
                    rss.pop("_id", None)
                    rss_data[user_id] = rss
            return rss_data
        except PyMongoError as e:
            self._log_error("GET_ALL_RSS", e)
            return {}
    
    async def clear_all_rss(self) -> bool:
        """Clear all RSS configurations"""
        if self._return:
            return False
        
        try:
            result = await self._db.rss[TgClient.ID].delete_many({})
            return True
        except PyMongoError as e:
            self._log_error("CLEAR_ALL_RSS", e)
            return False
    
    async def close(self):
        """Cleanup RSS repository"""
        pass
