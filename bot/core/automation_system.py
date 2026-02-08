"""
Automation System - Initialization and integration of all automation features
Coordinates client selection, auto-recovery, worker autoscaling, and thumbnail management

Enhanced by: justadi
Date: February 8, 2026
"""

import asyncio
from typing import Optional, Callable

from .. import LOGGER
from .client_selector import client_selector
from .auto_recovery_handler import auto_recovery, RecoverySeverity
from .worker_autoscaler import worker_autoscaler
from .thumbnail_manager import thumbnail_manager


class AutomationSystem:
    """Singleton automation system coordinator"""
    
    _instance: Optional['AutomationSystem'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._enabled = False
        LOGGER.info("✅ Automation System initialized")
    
    @classmethod
    def get_instance(cls) -> 'AutomationSystem':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    # ==================== INITIALIZATION ====================
    
    async def enable_all(
        self,
        enable_client_selection: bool = True,
        enable_auto_recovery: bool = True,
        enable_worker_autoscaling: bool = True,
        enable_thumbnails: bool = True,
        notify_callback: Optional[Callable] = None,
    ) -> bool:
        """
        Enable all automation features
        
        Args:
            enable_client_selection: Enable intelligent client selection
            enable_auto_recovery: Enable auto-recovery with health checks
            enable_worker_autoscaling: Enable worker autoscaling
            enable_thumbnails: Enable smart thumbnail caching
            notify_callback: Callback for admin notifications
        """
        try:
            LOGGER.info("🚀 Initializing Automation System...")
            
            # 1. Client Selector (always ready, no async init needed)
            if enable_client_selection:
                LOGGER.info("✓ Client Selection enabled")
            
            # 2. Auto-Recovery Handler
            if enable_auto_recovery:
                await auto_recovery.enable(notify_callback=notify_callback)
                self._setup_recovery_actions()
                LOGGER.info("✓ Auto-Recovery enabled")
            
            # 3. Worker Autoscaler
            if enable_worker_autoscaling:
                await worker_autoscaler.enable(check_interval=30.0)
                LOGGER.info("✓ Worker Autoscaler enabled")
            
            # 4. Thumbnail Manager (ready, no init needed)
            if enable_thumbnails:
                LOGGER.info("✓ Thumbnail Manager enabled")
            
            self._enabled = True
            LOGGER.info("✅ Automation System ready!")
            return True
            
        except Exception as e:
            LOGGER.error(f"❌ Failed to initialize Automation System: {e}", exc_info=True)
            return False
    
    def _setup_recovery_actions(self):
        """Register recovery actions for components"""
        
        # Redis recovery
        auto_recovery.register_recovery_action(
            component_id="redis",
            component_name="Redis Cache",
            severity=RecoverySeverity.AUTO_RESTART,
            action_fn=self._recover_redis,
            max_attempts=3,
        )
        
        # Aria2 recovery
        auto_recovery.register_recovery_action(
            component_id="aria2",
            component_name="Aria2 Client",
            severity=RecoverySeverity.AUTO_RESTART,
            action_fn=self._recover_aria2,
            max_attempts=3,
        )
        
        # qBittorrent recovery
        auto_recovery.register_recovery_action(
            component_id="qbittorrent",
            component_name="qBittorrent Client",
            severity=RecoverySeverity.AUTO_RESTART,
            action_fn=self._recover_qbittorrent,
            max_attempts=3,
        )
        
        # Database recovery
        auto_recovery.register_recovery_action(
            component_id="mongodb",
            component_name="MongoDB Database",
            severity=RecoverySeverity.NOTIFY_ADMIN,
            action_fn=self._recover_mongodb,
            max_attempts=2,
        )
        
        LOGGER.info("📋 Recovery actions registered for 4 components")
    
    # ==================== RECOVERY FUNCTIONS ====================
    
    async def _recover_redis(self) -> bool:
        """Recover Redis service"""
        try:
            import subprocess
            LOGGER.warning("🔄 Attempting Redis recovery...")
            
            # Try to restart redis container
            result = subprocess.run(
                ["docker-compose", "restart", "redis"],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                await asyncio.sleep(3)  # Wait for Redis to come up
                LOGGER.info("✅ Redis recovered successfully")
                return True
            else:
                LOGGER.error(f"Redis restart failed: {result.stderr.decode()}")
                return False
        except Exception as e:
            LOGGER.error(f"Redis recovery error: {e}")
            return False
    
    async def _recover_aria2(self) -> bool:
        """Recover Aria2 service"""
        try:
            LOGGER.warning("🔄 Attempting Aria2 recovery...")
            import subprocess
            
            result = subprocess.run(
                ["docker-compose", "restart", "aria2"],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                await asyncio.sleep(2)
                LOGGER.info("✅ Aria2 recovered successfully")
                return True
            else:
                LOGGER.error(f"Aria2 restart failed: {result.stderr.decode()}")
                return False
        except Exception as e:
            LOGGER.error(f"Aria2 recovery error: {e}")
            return False
    
    async def _recover_qbittorrent(self) -> bool:
        """Recover qBittorrent service"""
        try:
            LOGGER.warning("🔄 Attempting qBittorrent recovery...")
            import subprocess
            
            result = subprocess.run(
                ["docker-compose", "restart", "qbittorrent"],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                await asyncio.sleep(2)
                LOGGER.info("✅ qBittorrent recovered successfully")
                return True
            else:
                LOGGER.error(f"qBittorrent restart failed: {result.stderr.decode()}")
                return False
        except Exception as e:
            LOGGER.error(f"qBittorrent recovery error: {e}")
            return False
    
    async def _recover_mongodb(self) -> bool:
        """Recover MongoDB service"""
        try:
            LOGGER.warning("🔄 Attempting MongoDB recovery...")
            import subprocess
            
            result = subprocess.run(
                ["docker-compose", "restart", "mongodb"],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                await asyncio.sleep(5)  # MongoDB needs more time
                LOGGER.info("✅ MongoDB recovered successfully")
                return True
            else:
                LOGGER.error(f"MongoDB restart failed: {result.stderr.decode()}")
                return False
        except Exception as e:
            LOGGER.error(f"MongoDB recovery error: {e}")
            return False
    
    # ==================== PUBLIC API ====================
    
    async def disable_all(self) -> bool:
        """Disable all automation features"""
        await worker_autoscaler.disable()
        await auto_recovery.disable()
        self._enabled = False
        LOGGER.info("❌ Automation System disabled")
        return True
    
    def is_enabled(self) -> bool:
        """Check if automation system is enabled"""
        return self._enabled
    
    async def get_full_status(self) -> dict:
        """Get comprehensive status of all automation features"""
        return {
            "enabled": self._enabled,
            "client_selector": client_selector.get_status(),
            "auto_recovery": auto_recovery.get_status(),
            "worker_autoscaler": await worker_autoscaler.get_status(),
            "thumbnail_manager": thumbnail_manager.get_status(),
        }
    
    async def trigger_cleanup(self) -> dict:
        """Manually trigger cleanup operations"""
        results = {
            "expired_thumbnails": await thumbnail_manager.cleanup_expired(),
            "timestamp": __import__('datetime').datetime.now().isoformat(),
        }
        LOGGER.info(f"🧹 Cleanup completed: {results}")
        return results


# Global instance
automation_system = AutomationSystem.get_instance()
