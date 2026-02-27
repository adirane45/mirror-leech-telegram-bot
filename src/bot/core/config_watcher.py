"""
Zero-Downtime Configuration Reload System
Monitors config files and broadcasts changes to all workers via Redis pubsub
"""

import asyncio
from logging import getLogger
from pathlib import Path
from typing import Dict, Any, Optional, Set
from datetime import datetime
import os

LOGGER = getLogger(__name__)


class ConfigWatcher:
    """
    Watch configuration files for changes and trigger hot-reloads
    """
    
    def __init__(self):
        self.watched_files: Set[Path] = set()
        self.file_timestamps: Dict[Path, float] = {}
        self.is_running = False
        self._watcher_task: Optional[asyncio.Task] = None
        self.check_interval = 5  # seconds
        
    def add_watch(self, file_path: str):
        """Add a file to watch for changes"""
        path = Path(file_path)
        if path.exists():
            self.watched_files.add(path)
            self.file_timestamps[path] = path.stat().st_mtime
            LOGGER.info(f"👁️ Watching config file: {path}")
        else:
            LOGGER.warning(f"Config file not found: {path}")
    
    async def _check_file_changes(self) -> Dict[Path, float]:
        """Check all watched files for modifications"""
        changed_files = {}
        
        for file_path in self.watched_files:
            try:
                if not file_path.exists():
                    LOGGER.warning(f"Watched file disappeared: {file_path}")
                    continue
                
                current_mtime = file_path.stat().st_mtime
                last_mtime = self.file_timestamps.get(file_path, 0)
                
                if current_mtime > last_mtime:
                    changed_files[file_path] = current_mtime
                    LOGGER.info(f"🔄 Config file changed: {file_path}")
                    
            except Exception as e:
                LOGGER.error(f"Error checking {file_path}: {e}")
        
        return changed_files
    
    async def _validate_env_file(self, file_path: Path) -> tuple[bool, Optional[Dict[str, str]]]:
        """Validate .env file syntax and parse"""
        try:
            new_config = {}
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        new_config[key.strip()] = value.strip().strip('"').strip("'")
            
            return True, new_config
        except Exception as e:
            LOGGER.error(f"Failed to validate {file_path}: {e}")
            return False, None
    
    async def _broadcast_config_change(self, file_path: Path, new_config: Dict[str, str]):
        """Broadcast configuration change to all workers via Redis"""
        try:
            from .redis_manager import redis_client
            
            if not redis_client.is_connected():
                LOGGER.warning("Redis not connected, skipping broadcast")
                return
            
            message = {
                "timestamp": datetime.utcnow().isoformat(),
                "file": str(file_path),
                "config": new_config,
                "action": "reload"
            }
            
            await redis_client.publish("config:reload", message)
            LOGGER.info(f"📡 Broadcasted config reload: {file_path.name}")
            
        except Exception as e:
            LOGGER.warning(f"Redis broadcast failed: {e}")
    
    async def _reload_config(self, file_path: Path):
        """Handle config file reload"""
        try:
            # Validate new config
            is_valid, new_config = await self._validate_env_file(file_path)
            
            if not is_valid:
                LOGGER.error(f"❌ Invalid config in {file_path}, skipping reload")
                return
            
            # Update timestamp
            self.file_timestamps[file_path] = file_path.stat().st_mtime
            
            # Reload Config class
            from .config_manager import Config
            
            # Store old values for rollback
            old_values = {}
            for key in new_config:
                if hasattr(Config, key):
                    old_values[key] = getattr(Config, key)
            
            # Apply new values
            for key, value in new_config.items():
                try:
                    # Type conversion
                    if hasattr(Config, key):
                        old_val = getattr(Config, key)
                        if isinstance(old_val, bool):
                            value = value.lower() in ('true', '1', 'yes')
                        elif isinstance(old_val, int):
                            value = int(value)
                        elif isinstance(old_val, float):
                            value = float(value)
                    
                    setattr(Config, key, value)
                except Exception as e:
                    LOGGER.error(f"Failed to set {key}={value}: {e}")
            
            # Broadcast to all workers
            await self._broadcast_config_change(file_path, new_config)
            
            LOGGER.info(f"✅ Config reloaded from {file_path.name}")
            
        except Exception as e:
            LOGGER.error(f"Config reload failed: {e}", exc_info=True)
    
    async def _watch_loop(self):
        """Main watch loop"""
        LOGGER.info("🔄 Config watcher started")
        
        while self.is_running:
            try:
                changed_files = await self._check_file_changes()
                
                for file_path, new_mtime in changed_files.items():
                    LOGGER.info(f"🔧 Reloading config: {file_path.name}")
                    await self._reload_config(file_path)
                    await asyncio.sleep(1)  # Brief delay between reloads
                
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                LOGGER.error(f"Error in watch loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def start(self):
        """Start watching config files"""
        if self.is_running:
            LOGGER.warning("Config watcher already running")
            return
        
        self.is_running = True
        self._watcher_task = asyncio.create_task(self._watch_loop())
        LOGGER.info("✅ Config watcher enabled")
    
    async def stop(self):
        """Stop watching config files"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._watcher_task:
            self._watcher_task.cancel()
            try:
                await self._watcher_task
            except asyncio.CancelledError:
                pass
        
        LOGGER.info("⏹️ Config watcher stopped")


# Global instance
config_watcher = ConfigWatcher()
