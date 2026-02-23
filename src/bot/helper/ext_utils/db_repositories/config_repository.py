"""
Config Repository - Handles all configuration storage
Manages deploy config, bot settings, aria2, qbittorrent, and file storage
"""

from aiofiles import open as aiopen
from aiofiles.os import path as aiopath
from importlib import import_module
from pymongo.errors import PyMongoError

from bot import LOGGER, qbit_options
from bot.core.telegram_manager import TgClient
from . import BaseDbRepository


class ConfigRepository(BaseDbRepository):
    """Manages configuration and settings in database"""
    
    async def update_deploy_config(self) -> bool:
        """Update deployment configuration from config module"""
        if self._return:
            return False
        
        try:
            settings = import_module("config")
            config_file = {
                key: value.strip() if isinstance(value, str) else value
                for key, value in vars(settings).items()
                if not key.startswith("__")
            }
            await self._db.settings.deployConfig.replace_one(
                {"_id": TgClient.ID}, config_file, upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_DEPLOY_CONFIG", e)
            return False
    
    async def update_config(self, config_dict: dict) -> bool:
        """Update bot configuration"""
        if self._return:
            return False
        
        try:
            await self._db.settings.config.update_one(
                {"_id": TgClient.ID}, {"$set": config_dict}, upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_CONFIG", e)
            return False
    
    async def get_config(self) -> dict:
        """Get current bot configuration"""
        if self._return:
            return {}
        
        try:
            config = await self._db.settings.config.find_one({"_id": TgClient.ID})
            return config if config else {}
        except PyMongoError as e:
            self._log_error("GET_CONFIG", e)
            return {}
    
    async def update_aria2(self, key: str, value) -> bool:
        """Update aria2c setting"""
        if self._return:
            return False
        
        try:
            await self._db.settings.aria2c.update_one(
                {"_id": TgClient.ID}, {"$set": {key: value}}, upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_ARIA2", e)
            return False
    
    async def update_qbittorrent(self, key: str, value) -> bool:
        """Update qBittorrent setting"""
        if self._return:
            return False
        
        try:
            await self._db.settings.qbittorrent.update_one(
                {"_id": TgClient.ID}, {"$set": {key: value}}, upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_QBITTORRENT", e)
            return False
    
    async def save_qbit_settings(self) -> bool:
        """Save all qBittorrent settings"""
        if self._return:
            return False
        
        try:
            await self._db.settings.qbittorrent.update_one(
                {"_id": TgClient.ID}, {"$set": qbit_options}, upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("SAVE_QBIT_SETTINGS", e)
            return False
    
    async def update_private_file(self, path: str) -> bool:
        """Store or delete private file (config.py, etc.)"""
        if self._return:
            return False
        
        try:
            db_path = path.replace(".", "__")
            
            if await aiopath.exists(path):
                # Store file
                async with aiopen(path, "rb+") as pf:
                    pf_bin = await pf.read()
                await self._db.settings.files.update_one(
                    {"_id": TgClient.ID}, {"$set": {db_path: pf_bin}}, upsert=True
                )
                # If it's config.py, also update deploy config
                if path == "config.py":
                    await self.update_deploy_config()
            else:
                # Delete file
                await self._db.settings.files.update_one(
                    {"_id": TgClient.ID}, {"$unset": {db_path: ""}}, upsert=True
                )
            
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_PRIVATE_FILE", e)
            return False
        except Exception as e:
            LOGGER.error(f"Error updating private file {path}: {e}")
            return False
    
    async def update_nzb_config(self) -> bool:
        """Update SABnzbd configuration"""
        if self._return:
            return False
        
        try:
            async with aiopen("sabnzbd/SABnzbd.ini", "rb+") as pf:
                nzb_conf = await pf.read()
            await self._db.settings.nzb.replace_one(
                {"_id": TgClient.ID}, {"SABnzbd__ini": nzb_conf}, upsert=True
            )
            return True
        except PyMongoError as e:
            self._log_error("UPDATE_NZB_CONFIG", e)
            return False
        except Exception as e:
            LOGGER.error(f"Error updating NZB config: {e}")
            return False
    
    async def close(self):
        """Cleanup config repository"""
        pass
