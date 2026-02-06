"""
User Preferences Repository - Handles user preferences storage and management
Manages user-specific settings and configuration
"""

from pymongo.errors import PyMongoError

from bot import LOGGER
from bot.core.telegram_manager import TgClient
from . import BaseDbRepository


class UserPreferencesRepository(BaseDbRepository):
    """Manages user preferences in database"""
    
    async def update_preference(self, user_id: int, key: str, value) -> bool:
        """
        Update a user preference
        
        Args:
            user_id: Telegram user ID
            key: Preference key
            value: Preference value
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            await self._db.user_preferences[TgClient.ID].update_one(
                {"_id": user_id},
                {"$set": {key: value}},
                upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_PREFERENCE", e)
            return False
    
    async def get_preference(self, user_id: int, key: str):
        """Get a specific user preference"""
        if self._return:
            return None
        
        try:
            prefs = await self._db.user_preferences[TgClient.ID].find_one({"_id": user_id})
            if prefs:
                return prefs.get(key)
            return None
        except PyMongoError as e:
            self._log_error("GET_PREFERENCE", e)
            return None
    
    async def delete_preference(self, user_id: int, key: str) -> bool:
        """Delete a user preference"""
        if self._return:
            return False
        
        try:
            await self._db.user_preferences[TgClient.ID].update_one(
                {"_id": user_id},
                {"$unset": {key: 1}}
            )
            return True
        except PyMongoError as e:
            self._log_error("DELETE_PREFERENCE", e)
            return False
    
    async def get_all_preferences(self, user_id: int) -> dict:
        """Get all preferences for a user"""
        if self._return:
            return {}
        
        try:
            prefs = await self._db.user_preferences[TgClient.ID].find_one({"_id": user_id})
            if prefs:
                prefs.pop("_id", None)
                return prefs
            return {}
        except PyMongoError as e:
            self._log_error("GET_ALL_PREFERENCES", e)
            return {}
    
    async def get_all_user_preferences(self) -> dict:
        """Get all users' preferences"""
        if self._return:
            return {}
        
        try:
            preferences = {}
            async for prefs in self._db.user_preferences[TgClient.ID].find({}):
                user_id = prefs.get("_id")
                if user_id:
                    prefs.pop("_id", None)
                    preferences[user_id] = prefs
            return preferences
        except PyMongoError as e:
            self._log_error("GET_ALL_USER_PREFERENCES", e)
            return {}
    
    async def delete_all_preferences(self, user_id: int) -> bool:
        """Delete all preferences for a user"""
        if self._return:
            return False
        
        try:
            result = await self._db.user_preferences[TgClient.ID].delete_one({"_id": user_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            self._log_error("DELETE_ALL_PREFERENCES", e)
            return False
    
    async def clear_all_preferences(self) -> bool:
        """Clear all preferences from all users"""
        if self._return:
            return False
        
        try:
            await self._db.user_preferences[TgClient.ID].delete_many({})
            return True
        except PyMongoError as e:
            self._log_error("CLEAR_ALL_PREFERENCES", e)
            return False
    
    async def close(self):
        """Cleanup user preferences repository"""
        pass
