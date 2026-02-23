"""
Indexed Repository - Handles indexed data storage
Manages indexed documents for efficient searching and filtering
"""

from typing import List
from pymongo.errors import PyMongoError
from pymongo import ASCENDING, DESCENDING

from bot import LOGGER
from bot.core.telegram_manager import TgClient
from . import BaseDbRepository


class IndexedRepository(BaseDbRepository):
    """Manages indexed data in database"""
    
    async def create_index(self, table: str, field: str, direction: int = ASCENDING) -> bool:
        """
        Create an index on a field
        
        Args:
            table: Table name
            field: Field name to index
            direction: ASCENDING or DESCENDING
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            await self._db[table][TgClient.ID].create_index([(field, direction)])
            return True
        except PyMongoError as e:
            self._log_error("CREATE_INDEX", e)
            return False
    
    async def create_compound_index(self, table: str, fields: List[tuple]) -> bool:
        """
        Create a compound index on multiple fields
        
        Args:
            table: Table name
            fields: List of (field, direction) tuples
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            await self._db[table][TgClient.ID].create_index(fields)
            return True
        except PyMongoError as e:
            self._log_error("CREATE_COMPOUND_INDEX", e)
            return False
    
    async def drop_index(self, table: str, index_name: str) -> bool:
        """
        Drop an index
        
        Args:
            table: Table name
            index_name: Index name to drop
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        try:
            await self._db[table][TgClient.ID].drop_index(index_name)
            return True
        except PyMongoError as e:
            self._log_error("DROP_INDEX", e)
            return False
    
    async def get_indexes(self, table: str) -> dict:
        """Get all indexes for a table"""
        if self._return:
            return {}
        
        try:
            indexes = await self._db[table][TgClient.ID].index_information()
            return indexes
        except PyMongoError as e:
            self._log_error("GET_INDEXES", e)
            return {}
    
    async def search(self, table: str, query: dict, limit: int = 100) -> list:
        """
        Search documents with query
        
        Args:
            table: Table name
            query: MongoDB query
            limit: Maximum results to return
        
        Returns:
            List of matching documents
        """
        if self._return:
            return []
        
        try:
            results = []
            async for doc in self._db[table][TgClient.ID].find(query).limit(limit):
                results.append(doc)
            return results
        except PyMongoError as e:
            self._log_error("SEARCH", e)
            return []
    
    async def count_documents(self, table: str, query: dict = None) -> int:
        """Count documents matching query"""
        if self._return:
            return 0
        
        query = query or {}
        
        try:
            count = await self._db[table][TgClient.ID].count_documents(query)
            return count
        except PyMongoError as e:
            self._log_error("COUNT_DOCUMENTS", e)
            return 0
    
    async def distinct(self, table: str, field: str, query: dict = None) -> list:
        """Get distinct values for a field"""
        if self._return:
            return []
        
        query = query or {}
        
        try:
            values = await self._db[table][TgClient.ID].distinct(field, query)
            return values
        except PyMongoError as e:
            self._log_error("DISTINCT", e)
            return []
    
    async def aggregate(self, table: str, pipeline: list) -> list:
        """
        Run aggregation pipeline
        
        Args:
            table: Table name
            pipeline: Aggregation pipeline
        
        Returns:
            Aggregation results
        """
        if self._return:
            return []
        
        try:
            results = []
            async for doc in self._db[table][TgClient.ID].aggregate(pipeline):
                results.append(doc)
            return results
        except PyMongoError as e:
            self._log_error("AGGREGATE", e)
            return []
    
    async def close(self):
        """Cleanup indexed repository"""
        pass
