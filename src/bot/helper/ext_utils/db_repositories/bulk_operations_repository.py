"""
Bulk Operations Repository - Handles batch operations and bulk updates
Manages efficient bulk inserts, updates, and deletes
"""

from typing import List
from pymongo.errors import PyMongoError
from pymongo import UpdateOne, InsertOne, DeleteOne

from bot import LOGGER
from bot.core.telegram_manager import TgClient
from . import BaseDbRepository


class BulkOperationsRepository(BaseDbRepository):
    """Manages bulk operations in database"""
    
    async def bulk_insert(self, table: str, documents: List[dict]) -> int:
        """
        Bulk insert documents
        
        Args:
            table: Table name
            documents: List of documents to insert
        
        Returns:
            Number of inserted documents
        """
        if self._return:
            return 0
        
        if not documents:
            return 0
        
        try:
            operations = [InsertOne(doc) for doc in documents]
            result = await self._db[table][TgClient.ID].bulk_write(operations)
            return result.inserted_count
        except PyMongoError as e:
            self._log_error("BULK_INSERT", e)
            return 0
    
    async def bulk_update(self, table: str, updates: List[tuple]) -> int:
        """
        Bulk update documents using (filter, update_data) tuples
        
        Args:
            table: Table name
            updates: List of (filter_dict, update_dict) tuples
        
        Returns:
            Number of modified documents
        """
        if self._return:
            return 0
        
        if not updates:
            return 0
        
        try:
            operations = [
                UpdateOne(filter_dict, {"$set": update_dict})
                for filter_dict, update_dict in updates
            ]
            result = await self._db[table][TgClient.ID].bulk_write(operations)
            return result.modified_count
        except PyMongoError as e:
            self._log_error("BULK_UPDATE", e)
            return 0
    
    async def bulk_delete(self, table: str, filters: List[dict]) -> int:
        """
        Bulk delete documents
        
        Args:
            table: Table name
            filters: List of filter dictionaries
        
        Returns:
            Number of deleted documents
        """
        if self._return:
            return 0
        
        if not filters:
            return 0
        
        try:
            operations = [DeleteOne(filter_dict) for filter_dict in filters]
            result = await self._db[table][TgClient.ID].bulk_write(operations)
            return result.deleted_count
        except PyMongoError as e:
            self._log_error("BULK_DELETE", e)
            return 0
    
    async def bulk_upsert(self, table: str, documents: List[tuple]) -> int:
        """
        Bulk upsert documents using (filter, update_data) tuples
        
        Args:
            table: Table name
            documents: List of (filter_dict, update_dict) tuples
        
        Returns:
            Number of upserted documents
        """
        if self._return:
            return 0
        
        if not documents:
            return 0
        
        try:
            operations = [
                UpdateOne(filter_dict, {"$set": update_dict}, upsert=True)
                for filter_dict, update_dict in documents
            ]
            result = await self._db[table][TgClient.ID].bulk_write(operations)
            return result.upserted_count + result.modified_count
        except PyMongoError as e:
            self._log_error("BULK_UPSERT", e)
            return 0
    
    async def bulk_replace(self, table: str, documents: List[tuple]) -> int:
        """
        Bulk replace documents using (filter, replacement) tuples
        
        Args:
            table: Table name
            documents: List of (filter_dict, replacement_dict) tuples
        
        Returns:
            Number of replaced documents
        """
        if self._return:
            return 0
        
        if not documents:
            return 0
        
        try:
            from pymongo import ReplaceOne
            operations = [
                ReplaceOne(filter_dict, replacement)
                for filter_dict, replacement in documents
            ]
            result = await self._db[table][TgClient.ID].bulk_write(operations)
            return result.modified_count
        except PyMongoError as e:
            self._log_error("BULK_REPLACE", e)
            return 0
    
    async def bulk_mixed_operations(self, table: str, operations: list) -> dict:
        """
        Execute mixed bulk operations
        
        Args:
            table: Table name
            operations: List of pymongo operation objects
        
        Returns:
            Dictionary with operation results
        """
        if self._return:
            return {}
        
        if not operations:
            return {}
        
        try:
            result = await self._db[table][TgClient.ID].bulk_write(operations)
            return {
                "inserted_count": result.inserted_count,
                "modified_count": result.modified_count,
                "deleted_count": result.deleted_count,
                "upserted_count": result.upserted_count,
            }
        except PyMongoError as e:
            self._log_error("BULK_MIXED_OPERATIONS", e)
            return {}
    
    async def close(self):
        """Cleanup bulk operations repository"""
        pass
