"""
Automation System - Initialization and integration of all automation features
Coordinates client selection, auto-recovery, worker autoscaling, and thumbnail management

Enhanced by: justadi
Date: February 8, 2026
"""

import asyncio
import importlib
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable, Optional

from .. import LOGGER
from .auto_recovery_handler import RecoverySeverity, auto_recovery

NotifyCallback = Callable[[str, RecoverySeverity, str], object | Awaitable[object]]


class AutomationSystem:
    """Singleton automation system coordinator"""

    _instance: Optional['AutomationSystem'] = None

    def __new__(cls) -> 'AutomationSystem':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
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

    @staticmethod
    def _get_config_flag(flag_name: str, default: bool) -> bool:
        try:
            config_module = importlib.import_module("bot.core.config_manager")
            config_obj = getattr(config_module, "Config", None)
            if config_obj is None:
                return default
            return bool(getattr(config_obj, flag_name, default))
        except Exception:
            return default

    # ==================== INITIALIZATION ====================

    async def enable_all(
        self,
        enable_client_selection: bool = True,
        enable_auto_recovery: bool = True,
        enable_thumbnails: bool = True,
        notify_callback: Optional[NotifyCallback] = None,
    ) -> bool:
        """
        Enable all automation features

        Args:
            enable_client_selection: Enable intelligent client selection
            enable_auto_recovery: Enable auto-recovery with health checks
            enable_thumbnails: Enable smart thumbnail caching
            notify_callback: Callback for admin notifications
        """
        try:
            LOGGER.info("🚀 Initializing Automation System...")

            # 1. Client Selector (always ready, no async init needed)
            if enable_client_selection and self._get_config_flag("ENABLE_CLIENT_SELECTION", True):
                LOGGER.info("✓ Client Selection enabled")

            # 2. Auto-Recovery Handler
            if enable_auto_recovery and self._get_config_flag("ENABLE_AUTO_RECOVERY", True):
                await auto_recovery.enable(notify_callback=notify_callback)
                self._setup_recovery_actions()
                await self._register_health_recovery_callbacks()
                LOGGER.info("✓ Auto-Recovery enabled")

            # 3. Thumbnail Manager (ready, no init needed)
            if enable_thumbnails and self._get_config_flag("ENABLE_SMART_THUMBNAILS", True):
                LOGGER.info("✓ Thumbnail Manager enabled")

            self._enabled = True
            LOGGER.info("✅ Automation System ready!")
            return True

        except Exception as e:
            LOGGER.error(f"❌ Failed to initialize Automation System: {e}", exc_info=True)
            return False

    def _setup_recovery_actions(self) -> None:
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

    async def _register_health_recovery_callbacks(self) -> None:
        """Link health monitor to auto-recovery callbacks"""
        try:
            from .health_monitor import HealthMonitor

            health_monitor = HealthMonitor.get_instance()
            if not health_monitor.is_enabled():
                return

            def _make_callback(
                component_id: str,
            ) -> Callable[[Any], Awaitable[None]]:
                async def _callback(result: Any) -> None:
                    await auto_recovery.attempt_recovery(
                        component_id,
                        error_message=result.error or "Health check failed",
                    )
                return _callback

            for component_id in ("redis", "aria2", "qbittorrent", "mongodb"):
                callback = _make_callback(component_id)
                await health_monitor.register_recovery_callback(component_id, callback)
        except Exception as e:
            LOGGER.debug(f"Health monitor recovery callback registration skipped: {e}")

    # ==================== RECOVERY FUNCTIONS ====================

    async def _recover_redis(self) -> bool:
        """Recover Redis service"""
        try:
            import subprocess
            LOGGER.warning("🔄 Attempting Redis recovery...")

            # Try to restart redis container
            result = await asyncio.to_thread(
                subprocess.run,
                ["docker-compose", "restart", "redis"],
                capture_output=True,
                timeout=30,
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

            result = await asyncio.to_thread(
                subprocess.run,
                ["docker-compose", "restart", "aria2"],
                capture_output=True,
                timeout=30,
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

            result = await asyncio.to_thread(
                subprocess.run,
                ["docker-compose", "restart", "qbittorrent"],
                capture_output=True,
                timeout=30,
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

            result = await asyncio.to_thread(
                subprocess.run,
                ["docker-compose", "restart", "mongodb"],
                capture_output=True,
                timeout=30,
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

    @staticmethod
    def _get_client_selector() -> Any:
        try:
            selector_module = importlib.import_module("bot.core.client_selector")
            return getattr(selector_module, "client_selector", None)
        except Exception:
            return None

    @staticmethod
    def _get_thumbnail_manager() -> Any:
        try:
            thumbnail_module = importlib.import_module("bot.core.thumbnail_manager")
            return getattr(thumbnail_module, "thumbnail_manager", None)
        except Exception:
            return None

    @staticmethod
    def _get_worker_autoscaler() -> Any:
        try:
            worker_module = importlib.import_module("bot.core.worker_autoscaler")
            return getattr(worker_module, "worker_autoscaler", None)
        except Exception:
            return None

    async def disable_all(self) -> bool:
        """Disable all automation features"""
        worker_autoscaler = self._get_worker_autoscaler()
        if worker_autoscaler is not None:
            await worker_autoscaler.disable()
        await auto_recovery.disable()
        self._enabled = False
        LOGGER.info("❌ Automation System disabled")
        return True

    def is_enabled(self) -> bool:
        """Check if automation system is enabled"""
        return self._enabled

    async def get_full_status(self) -> dict[str, Any]:
        """Get comprehensive status of all automation features"""
        client_selector = self._get_client_selector()
        thumbnail_manager = self._get_thumbnail_manager()
        worker_autoscaler = self._get_worker_autoscaler()

        worker_status: Any = {"available": False}
        if worker_autoscaler is not None:
            worker_status = await worker_autoscaler.get_status()

        return {
            "enabled": self._enabled,
            "client_selector": (
                client_selector.get_status() if client_selector is not None else {"available": False}
            ),
            "auto_recovery": auto_recovery.get_status(),
            "worker_autoscaler": worker_status,
            "thumbnail_manager": (
                thumbnail_manager.get_status() if thumbnail_manager is not None else {"available": False}
            ),
        }

    async def trigger_cleanup(self) -> dict[str, Any]:
        """Manually trigger cleanup operations"""
        thumbnail_manager = self._get_thumbnail_manager()
        expired_thumbnails: Any = {"available": False}
        if thumbnail_manager is not None:
            expired_thumbnails = await thumbnail_manager.cleanup_expired()

        results = {
            "expired_thumbnails": expired_thumbnails,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        LOGGER.info(f"🧹 Cleanup completed: {results}")
        return results


# Global instance
automation_system = AutomationSystem.get_instance()
