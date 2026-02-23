"""
Phase 5: High Availability - Enhanced Startup Module
Orchestrates initialization and shutdown of all Phase 5 distributed systems

This module provides lifecycle management for:
- TIER 1: Health Monitor, Cluster Manager, Failover Manager
- TIER 2: Replication Manager, Distributed State Manager
- TIER 3: Task Coordinator, Performance Optimizer, API Gateway
"""

import logging
from typing import Any, Dict, Optional
from datetime import datetime, UTC

from bot.core.health_monitor import HealthMonitor
from bot.core.cluster_manager import ClusterManager
from bot.core.failover_manager import FailoverManager
from bot.core.replication_manager import ReplicationManager
from bot.core.distributed_state_manager import DistributedStateManager
from bot.core.task_coordinator import TaskCoordinator
from bot.core.performance_optimizer import PerformanceOptimizer, OptimizationStrategy
from bot.core.api_gateway import ApiGateway

logger = logging.getLogger(__name__)


# Phase 5 Configuration (can be overridden by environment)
PHASE5_CONFIG = {
    # Global Phase 5 control
    "ENABLE_PHASE5": False,  # Master switch for all HA features

    # TIER 1: Fault Detection & Recovery
    "ENABLE_HEALTH_MONITOR": True,
    "ENABLE_CLUSTER_MANAGER": False,  # Requires multi-node setup
    "ENABLE_FAILOVER_MANAGER": False,  # Requires cluster

    # TIER 2: State Consistency
    "ENABLE_REPLICATION_MANAGER": False,  # Requires cluster
    "ENABLE_DISTRIBUTED_STATE": False,  # Requires cluster

    # TIER 3: Orchestration & APIs
    "ENABLE_TASK_COORDINATOR": True,  # Can run standalone
    "ENABLE_PERFORMANCE_OPTIMIZER": True,  # Can run standalone
    "ENABLE_API_GATEWAY": True,  # Can run standalone

    # Health Monitor Configuration
    "HEALTH_CHECK_INTERVAL": 30,  # seconds
    "HEALTH_ALERT_THRESHOLD": 3,  # failures before alert

    # Cluster Manager Configuration
    "CLUSTER_NODE_ID": "node-1",
    "CLUSTER_NODES": [],  # ["node-2:7946", "node-3:7946"]
    "CLUSTER_BIND_ADDRESS": "0.0.0.0",
    "CLUSTER_BIND_PORT": 7946,
    "CLUSTER_MIN_NODES": 2,

    # Failover Configuration
    "FAILOVER_ROLE": "PRIMARY",  # PRIMARY, SECONDARY, STANDBY
    "FAILOVER_AUTO_ENABLED": True,
    "FAILOVER_HEALTH_CHECK_INTERVAL": 5,
    "FAILOVER_FAILURE_THRESHOLD": 3,
    "FAILOVER_RECOVERY_WAIT": 60,

    # Replication Configuration
    "REPLICATION_STRATEGY": "MASTER_SLAVE",  # MASTER_SLAVE or MULTI_MASTER
    "REPLICATION_CONFLICT_RESOLUTION": "TIMESTAMP",  # TIMESTAMP, MANUAL, CUSTOM
    "REPLICATION_SYNC_INTERVAL": 10,

    # Distributed State Configuration
    "STATE_SNAPSHOT_ENABLED": True,
    "STATE_SNAPSHOT_INTERVAL": 300,  # 5 minutes
    "STATE_LOCK_STRATEGY": "DISTRIBUTED",  # LOCAL, DISTRIBUTED, OPTIMISTIC
    "STATE_LOCK_TIMEOUT": 30,

    # Task Coordinator Configuration
    "TASK_COORDINATOR_MAX_PARALLEL": 10,
    "TASK_COORDINATOR_RETRY_MAX": 3,
    "TASK_COORDINATOR_TIMEOUT": 300,

    # Performance Optimizer Configuration
    "OPTIMIZER_STRATEGY": "BALANCED",  # AGGRESSIVE, BALANCED, CONSERVATIVE, MANUAL
    "OPTIMIZER_COLLECTION_INTERVAL": 60,
    "OPTIMIZER_ANALYSIS_INTERVAL": 300,
    "OPTIMIZER_AUTO_SCALING": False,

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

    # Check master switch
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

    # ========================================
    # TIER 1: Fault Detection & Recovery
    # ========================================

    # 1. Health Monitor (Foundation)
    if final_config.get("ENABLE_HEALTH_MONITOR"):
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

    # 2. Cluster Manager
    if final_config.get("ENABLE_CLUSTER_MANAGER"):
        try:
            logger.info("  🌐 Initializing Cluster Manager...")
            cluster = ClusterManager.get_instance()
            cluster.node_id = final_config.get("CLUSTER_NODE_ID", "node-1")
            cluster.min_cluster_size = final_config.get("CLUSTER_MIN_NODES", 2)

            # Register peer nodes
            for node_addr in final_config.get("CLUSTER_NODES", []):
                if ":" in node_addr:
                    host, port = node_addr.split(":", 1)
                    await cluster.register_node(f"node-{host}", host, int(port))

            await cluster.start()

            results["components"]["cluster_manager"] = True
            _phase5_status.components["cluster_manager"] = True
            logger.info("  ✅ Cluster Manager: Active")
        except Exception as e:
            logger.error(f"  ❌ Cluster Manager failed: {e}")
            results["components"]["cluster_manager"] = False
            results["errors"].append(f"Cluster Manager: {str(e)}")
            _phase5_status.errors["cluster_manager"] = str(e)
            results["success"] = False

    # 3. Failover Manager
    if final_config.get("ENABLE_FAILOVER_MANAGER"):
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

    # ========================================
    # TIER 2: State Consistency
    # ========================================

    # 4. Replication Manager
    if final_config.get("ENABLE_REPLICATION_MANAGER"):
        try:
            logger.info("  📡 Initializing Replication Manager...")
            replication = ReplicationManager.get_instance()
            await replication.start(
                node_id=final_config.get("CLUSTER_NODE_ID", "node-1")
            )

            results["components"]["replication_manager"] = True
            _phase5_status.components["replication_manager"] = True
            logger.info("  ✅ Replication Manager: Active")
        except Exception as e:
            logger.error(f"  ❌ Replication Manager failed: {e}")
            results["components"]["replication_manager"] = False
            results["errors"].append(f"Replication Manager: {str(e)}")
            _phase5_status.errors["replication_manager"] = str(e)
            results["success"] = False

    # 5. Distributed State Manager
    if final_config.get("ENABLE_DISTRIBUTED_STATE"):
        try:
            logger.info("  🗄️  Initializing Distributed State Manager...")
            state_manager = DistributedStateManager.get_instance()
            await state_manager.start(
                node_id=final_config.get("CLUSTER_NODE_ID", "node-1")
            )

            results["components"]["distributed_state_manager"] = True
            _phase5_status.components["distributed_state_manager"] = True
            logger.info("  ✅ Distributed State Manager: Active")
        except Exception as e:
            logger.error(f"  ❌ Distributed State Manager failed: {e}")
            results["components"]["distributed_state_manager"] = False
            results["errors"].append(f"Distributed State Manager: {str(e)}")
            _phase5_status.errors["distributed_state_manager"] = str(e)
            results["success"] = False

    # ========================================
    # TIER 3: Orchestration & APIs
    # ========================================

    # 6. Task Coordinator
    if final_config.get("ENABLE_TASK_COORDINATOR"):
        try:
            logger.info("  📋 Initializing Task Coordinator...")
            coordinator = TaskCoordinator.get_instance()
            coordinator.max_parallel_tasks = final_config.get(
                "TASK_COORDINATOR_MAX_PARALLEL", 10
            )
            await coordinator.start(
                node_id=final_config.get("CLUSTER_NODE_ID", "node-1")
            )

            results["components"]["task_coordinator"] = True
            _phase5_status.components["task_coordinator"] = True
            logger.info("  ✅ Task Coordinator: Active")
        except Exception as e:
            logger.error(f"  ❌ Task Coordinator failed: {e}")
            results["components"]["task_coordinator"] = False
            results["errors"].append(f"Task Coordinator: {str(e)}")
            _phase5_status.errors["task_coordinator"] = str(e)
            results["success"] = False

    # 7. Performance Optimizer
    if final_config.get("ENABLE_PERFORMANCE_OPTIMIZER"):
        try:
            logger.info("  ⚡ Initializing Performance Optimizer...")
            optimizer = PerformanceOptimizer.get_instance()

            strategy_str = final_config.get("OPTIMIZER_STRATEGY", "BALANCED").upper()
            if strategy_str in OptimizationStrategy.__members__:
                strategy = OptimizationStrategy[strategy_str]
            else:
                strategy = OptimizationStrategy.BALANCED

            await optimizer.start(
                node_id=final_config.get("CLUSTER_NODE_ID", "node-1"),
                strategy=strategy,
            )

            results["components"]["performance_optimizer"] = True
            _phase5_status.components["performance_optimizer"] = True
            logger.info("  ✅ Performance Optimizer: Active")
        except Exception as e:
            logger.error(f"  ❌ Performance Optimizer failed: {e}")
            results["components"]["performance_optimizer"] = False
            results["errors"].append(f"Performance Optimizer: {str(e)}")
            _phase5_status.errors["performance_optimizer"] = str(e)
            results["success"] = False

    # 8. API Gateway
    if final_config.get("ENABLE_API_GATEWAY"):
        try:
            logger.info("  🌉 Initializing API Gateway...")
            gateway = ApiGateway.get_instance()
            await gateway.start(node_id=final_config.get("CLUSTER_NODE_ID", "node-1"))

            results["components"]["api_gateway"] = True
            _phase5_status.components["api_gateway"] = True
            logger.info("  ✅ API Gateway: Active")
        except Exception as e:
            logger.error(f"  ❌ API Gateway failed: {e}")
            results["components"]["api_gateway"] = False
            results["errors"].append(f"API Gateway: {str(e)}")
            _phase5_status.errors["api_gateway"] = str(e)
            results["success"] = False

    # Final summary
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
        ("performance_optimizer", PerformanceOptimizer, "stop"),
        ("task_coordinator", TaskCoordinator, "stop"),
        ("distributed_state_manager", DistributedStateManager, "stop"),
        ("replication_manager", ReplicationManager, "stop"),
        ("failover_manager", FailoverManager, "stop"),
        ("cluster_manager", ClusterManager, "stop"),
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
        try:
            health_monitor = HealthMonitor.get_instance()
            detailed["components"]["health_monitor"] = {
                "active": True,
                "components": len(health_monitor.components),
                "unhealthy": sum(
                    1
                    for c in health_monitor.components.values()
                    if c.status.value in ["unhealthy", "critical"]
                ),
            }
        except Exception:
            detailed["components"]["health_monitor"] = {"active": False}

    if "cluster_manager" in _phase5_status.components:
        try:
            cluster = ClusterManager.get_instance()
            info = cluster.get_cluster_info()
            detailed["components"]["cluster_manager"] = {
                "active": True,
                "state": info.state.value,
                "total_nodes": info.total_nodes,
                "active_nodes": info.active_nodes,
                "leader": info.leader_id,
            }
        except Exception:
            detailed["components"]["cluster_manager"] = {"active": False}

    if "failover_manager" in _phase5_status.components:
        try:
            failover = FailoverManager.get_instance()
            detailed["components"]["failover_manager"] = {
                "active": True,
                "enabled": failover.enabled,
                "recovery_operations": len(failover.active_recoveries),
            }
        except Exception:
            detailed["components"]["failover_manager"] = {"active": False}

    if "replication_manager" in _phase5_status.components:
        try:
            replication = ReplicationManager.get_instance()
            detailed["components"]["replication_manager"] = {
                "active": True,
                "node_id": replication.node_id,
                "replicas": len(replication.replicas),
            }
        except Exception:
            detailed["components"]["replication_manager"] = {"active": False}

    if "distributed_state_manager" in _phase5_status.components:
        try:
            state_manager = DistributedStateManager.get_instance()
            detailed["components"]["distributed_state_manager"] = {
                "active": True,
                "node_id": state_manager.node_id,
                "state_entries": len(state_manager.state),
                "active_locks": len(state_manager.locks),
            }
        except Exception:
            detailed["components"]["distributed_state_manager"] = {"active": False}

    if "task_coordinator" in _phase5_status.components:
        try:
            coordinator = TaskCoordinator.get_instance()
            metrics = coordinator.get_metrics()
            detailed["components"]["task_coordinator"] = {
                "active": True,
                "total_tasks": metrics.total_tasks,
                "active_tasks": metrics.active_tasks,
                "completed": metrics.completed_tasks,
                "failed": metrics.failed_tasks,
            }
        except Exception:
            detailed["components"]["task_coordinator"] = {"active": False}

    if "performance_optimizer" in _phase5_status.components:
        try:
            optimizer = PerformanceOptimizer.get_instance()
            metrics = optimizer.get_metrics()
            detailed["components"]["performance_optimizer"] = {
                "active": True,
                "strategy": optimizer.strategy.value,
                "node_health": optimizer.get_node_health(optimizer.node_id),
                "total_snapshots": metrics.total_snapshots,
                "recommendations": metrics.recommendations_generated,
            }
        except Exception:
            detailed["components"]["performance_optimizer"] = {"active": False}

    if "api_gateway" in _phase5_status.components:
        try:
            gateway = ApiGateway.get_instance()
            metrics = gateway.get_metrics()
            detailed["components"]["api_gateway"] = {
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
            detailed["components"]["api_gateway"] = {"active": False}

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
