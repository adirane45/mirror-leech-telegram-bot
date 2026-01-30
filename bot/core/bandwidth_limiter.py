# Bandwidth Limiting Module
# Control download and upload speeds
# Supports global and per-task limits
# Modified by: justadi

from typing import Optional, Dict
from asyncio import Lock

from .. import LOGGER, task_dict, task_dict_lock


class BandwidthLimiter:
    """
    Manages global and per-task bandwidth limits
    """
    
    # Global limits in bytes per second
    global_download_limit: Optional[int] = None  # None = unlimited
    global_upload_limit: Optional[int] = None
    
    # Per-task limits
    task_limits: Dict[str, dict] = {}
    
    # Lock for thread safety
    _lock = Lock()
    
    @classmethod
    async def set_global_download_limit(cls, limit_mbps: Optional[float]) -> bool:
        """
        Set global download speed limit
        
        Args:
            limit_mbps: Speed limit in Mbps (None = unlimited)
            
        Returns:
            True if set successfully
        """
        try:
            async with cls._lock:
                if limit_mbps is None:
                    cls.global_download_limit = None
                    LOGGER.info("Global download limit removed")
                else:
                    # Convert Mbps to bytes per second
                    cls.global_download_limit = int(limit_mbps * 1_000_000 / 8)
                    LOGGER.info(f"Global download limit set to {limit_mbps} Mbps")
            return True
        except Exception as e:
            LOGGER.error(f"Error setting global download limit: {e}")
            return False
    
    @classmethod
    async def set_global_upload_limit(cls, limit_mbps: Optional[float]) -> bool:
        """
        Set global upload speed limit
        
        Args:
            limit_mbps: Speed limit in Mbps (None = unlimited)
            
        Returns:
            True if set successfully
        """
        try:
            async with cls._lock:
                if limit_mbps is None:
                    cls.global_upload_limit = None
                    LOGGER.info("Global upload limit removed")
                else:
                    # Convert Mbps to bytes per second
                    cls.global_upload_limit = int(limit_mbps * 1_000_000 / 8)
                    LOGGER.info(f"Global upload limit set to {limit_mbps} Mbps")
            return True
        except Exception as e:
            LOGGER.error(f"Error setting global upload limit: {e}")
            return False
    
    @classmethod
    async def set_task_limit(
        cls,
        task_id: str,
        download_limit: Optional[float] = None,
        upload_limit: Optional[float] = None
    ) -> bool:
        """
        Set speed limits for a specific task
        
        Args:
            task_id: Task ID
            download_limit: Download speed in Mbps
            upload_limit: Upload speed in Mbps
            
        Returns:
            True if set successfully
        """
        try:
            async with cls._lock:
                if task_id not in cls.task_limits:
                    cls.task_limits[task_id] = {}
                
                if download_limit is not None:
                    cls.task_limits[task_id]["download"] = int(download_limit * 1_000_000 / 8)
                
                if upload_limit is not None:
                    cls.task_limits[task_id]["upload"] = int(upload_limit * 1_000_000 / 8)
                
                LOGGER.info(f"Limits set for task {task_id}: DL={download_limit}Mbps, UL={upload_limit}Mbps")
            return True
        except Exception as e:
            LOGGER.error(f"Error setting task limits: {e}")
            return False
    
    @classmethod
    async def get_effective_limit(
        cls,
        task_id: str,
        limit_type: str  # 'download' or 'upload'
    ) -> Optional[int]:
        """
        Get the effective speed limit for a task
        Considers both global and task-specific limits
        
        Args:
            task_id: Task ID
            limit_type: 'download' or 'upload'
            
        Returns:
            Speed limit in bytes per second, or None if unlimited
        """
        try:
            async with cls._lock:
                global_limit = (
                    cls.global_download_limit
                    if limit_type == "download"
                    else cls.global_upload_limit
                )
                
                task_limit = None
                if task_id in cls.task_limits:
                    task_limit = cls.task_limits[task_id].get(limit_type)
                
                # Return the most restrictive limit
                if global_limit is None:
                    return task_limit
                if task_limit is None:
                    return global_limit
                return min(global_limit, task_limit)
        except Exception as e:
            LOGGER.error(f"Error getting effective limit: {e}")
            return None
    
    @classmethod
    async def remove_task_limit(cls, task_id: str) -> bool:
        """Remove speed limits for a task"""
        try:
            async with cls._lock:
                if task_id in cls.task_limits:
                    del cls.task_limits[task_id]
                    LOGGER.info(f"Limits removed for task {task_id}")
            return True
        except Exception as e:
            LOGGER.error(f"Error removing task limits: {e}")
            return False
    
    @classmethod
    async def get_stats(cls) -> dict:
        """Get current bandwidth limiting statistics"""
        try:
            async with cls._lock:
                return {
                    "global_download_limit_mbps": (
                        cls.global_download_limit * 8 / 1_000_000
                        if cls.global_download_limit else None
                    ),
                    "global_upload_limit_mbps": (
                        cls.global_upload_limit * 8 / 1_000_000
                        if cls.global_upload_limit else None
                    ),
                    "task_limits_count": len(cls.task_limits),
                    "limited_tasks": list(cls.task_limits.keys())
                }
        except Exception as e:
            LOGGER.error(f"Error getting bandwidth stats: {e}")
            return {}
