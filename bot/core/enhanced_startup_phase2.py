"""
Phase 2 Startup - Initialize Enhanced Services
Bootstraps Phase 2 infrastructure safely with error handling

Safe Innovation Path - Phase 2

Enhanced by: justadi
Date: February 5, 2026
"""

from typing import Dict
from . import LOGGER

from .logger_manager import logger_manager
from .alert_manager import alert_manager
from .backup_manager import backup_manager
from .profiler import profiler
from .recovery_manager import recovery_manager


async def initialize_phase2_services() -> Dict[str, bool]:
    """
    Initialize all Phase 2 services safely

    Returns:
        Dictionary with service initialization status
    """
    status = {
        "logger": False,
        "alerts": False,
        "backups": False,
        "profiler": False,
        "recovery": False,
    }

    # Initialize logger manager
    try:
        logger_manager.enable()
        status["logger"] = logger_manager.is_enabled
        if status["logger"]:
            LOGGER.info("✅ Logger Manager initialized")
    except Exception as e:
        LOGGER.error(f"❌ Failed to initialize Logger Manager: {e}")

    # Initialize alert manager
    try:
        alert_manager.enable()
        status["alerts"] = alert_manager.is_enabled
        if status["alerts"]:
            LOGGER.info("✅ Alert Manager initialized")
    except Exception as e:
        LOGGER.error(f"❌ Failed to initialize Alert Manager: {e}")

    # Initialize backup manager
    try:
        backup_manager.enable()
        status["backups"] = backup_manager.is_enabled
        if status["backups"]:
            LOGGER.info("✅ Backup Manager initialized")
    except Exception as e:
        LOGGER.error(f"❌ Failed to initialize Backup Manager: {e}")

    # Initialize profiler
    try:
        profiler.enable()
        status["profiler"] = profiler.is_enabled
        if status["profiler"]:
            LOGGER.info("✅ Profiler initialized")
    except Exception as e:
        LOGGER.error(f"❌ Failed to initialize Profiler: {e}")

    # Initialize recovery manager
    try:
        recovery_manager.enable()
        status["recovery"] = recovery_manager.is_enabled
        if status["recovery"]:
            LOGGER.info("✅ Recovery Manager initialized")
    except Exception as e:
        LOGGER.error(f"❌ Failed to initialize Recovery Manager: {e}")

    # Log summary
    enabled_count = sum(1 for v in status.values() if v)
    LOGGER.info(f"Phase 2: {enabled_count}/5 services enabled")

    return status


async def shutdown_phase2_services():
    """
    Gracefully shutdown Phase 2 services

    Should be called during bot shutdown
    """
    try:
        logger_manager.close()
        LOGGER.debug("Logger Manager shut down")
    except Exception as e:
        LOGGER.error(f"Error shutting down Logger Manager: {e}")

    try:
        # Cleanup old metrics
        profiler.cleanup_old_metrics(hours=24)
        LOGGER.debug("Profiler cleaned up")
    except Exception as e:
        LOGGER.error(f"Error cleaning profiler: {e}")

    try:
        # Clear old alerts
        alert_manager.clear_old_alerts(hours=24)
        LOGGER.debug("Alerts cleaned up")
    except Exception as e:
        LOGGER.error(f"Error cleaning alerts: {e}")

    try:
        # Cleanup old backups
        backup_manager.cleanup_old_backups(days=30)
        LOGGER.debug("Backups cleaned up")
    except Exception as e:
        LOGGER.error(f"Error cleaning backups: {e}")

    LOGGER.info("Phase 2 services shut down complete")
