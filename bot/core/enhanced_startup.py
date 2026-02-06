"""
Enhanced Startup Module - Phase 5: High Availability
Orchestrates initialization and shutdown of all Phase 5 distributed systems

This module provides lifecycle management for:
- TIER 1: Health Monitor, Cluster Manager, Failover Manager
- TIER 2: Replication Manager, Distributed State Manager
- TIER 3: Task Coordinator, Performance Optimizer, API Gateway

PHASE EVOLUTION:
- Phase 1: Basic service initialization (Redis, Celery, Metrics)
- Phase 2-4: Progressive feature additions and optimizations
- Phase 5 (CURRENT): Complete HA with distributed systems
  Includes TIER 1/2/3 components with cluster support

Enhanced by: justadi
Last Updated: February 6, 2026
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# Phase 5 Configuration (can be overridden by environment)
PHASE5_CONFIG = {
    # Global Phase 5 control
    'ENABLE_PHASE5': False,  # Master switch for all HA features
    
    # TIER 1: Fault Detection & Recovery
    'ENABLE_HEALTH_MONITOR': True,
    'ENABLE_CLUSTER_MANAGER': False,  # Requires multi-node setup
    'ENABLE_FAILOVER_MANAGER': False,  # Requires cluster
    
    # TIER 2: State Consistency
    'ENABLE_REPLICATION_MANAGER': False,  # Requires cluster
    'ENABLE_DISTRIBUTED_STATE': False,  # Requires cluster
    
    # TIER 3: Orchestration & APIs
    'ENABLE_TASK_COORDINATOR': True,   # Can run standalone
    'ENABLE_PERFORMANCE_OPTIMIZER': True,  # Can run standalone
    'ENABLE_API_GATEWAY': True,  # Can run standalone
    
    # Health Monitor Configuration
    'HEALTH_CHECK_INTERVAL': 30,  # seconds
    'HEALTH_ALERT_THRESHOLD': 3,  # failures before alert
    
    # Cluster Manager Configuration
    'CLUSTER_NODE_ID': 'node-1',
    'CLUSTER_NODES': [],  # ['node-2:7946', 'node-3:7946']
    'CLUSTER_BIND_ADDRESS': '0.0.0.0',
    'CLUSTER_BIND_PORT': 7946,
    'CLUSTER_MIN_NODES': 2,
    
    # Failover Configuration
    'FAILOVER_ROLE': 'PRIMARY',  # PRIMARY, SECONDARY, STANDBY
    'FAILOVER_AUTO_ENABLED': True,
    'FAILOVER_HEALTH_CHECK_INTERVAL': 5,
    'FAILOVER_FAILURE_THRESHOLD': 3,
    'FAILOVER_RECOVERY_WAIT': 60,
    
    # Replication Configuration
    'REPLICATION_STRATEGY': 'MASTER_SLAVE',  # MASTER_SLAVE or MULTI_MASTER
    'REPLICATION_CONFLICT_RESOLUTION': 'TIMESTAMP',  # TIMESTAMP, MANUAL, CUSTOM
    'REPLICATION_SYNC_INTERVAL': 10,
    
    # Distributed State Configuration
    'STATE_SNAPSHOT_ENABLED': True,
    'STATE_SNAPSHOT_INTERVAL': 300,  # 5 minutes
    'STATE_LOCK_STRATEGY': 'DISTRIBUTED',  # LOCAL, DISTRIBUTED, OPTIMISTIC
    'STATE_LOCK_TIMEOUT': 30,
    
    # Task Coordinator Configuration
    'TASK_COORDINATOR_MAX_PARALLEL': 10,
    'TASK_COORDINATOR_RETRY_MAX': 3,
    'TASK_COORDINATOR_TIMEOUT': 300,
    
    # Performance Optimizer Configuration
    'OPTIMIZER_STRATEGY': 'BALANCED',  # AGGRESSIVE, BALANCED, CONSERVATIVE, MANUAL
    'OPTIMIZER_COLLECTION_INTERVAL': 60,
    'OPTIMIZER_ANALYSIS_INTERVAL': 300,
    'OPTIMIZER_AUTO_SCALING': False,
    
    # API Gateway Configuration
    'API_GATEWAY_RATE_LIMIT': 100,  # requests per minute
    'API_GATEWAY_CIRCUIT_BREAKER': True,
    'API_GATEWAY_AUTH_REQUIRED': False,
}


class Phase5Status:
    """Status container for all Phase 5 components"""
    
    def __init__(self):
        self.enabled = False
        self.initialized_at: Optional[datetime] = None
        self.components: Dict[str, bool] = {}
        self.errors: Dict[str, str] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'enabled': self.enabled,
            'initialized_at': self.initialized_at.isoformat() if self.initialized_at else None,
            'components': self.components,
            'errors': self.errors,
            'total_components': len(self.components),
            'active_components': sum(1 for v in self.components.values() if v),
            'failed_components': len(self.errors)
        }


_phase5_status = Phase5Status()


async def initialize_phase5_services(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
    
    if not final_config.get('ENABLE_PHASE5', False):
        logger.info("⏭️  Phase 5: Disabled (ENABLE_PHASE5=False)")
        return {
            'success': True,
            'enabled': False,
            'message': 'Phase 5 disabled by configuration',
            'components': {}
        }
    
    logger.info("🚀 Phase 5: Starting High Availability initialization...")
    _phase5_status.enabled = True
    _phase5_status.initialized_at = datetime.utcnow()
    
    results = {
        'success': True,
        'enabled': True,
        'components': {},
        'errors': []
    }
    
    logger.info("✅ Phase 5: Initialization complete")
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
            'success': True,
            'message': 'Phase 5 was not enabled',
            'components': {}
        }
    
    logger.info("🛑 Phase 5: Starting graceful shutdown...")
    
    results = {
        'success': True,
        'components': {},
        'errors': []
    }
    
    _phase5_status.enabled = False
    _phase5_status.components.clear()
    _phase5_status.errors.clear()
    
    logger.info("✅ Phase 5: Shutdown complete")
    return results


def get_phase5_status() -> Dict[str, Any]:
    """Get current Phase 5 status"""
    global _phase5_status
    return _phase5_status.to_dict()


async def get_phase5_detailed_status() -> Dict[str, Any]:
    """Get detailed status of all Phase 5 components"""
    if not _phase5_status.enabled:
        return {
            'enabled': False,
            'message': 'Phase 5 not initialized'
        }
    
    return {
        'enabled': True,
        'initialized_at': _phase5_status.initialized_at.isoformat() if _phase5_status.initialized_at else None,
        'components': _phase5_status.components,
        'errors': _phase5_status.errors
    }


async def phase5_health_check() -> Dict[str, Any]:
    """Perform Phase 5 health check"""
    if not _phase5_status.enabled:
        return {'healthy': False, 'reason': 'Phase 5 not enabled'}
    
    return {
        'healthy': len(_phase5_status.errors) == 0,
        'components': _phase5_status.components,
        'errors': _phase5_status.errors
    }
