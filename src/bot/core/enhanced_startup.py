"""
Phase 5: High Availability - Enhanced Startup Module
Orchestrates initialization and shutdown of all Phase 5 distributed systems

This module provides lifecycle management for:
- TIER 1: Health Monitor, Failover Manager
- TIER 2: Task Coordinator, API Gateway

NOTE: Cluster management and distributed consensus features were removed (2026-03-01).
Use Kubernetes/Docker Swarm for orchestration and Redis for distributed features.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from bot.core.api_gateway import ApiGateway
from bot.core.failover_manager import FailoverManager
from bot.core.health_monitor import HealthMonitor
from bot.core.task_coordinator import TaskCoordinator

logger = logging.getLogger(__name__)


# Phase 5 Configuration (can be overridden by environment)
# NOTE: Cluster/Distributed consensus features removed (2026-03-01)
# Use Kubernetes/Docker Swarm + Redis for distributed features
PHASE5_CONFIG = {
    # Global Phase 5 control
    "ENABLE_PHASE5": False,  # Master switch for all HA features

    # TIER 1: Fault Detection & Recovery
    "ENABLE_HEALTH_MONITOR": True,
    "ENABLE_FAILOVER_MANAGER": False,  # For Redis/external failover scenarios only

    # TIER 2: Task & API Orchestration (K8s/Swarm native recommended)
    "ENABLE_TASK_COORDINATOR": True,  # Can run standalone
    "ENABLE_API_GATEWAY": True,  # Can run standalone

    # Replication Configuration (for Redis replication - K8s external)
    "REPLICATION_STRATEGY": "MASTER_SLAVE",  # Handled by external Redis

    # Health Monitor Configuration
    "HEALTH_CHECK_INTERVAL": 30,  # seconds
    "HEALTH_ALERT_THRESHOLD": 3,  # failures before alert

    # Failover Configuration (for Redis failover only)
    "FAILOVER_AUTO_ENABLED": True,
    "FAILOVER_HEALTH_CHECK_INTERVAL": 5,
    "FAILOVER_FAILURE_THRESHOLD": 3,

    # Task Coordinator Configuration
    "TASK_COORDINATOR_MAX_PARALLEL": 10,
    "TASK_COORDINATOR_RETRY_MAX": 3,
    "TASK_COORDINATOR_TIMEOUT": 300,

    # API Gateway Configuration
    "API_GATEWAY_RATE_LIMIT": 100,  # requests per minute
    "API_GATEWAY_CIRCUIT_BREAKER": True,
    "API_GATEWAY_AUTH_REQUIRED": False,
}


class Phase5Status:
    """Status container for all Phase 5 components"""

    def __init__(self):
        self.enabled = False
        self.initialized_at: Optional[datetime] = None
        self.components: Dict[str, bool] = {}
        self.errors: Dict[str, str] = {}

    def to_dict(self) -> Dict[str, Any]:
        if self.enabled:
            components = self.components
            errors = self.errors
            initialized_at = (
                self.initialized_at.isoformat() if self.initialized_at else None
            )
        else:
            components = {}
            errors = {}
            initialized_at = None

        return {
            "enabled": self.enabled,
            "initialized_at": initialized_at,
            "components": components,
            "errors": errors,
            "total_components": len(components),
            "active_components": sum(1 for v in components.values() if v),
            "failed_components": len(errors),
        }


# Global status tracker
_phase5_status = Phase5Status()


async def initialize_enhanced_services(
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Initialize Phase 1 enhanced services (Redis/Celery/Metrics) without side effects."""
    final_config = {
        "ENABLE_REDIS_CACHE": False,
        "ENABLE_CELERY": False,
        "ENABLE_METRICS": False,
    }

    try:
        from bot.core.config_manager import Config

        final_config.update(
            {
                "ENABLE_REDIS_CACHE": getattr(Config, "ENABLE_REDIS_CACHE", False),
                "ENABLE_CELERY": getattr(Config, "ENABLE_CELERY", False),
                "ENABLE_METRICS": getattr(Config, "ENABLE_METRICS", False),
            }
        )
    except Exception:
        pass

    if config:
        final_config.update(config)

    return {
        "redis": {"enabled": bool(final_config["ENABLE_REDIS_CACHE"])},
        "celery": {"enabled": bool(final_config["ENABLE_CELERY"])},
        "metrics": {"enabled": bool(final_config["ENABLE_METRICS"])},
    }


async def _initialize_health_monitor(final_config, results) -> None:
    if not final_config.get("ENABLE_HEALTH_MONITOR"):
        return

    try:
        logger.info("  📊 Initializing Health Monitor...")
        health_monitor = HealthMonitor.get_instance()
        health_monitor.check_interval = final_config["HEALTH_CHECK_INTERVAL"]
        await health_monitor.enable()
        results["components"]["health_monitor"] = True
        _phase5_status.components["health_monitor"] = True
        logger.info("  ✅ Health Monitor: Active")
    except Exception as e:
        logger.error(f"  ❌ Health Monitor failed: {e}")
        results["components"]["health_monitor"] = False
        results["errors"].append(f"Health Monitor: {str(e)}")
        results["success"] = False
        _phase5_status.errors["health_monitor"] = str(e)


async def _initialize_failover_manager(final_config, results) -> None:
    if not final_config.get("ENABLE_FAILOVER_MANAGER"):
        return

    try:
        logger.info("  🔄 Initializing Failover Manager...")
        failover = FailoverManager.get_instance()
        failover.max_retries = 3
        await failover.start()
        results["components"]["failover_manager"] = True
        _phase5_status.components["failover_manager"] = True
        logger.info("  ✅ Failover Manager: Active")
    except Exception as e:
        logger.error(f"  ❌ Failover Manager failed: {e}")
        results["components"]["failover_manager"] = False
        results["errors"].append(f"Failover Manager: {str(e)}")
        _phase5_status.errors["failover_manager"] = str(e)
        results["success"] = False


async def _initialize_task_coordinator(final_config, results) -> None:
    if not final_config.get("ENABLE_TASK_COORDINATOR"):
        return

    try:
        logger.info("  📋 Initializing Task Coordinator...")
        coordinator = TaskCoordinator.get_instance()
        coordinator.max_parallel_tasks = final_config.get(
            "TASK_COORDINATOR_MAX_PARALLEL", 10
        )
        await coordinator.start()
        results["components"]["task_coordinator"] = True
        _phase5_status.components["task_coordinator"] = True
        logger.info("  ✅ Task Coordinator: Active")
    except Exception as e:
        logger.error(f"  ❌ Task Coordinator failed: {e}")
        results["components"]["task_coordinator"] = False
        results["errors"].append(f"Task Coordinator: {str(e)}")
        _phase5_status.errors["task_coordinator"] = str(e)
        results["success"] = False


async def _initialize_api_gateway(final_config, results) -> None:
    if not final_config.get("ENABLE_API_GATEWAY"):
        return

    try:
        logger.info("  🌉 Initializing API Gateway...")
        gateway = ApiGateway.get_instance()
        await gateway.start()
        results["components"]["api_gateway"] = True
        _phase5_status.components["api_gateway"] = True
        logger.info("  ✅ API Gateway: Active")
    except Exception as e:
        logger.error(f"  ❌ API Gateway failed: {e}")
        results["components"]["api_gateway"] = False
        results["errors"].append(f"API Gateway: {str(e)}")
        _phase5_status.errors["api_gateway"] = str(e)
        results["success"] = False


async def initialize_phase5_services(
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Initialize all Phase 5 High Availability services

    Args:
        config: Custom configuration (overrides PHASE5_CONFIG)

    Returns:
        Status dict with initialization results
    """
    global _phase5_status

    final_config = {**PHASE5_CONFIG}
    if config:
        final_config.update(config)

    if not final_config.get("ENABLE_PHASE5", False):
        logger.info("🔧 Phase 5: Disabled (ENABLE_PHASE5=False)")
        return {
            "success": True,
            "enabled": False,
            "message": "Phase 5 disabled by configuration",
            "components": {},
        }

    logger.info("🚀 Phase 5: Starting High Availability initialization...")
    _phase5_status.enabled = True
    _phase5_status.initialized_at = datetime.now(UTC)

    results = {
        "success": True,
        "enabled": True,
        "components": {},
        "errors": [],
    }

    await _initialize_health_monitor(final_config, results)
    await _initialize_failover_manager(final_config, results)
    await _initialize_task_coordinator(final_config, results)
    await _initialize_api_gateway(final_config, results)

    active_count = sum(1 for v in results["components"].values() if v)
    total_count = len(results["components"])

    if results["success"]:
        logger.info(
            f"✅ Phase 5: Initialized successfully ({active_count}/{total_count} components active)"
        )
    else:
        logger.warning(
            f"⚠️  Phase 5: Partially initialized ({active_count}/{total_count} components active)"
        )
        logger.warning(f"   Errors: {', '.join(results['errors'])}")

    return results


async def shutdown_phase5_services() -> Dict[str, Any]:
    """
    Gracefully shutdown all Phase 5 services

    Returns:
        Status dict with shutdown results
    """
    global _phase5_status

    if not _phase5_status.enabled:
        return {
            "success": True,
            "message": "Phase 5 was not enabled",
            "components": {},
        }

    logger.info("🛑 Phase 5: Starting graceful shutdown...")

    results = {
        "success": True,
        "components": {},
        "errors": [],
    }

    # Shutdown in reverse order of initialization
    shutdown_order = [
        ("api_gateway", ApiGateway, "stop"),
        ("task_coordinator", TaskCoordinator, "stop"),
        ("failover_manager", FailoverManager, "stop"),
        ("health_monitor", HealthMonitor, "disable"),
    ]

    for component_name, component_class, method_name in shutdown_order:
        if component_name not in _phase5_status.components:
            continue

        try:
            logger.info(f"  Stopping {component_name}...")
            instance = component_class.get_instance()
            shutdown_method = getattr(instance, method_name)
            await shutdown_method()
            results["components"][component_name] = True
            logger.info(f"  ✅ {component_name}: Stopped")
        except Exception as e:
            logger.error(f"  ❌ {component_name} shutdown failed: {e}")
            results["components"][component_name] = False
            results["errors"].append(f"{component_name}: {str(e)}")
            results["success"] = False

    _phase5_status.enabled = False
    _phase5_status.components.clear()
    _phase5_status.errors.clear()

    if results["success"]:
        logger.info("✅ Phase 5: Shutdown complete")
    else:
        logger.warning(
            f"⚠️  Phase 5: Shutdown completed with errors: {', '.join(results['errors'])}"
        )

    return results


def get_phase5_status() -> Dict[str, Any]:
    """
    Get current Phase 5 status

    Returns:
        Status dict with component states
    """
    global _phase5_status
    return _phase5_status.to_dict()


def _gather_health_monitor_status() -> Dict[str, Any]:
    """Gather health monitor component status"""
    try:
        health_monitor = HealthMonitor.get_instance()
        return {
            "active": True,
            "components": len(health_monitor.components),
            "unhealthy": sum(
                1
                for c in health_monitor.components.values()
                if c.status.value in ["unhealthy", "critical"]
            ),
        }
    except Exception:
        return {"active": False}

def _gather_failover_status() -> Dict[str, Any]:
    """Gather failover manager component status"""
    try:
        failover = FailoverManager.get_instance()
        return {
            "active": True,
            "enabled": failover.enabled,
            "recovery_operations": len(failover.active_recoveries),
        }
    except Exception:
        return {"active": False}

def _gather_task_coordinator_status() -> Dict[str, Any]:
    """Gather task coordinator component status"""
    try:
        coordinator = TaskCoordinator.get_instance()
        metrics = coordinator.get_metrics()
        return {
            "active": True,
            "total_tasks": metrics.total_tasks,
            "active_tasks": metrics.active_tasks,
            "completed": metrics.completed_tasks,
            "failed": metrics.failed_tasks,
        }
    except Exception:
        return {"active": False}

def _gather_api_gateway_status() -> Dict[str, Any]:
    """Gather API gateway component status"""
    try:
        gateway = ApiGateway.get_instance()
        metrics = gateway.get_metrics()
        return {
            "active": True,
            "total_requests": metrics.total_requests,
            "success_rate": (
                metrics.successful_requests / metrics.total_requests * 100
            )
            if metrics.total_requests > 0
            else 0,
            "rate_limited": metrics.rate_limited_requests,
            "circuit_breaker_open": metrics.circuit_breaker_open,
        }
    except Exception:
        return {"active": False}

async def get_phase5_detailed_status() -> Dict[str, Any]:
    """
    Get detailed status of all Phase 5 components

    Returns:
        Detailed status dict with component-specific information
    """
    if not _phase5_status.enabled:
        return {
            "enabled": False,
            "message": "Phase 5 not initialized",
        }

    detailed = {
        "enabled": True,
        "initialized_at": _phase5_status.initialized_at.isoformat()
        if _phase5_status.initialized_at
        else None,
        "components": {},
    }

    # Gather status from each active component
    if "health_monitor" in _phase5_status.components:
        detailed["components"]["health_monitor"] = _gather_health_monitor_status()

    if "failover_manager" in _phase5_status.components:
        detailed["components"]["failover_manager"] = _gather_failover_status()

    if "task_coordinator" in _phase5_status.components:
        detailed["components"]["task_coordinator"] = _gather_task_coordinator_status()

    if "api_gateway" in _phase5_status.components:
        detailed["components"]["api_gateway"] = _gather_api_gateway_status()

    return detailed


async def phase5_health_check() -> Dict[str, Any]:
    """
    Perform Phase 5 health check

    Returns:
        Health check result with status for all components
    """
    if not _phase5_status.enabled:
        return {
            "healthy": True,
            "enabled": False,
            "message": "Phase 5 not enabled",
        }

    health_status = {
        "healthy": True,
        "enabled": True,
        "components": {},
        "issues": [],
    }

    # Check each component
    for component_name in _phase5_status.components:
        if component_name in _phase5_status.errors:
            health_status["healthy"] = False
            health_status["components"][component_name] = False
            health_status["issues"].append(
                f"{component_name}: {_phase5_status.errors[component_name]}"
            )
        else:
            health_status["components"][component_name] = True

    return health_status
