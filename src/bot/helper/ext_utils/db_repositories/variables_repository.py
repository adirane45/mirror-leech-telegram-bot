"""
Variables Repository - Handles global variables and configuration storage
Manages bot-wide settings and persistent variables
"""

from pymongo.errors import PyMongoError

from bot import LOGGER
from bot.core.telegram_manager import TgClient
from . import BaseDbRepository


class VariablesRepository(BaseDbRepository):
    """Manages global variables in database"""
    
    async def update_variable(self, key: str, value, table: str = None) -> bool:
        """
        Update a global variable
        
        Args:
            key: Variable key
            value: Variable value
            table: Optional table name (defaults to variables)
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        table = table or "variables"
        
        try:
            await self._db[table][TgClient.ID].replace_one(
                {"_id": key}, {"_id": key, "value": value}, upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_VARIABLE", e)
            return False
    
    async def delete_variable(self, key: str, table: str = None) -> bool:
        """
        Delete a global variable
        
        Args:
            key: Variable key
            table: Optional table name (defaults to variables)
        
        Returns:
            True if successful, False otherwise
        """
        if self._return:
            return False
        
        table = table or "variables"
        
        try:
            result = await self._db[table][TgClient.ID].delete_one({"_id": key})
            return result.deleted_count > 0
        except PyMongoError as e:
            self._log_error("DELETE_VARIABLE", e)
            return False
    
    async def get_variable(self, key: str, table: str = None):
        """Get a global variable value"""
        if self._return:
            return None
        
        table = table or "variables"
        
        try:
            var = await self._db[table][TgClient.ID].find_one({"_id": key})
            return var.get("value") if var else None
        except PyMongoError as e:
            self._log_error("GET_VARIABLE", e)
            return None
    
    async def get_all_variables(self, table: str = None) -> dict:
        """Get all variables from a table"""
        if self._return:
            return {}
        
        table = table or "variables"
        
        try:
            vars_data = {}
            async for var in self._db[table][TgClient.ID].find({}):
                key = var.get("_id")
                if key:
                    vars_data[key] = var.get("value")
            return vars_data
        except PyMongoError as e:
            self._log_error("GET_ALL_VARIABLES", e)
            return {}
    
    async def update_multiple_variables(self, variables: dict, table: str = None) -> bool:
        """
        Update multiple variables at once
        
        Args:
            variables: Dictionary of key-value pairs to update
            table: Optional table name (defaults to variables)
        
        Returns:
            True if all successful, False otherwise
        """
        if self._return:
            return False
        
        table = table or "variables"
        success = True
        
        try:
            for key, value in variables.items():
                await self._db[table][TgClient.ID].replace_one(
                    {"_id": key}, {"_id": key, "value": value}, upsert=True
                )
        except PyMongoError as e:
            self._log_error("UPDATE_MULTIPLE_VARIABLES", e)
            success = False
        
        return success
    
    async def clear_all_variables(self, table: str = None) -> bool:
        """Clear all variables in a table"""
        if self._return:
            return False
        
        table = table or "variables"
        
        try:
            await self._db[table][TgClient.ID].delete_many({})
            return True
        except PyMongoError as e:
            self._log_error("CLEAR_ALL_VARIABLES", e)
            return False
    
    async def close(self):
        """Cleanup variables repository"""
        pass
