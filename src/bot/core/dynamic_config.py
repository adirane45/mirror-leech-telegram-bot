"""
Dynamic Configuration Reloading with Zero Downtime

Implements:
- File watching for config changes
- Validation before applying changes
- Redis pubsub for cluster-wide updates
- Rollback on validation failure
- Audit logging of all changes
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from pathlib import Path
import importlib

from .. import LOGGER
from .config_manager import Config
from .redis_manager import redis_client


@dataclass
class ConfigChange:
    """Represents a configuration change"""
    key: str
    old_value: Any
    new_value: Any
    timestamp: datetime
    source: str = "manual"
    validated: bool = False


class ConfigValidator:
    """Validate configuration changes"""
    
    # Define valid value types and ranges
    VALIDATION_RULES = {
        "AUTHORIZED_CHATS": (str, lambda x: len(x) > 0),
        "OWNER_ID": (int, lambda x: x > 0),
        "BOT_TOKEN": (str, lambda x: len(x) > 20),
        "DOWNLOAD_LIMITS": (int, lambda x: x > 0),
        "UPLOAD_BUCKET": (str, lambda x: len(x) > 0),
        "FILE_CACHE_TTL_DAYS": (int, lambda x: 1 <= x <= 365),
        "STREAM_LINK_TTL_SECONDS": (int, lambda x: 60 <= x <= 3600),
        "ADMIN_TOKEN_TTL_SECONDS": (int, lambda x: 60 <= x <= 3600),
    }
    
    @staticmethod
    def validate_change(key: str, new_value: Any) -> Optional[str]:
        """
        Validate a config change
        
        Returns:
            None if valid, error message if invalid
        """
        if key not in ConfigValidator.VALIDATION_RULES:
            return None  # Unknown key is allowed
        
        expected_type, validator = ConfigValidator.VALIDATION_RULES[key]
        
        # Type check
        if not isinstance(new_value, expected_type):
            return f"Invalid type for {key}: expected {expected_type.__name__}, got {type(new_value).__name__}"
        
        # Value check
        try:
            if not validator(new_value):
                return f"Invalid value for {key}: {new_value}"
        except Exception as e:
            return f"Validation failed for {key}: {e}"
        
        return None


class DynamicConfig:
    """Manage dynamic configuration reloading"""
    
    def __init__(self):
        self.enabled = bool(getattr(Config, "ENABLE_HOT_RELOAD", True))
        self.config_file_path = getattr(Config, "CONFIG_FILE_PATH", "config/main_config.py")
        self.env_file_path = getattr(Config, "ENV_FILE_PATH", ".env")
        
        self.current_config: Dict[str, Any] = {}
        self.change_history: List[ConfigChange] = []
        self.listeners: List[Callable] = []
        self._watch_task: Optional[asyncio.Task] = None
        self._last_modified: Optional[float] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> bool:
        """Initialize dynamic config"""
        if not self.enabled:
            LOGGER.warning("Dynamic config reloading is disabled")
            return False
        
        # Load initial config
        self._load_current_config()
        LOGGER.info("Dynamic config initialized")
        return True
    
    async def start_watching(self) -> None:
        """Start watching config files for changes"""
        if not self.enabled:
            return
        
        self._watch_task = asyncio.create_task(self._watch_loop())
        LOGGER.info("Config file watcher started")
    
    async def stop_watching(self) -> None:
        """Stop watching config files"""
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
        LOGGER.info("Config file watcher stopped")
    
    async def _watch_loop(self) -> None:
        """Watch for config file changes"""
        while True:
            try:
                # Check if files were modified
                modified = False
                
                for path in [self.config_file_path, self.env_file_path]:
                    if os.path.exists(path):
                        mtime = os.path.getmtime(path)
                        if self._last_modified is None or mtime > self._last_modified:
                            modified = True
                            self._last_modified = mtime
                
                if modified:
                    LOGGER.info("Config file change detected, reloading...")
                    await self.reload_config()
                
                await asyncio.sleep(5)  # Poll every 5 seconds
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                LOGGER.error(f"Config watch error: {e}")
                await asyncio.sleep(5)
    
    def _load_current_config(self) -> None:
        """Load current configuration from Config object"""
        # Get all attributes that look like config settings
        for attr in dir(Config):
            if attr.isupper() and not attr.startswith('_'):
                try:
                    value = getattr(Config, attr)
                    if not callable(value):
                        self.current_config[attr] = value
                except Exception:
                    pass
    
    async def reload_config(self) -> bool:
        """Reload configuration from files"""
        async with self._lock:
            try:
                # Reload the config module
                import bot.core.config_manager as cm
                importlib.reload(cm)
                
                # Get new config
                new_config = {}
                for attr in dir(cm.Config):
                    if attr.isupper() and not attr.startswith('_'):
                        try:
                            value = getattr(cm.Config, attr)
                            if not callable(value):
                                new_config[attr] = value
                        except Exception:
                            pass
                
                # Detect changes
                changes = []
                for key in new_config:
                    if key not in self.current_config or self.current_config[key] != new_config[key]:
                        changes.append((
                            key,
                            self.current_config.get(key),
                            new_config[key]
                        ))
                
                if not changes:
                    LOGGER.info("No configuration changes detected")
                    return True
                
                # Validate changes
                for key, old_val, new_val in changes:
                    error = ConfigValidator.validate_change(key, new_val)
                    if error:
                        LOGGER.error(f"Config validation failed: {error}")
                        return False
                
                # Apply changes
                for key, old_val, new_val in changes:
                    self.current_config[key] = new_val
                    setattr(cm.Config, key, new_val)
                    
                    change = ConfigChange(
                        key=key,
                        old_value=old_val,
                        new_value=new_val,
                        timestamp=datetime.now(timezone.utc),
                    )
                    self.change_history.append(change)
                    
                    LOGGER.info(f"Config updated: {key} = {new_val}")
                
                # Notify listeners
                await self._notify_listeners(changes)
                
                # Broadcast to cluster
                await self._broadcast_changes(changes)
                
                return True
            
            except Exception as e:
                LOGGER.error(f"Failed to reload config: {e}")
                return False
    
    async def set_config(self, key: str, value: Any) -> bool:
        """Set a configuration value"""
        async with self._lock:
            # Validate
            error = ConfigValidator.validate_change(key, value)
            if error:
                LOGGER.error(f"Config validation failed: {error}")
                return False
            
            # Get old value
            old_value = self.current_config.get(key)
            
            # Set new value
            self.current_config[key] = value
            setattr(Config, key, value)
            
            # Record change
            change = ConfigChange(
                key=key,
                old_value=old_value,
                new_value=value,
                timestamp=datetime.now(timezone.utc),
                source="api",
            )
            self.change_history.append(change)
            
            LOGGER.info(f"Config set via API: {key} = {value}")
            
            # Notify listeners
            await self._notify_listeners([(key, old_value, value)])
            
            # Broadcast to cluster
            await self._broadcast_changes([(key, old_value, value)])
            
            return True
    
    async def _notify_listeners(self, changes: list) -> None:
        """Notify registered listeners of changes"""
        for listener in self.listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(changes)
                else:
                    listener(changes)
            except Exception as e:
                LOGGER.error(f"Config listener error: {e}")
    
    async def _broadcast_changes(self, changes: list) -> None:
        """Broadcast config changes to cluster via Redis pubsub"""
        if not redis_client.is_enabled:
            return
        
        try:
            for key, old_val, new_val in changes:
                message = {
                    "action": "config_change",
                    "key": key,
                    "old_value": str(old_val),
                    "new_value": str(new_val),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await redis_client.publish("config_updates", message)
        except Exception as e:
            LOGGER.error(f"Failed to broadcast config changes: {e}")
    
    def add_listener(self, callback: Callable) -> None:
        """Register a listener for config changes"""
        self.listeners.append(callback)
    
    def get_change_history(self, limit: int = 100) -> list:
        """Get recent configuration changes"""
        return [
            {
                "key": c.key,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "timestamp": c.timestamp.isoformat(),
                "source": c.source,
            }
            for c in self.change_history[-limit:]
        ]


# Global instance
dynamic_config = DynamicConfig()
