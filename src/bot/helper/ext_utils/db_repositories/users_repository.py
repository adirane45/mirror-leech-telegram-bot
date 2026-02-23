"""
Users Repository - Handles user data storage and management
Manages user preferences, permissions, and settings
"""

from pymongo.errors import PyMongoError

from bot import LOGGER
from bot.core.telegram_manager import TgClient
from . import BaseDbRepository


class UsersRepository(BaseDbRepository):
    """Manages user data in database"""
    
    async def update_user(self, user_id: int, user_data: dict) -> bool:
        """
        Update user data
        
        Args:
            user_id: Telegram user ID
            user_data: User data to update
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            await self._db.users[TgClient.ID].replace_one(
                {"_id": user_id}, user_data, upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_USER", e)
            return False
    
    async def delete_user(self, user_id: int) -> bool:
        """
        Delete user data
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            result = await self._db.users[TgClient.ID].delete_one({"_id": user_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            self._log_error("DELETE_USER", e)
            return False
    
    async def get_user(self, user_id: int) -> dict:
        """Get user data"""
        if self._return:
            return {}
        
        try:
            user = await self._db.users[TgClient.ID].find_one({"_id": user_id})
            return user if user else {}
        except PyMongoError as e:
            self._log_error("GET_USER", e)
            return {}
    
    async def get_all_users(self) -> dict:
        """Get all users data"""
        if self._return:
            return {}
        
        try:
            users_data = {}
            async for user in self._db.users[TgClient.ID].find({}):
                user_id = user.get("_id")
                if user_id:
                    user.pop("_id", None)
                    users_data[user_id] = user
            return users_data
        except PyMongoError as e:
            self._log_error("GET_ALL_USERS", e)
            return {}
    
    async def is_sudo(self, user_id: int) -> bool:
        """Check if user is sudo"""
        if self._return:
            return False
        
        try:
            user = await self._db.users[TgClient.ID].find_one({"_id": user_id})
            return user.get("is_sudo", False) if user else False
        except PyMongoError as e:
            self._log_error("IS_SUDO", e)
            return False
    
    async def set_sudo(self, user_id: int, is_sudo: bool) -> bool:
        """Set sudo status for user"""
        if self._return:
            return False
        
        try:
            await self._db.users[TgClient.ID].update_one(
                {"_id": user_id},
                {"$set": {"is_sudo": is_sudo}},
                upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("SET_SUDO", e)
            return False
    
    async def get_sudo_users(self) -> list:
        """Get all sudo users"""
        if self._return:
            return []
        
        try:
            sudo_users = []
            async for user in self._db.users[TgClient.ID].find({"is_sudo": True}):
                sudo_users.append(user.get("_id"))
            return sudo_users
        except PyMongoError as e:
            self._log_error("GET_SUDO_USERS", e)
            return []
    
    async def clear_all_users(self) -> bool:
        """Clear all users data"""
        if self._return:
            return False
        
        try:
            await self._db.users[TgClient.ID].delete_many({})
            return True
        except PyMongoError as e:
            self._log_error("CLEAR_ALL_USERS", e)
            return False
    
    async def close(self):
        """Cleanup users repository"""
        pass
