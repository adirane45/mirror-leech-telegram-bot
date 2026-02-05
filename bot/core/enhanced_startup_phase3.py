"""
Phase 3 Startup - Initialize Advanced Features
Bootstraps Phase 3 infrastructure safely with error handling

Safe Innovation Path - Phase 3

Enhanced by: justadi
Date: February 5, 2026
"""

from typing import Dict
from . import LOGGER

from .graphql_api import schema
from .plugin_manager import plugin_manager
from .advanced_dashboard import router as dashboard_router


async def initialize_phase3_services() -> Dict[str, bool]:
    """
    Initialize all Phase 3 services safely

    Returns:
        Dictionary with service initialization status
    """
    status = {
        "graphql_api": False,
        "plugin_system": False,
        "advanced_dashboard": False,
    }

    # Initialize GraphQL API
    try:
        if schema is not None:
            status["graphql_api"] = True
            LOGGER.info("✅ GraphQL API initialized")
    except Exception as e:
        LOGGER.error(f"❌ Failed to initialize GraphQL API: {e}")

    # Initialize plugin manager
    try:
        plugin_manager.enable()
        status["plugin_system"] = plugin_manager.is_enabled
        if status["plugin_system"]:
            LOGGER.info("✅ Plugin System initialized")
    except Exception as e:
        LOGGER.error(f"❌ Failed to initialize Plugin System: {e}")

    # Initialize advanced dashboard
    try:
        if dashboard_router is not None:
            status["advanced_dashboard"] = True
            LOGGER.info("✅ Advanced Dashboard initialized")
    except Exception as e:
        LOGGER.error(f"❌ Failed to initialize Advanced Dashboard: {e}")

    # Log summary
    enabled_count = sum(1 for v in status.values() if v)
    LOGGER.info(f"Phase 3: {enabled_count}/3 services enabled")

    return status


async def shutdown_phase3_services():
    """
    Gracefully shutdown Phase 3 services

    Should be called during bot shutdown
    """
    try:
        await plugin_manager.shutdown()
        LOGGER.debug("Plugin Manager shut down")
    except Exception as e:
        LOGGER.error(f"Error shutting down Plugin Manager: {e}")

    LOGGER.info("Phase 3 services shut down complete")
