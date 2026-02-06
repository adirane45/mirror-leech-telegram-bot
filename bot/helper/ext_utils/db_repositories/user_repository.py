"""
User Repository - Handles user data storage and retrieval
Manages user profiles, documents, and binary data
"""

from aiofiles import open as aiopen
from pymongo.errors import PyMongoError

from bot import LOGGER, user_data
from bot.core.telegram_manager import TgClient
from . import BaseDbRepository


class UserRepository(BaseDbRepository):
    """Manages user data in database"""
    
    async def update_user_data(self, user_id: int) -> bool:
        """
        Update user data in database
        
        Args:
            user_id: Telegram user ID
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            data = user_data.get(user_id, {})
            data = data.copy()
            
            # Remove binary fields
            for key in ("THUMBNAIL", "RCLONE_CONFIG", "TOKEN_PICKLE"):
                data.pop(key, None)
            
            # Complex aggregation pipeline to merge data while preserving binary fields
            pipeline = [
                {
                    "$replaceRoot": {
                        "newRoot": {
                            "$mergeObjects": [
                                data,
                                {
                                    "$arrayToObject": {
                                        "$filter": {
                                            "input": {"$objectToArray": "$$ROOT"},
                                            "as": "field",
                                            "cond": {
                                                "$in": [
                                                    "$$field.k",
                                                    [
                                                        "THUMBNAIL",
                                                        "RCLONE_CONFIG",
                                                        "TOKEN_PICKLE",
                                                    ],
                                                ]
                                            },
                                        }
                                    }
                                },
                            ]
                        }
                    }
                }
            ]
            
            await self._db.users.update_one({"_id": user_id}, pipeline, upsert=True)
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_USER_DATA", e)
            return False
    
    async def update_user_document(self, user_id: int, key: str, path: str = "") -> bool:
        """
        Update user document (binary data like thumbnails, configs)
        
        Args:
            user_id: Telegram user ID
            key: Document key in database
            path: File path to store (empty = delete document)
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            if path:
                # Store document
                async with aiopen(path, "rb+") as doc:
                    doc_bin = await doc.read()
                await self._db.users.update_one(
                    {"_id": user_id}, {"$set": {key: doc_bin}}, upsert=True
                )
            else:
                # Delete document
                await self._db.users.update_one(
                    {"_id": user_id}, {"$unset": {key: ""}}, upsert=True
                )
            
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_USER_DOCUMENT", e)
            return False
        except Exception as e:
            LOGGER.error(f"Error updating user document for {user_id}: {e}")
            return False
    
    async def get_user_data(self, user_id: int) -> dict:
        """Get user data from database"""
        if self._return:
            return {}
        
        try:
            user = await self._db.users.find_one({"_id": user_id})
            return user if user else {}
        except PyMongoError as e:
            self._log_error("GET_USER_DATA", e)
            return {}
    
    async def delete_user_data(self, user_id: int) -> bool:
        """Delete all user data"""
        if self._return:
            return False
        
        try:
            result = await self._db.users.delete_one({"_id": user_id})
            return result.deleted_count > 0
        except PyMongoError as e:
            self._log_error("DELETE_USER_DATA", e)
            return False
    
    async def save_thumbnail(self, user_id: int, thumbnail_data: bytes) -> bool:
        """Store user thumbnail"""
        return await self.update_user_document(user_id, "THUMBNAIL")
    
    async def save_rclone_config(self, user_id: int) -> bool:
        """Store rclone configuration for user"""
        return await self.update_user_document(user_id, "RCLONE_CONFIG")
    
    async def save_token_pickle(self, user_id: int) -> bool:
        """Store token pickle for user"""
        return await self.update_user_document(user_id, "TOKEN_PICKLE")
    
    async def get_all_users(self) -> list:
        """Get list of all user IDs"""
        if self._return:
            return []
        
        try:
            users = []
            async for user in self._db.users.find({}, {"_id": 1}):
                users.append(user["_id"])
            return users
        except PyMongoError as e:
            self._log_error("GET_ALL_USERS", e)
            return []
    
    async def close(self):
        """Cleanup user repository"""
        pass
