"""
Configuration Enhancements for Phase 5: High Availability

Adds configuration options for:
- Cluster Management
- Failover
- Replication
- Distributed State
- Health Monitoring

All features are disabled by default for backward compatibility.
"""

from typing import Dict, Any


def get_phase5_config() -> Dict[str, Any]:
    """Get Phase 5 High Availability configuration"""
    return {
        # ===== Cluster Management =====
        'CLUSTER_ENABLED': False,
        'CLUSTER_NODE_ID': None,  # Auto-generated if not provided
        'CLUSTER_ADDRESS': '0.0.0.0',
        'CLUSTER_PORT': 7946,
        'CLUSTER_SEED_NODES': [],  # List of seed nodes: ['host:port', ...]
        'CLUSTER_HEARTBEAT_INTERVAL': 5,  # seconds
        'CLUSTER_NODE_TIMEOUT': 15,  # seconds
        'CLUSTER_ELECTION_TIMEOUT': 10,  # seconds
        'CLUSTER_NODE_PRIORITY': 100,  # Higher = more likely to be leader
        
        # ===== Failover Configuration =====
        'FAILOVER_ENABLED': False,
        'FAILOVER_MODE': 'automatic',  # automatic, manual
        'FAILOVER_TIMEOUT': 30,  # seconds
        'FAILOVER_HEALTH_CHECK_INTERVAL': 5,  # seconds
        'FAILOVER_FAILURE_THRESHOLD': 3,  # consecutive failures
        'FAILOVER_RECOVERY_WAIT_TIME': 60,  # seconds before failback
        'FAILOVER_MAX_ATTEMPTS': 3,
        'FAILOVER_PRIMARY_NODE': None,  # Node ID for primary
        'FAILOVER_SECONDARY_NODES': [],  # List of secondary node IDs
        
        # ===== Replication Configuration =====
        'REPLICATION_ENABLED': False,
        'REPLICATION_MODE': 'master_slave',  # master_slave, multi_master
        'REPLICATION_CONSISTENCY': 'eventual',  # strong, eventual, quorum
        'REPLICATION_CONFLICT_RESOLUTION': 'last_write_wins',  # last_write_wins, first_write_wins, merge, manual
        'REPLICATION_MASTER_NODE': None,
        'REPLICATION_SLAVE_NODES': [],
        'REPLICATION_SYNC_INTERVAL': 5,  # seconds
        'REPLICATION_BATCH_SIZE': 100,
        'REPLICATION_ASYNC_WRITES': True,
        
        # Data Types to Replicate
        'REPLICATION_REPLICATE_TASKS': True,
        'REPLICATION_REPLICATE_CONFIG': True,
        'REPLICATION_REPLICATE_STATS': False,
        'REPLICATION_REPLICATE_LOGS': False,
        
        # ===== Distributed State Configuration =====
        'DISTRIBUTED_STATE_ENABLED': False,
        'DISTRIBUTED_STATE_BACKEND': 'memory',  # memory, redis, etcd
        'DISTRIBUTED_STATE_SYNC_INTERVAL': 5,  # seconds
        
        # Distributed Locks
        'DISTRIBUTED_LOCKS_ENABLED': False,
        'DISTRIBUTED_LOCK_DEFAULT_TTL': 30,  # seconds
        'DISTRIBUTED_LOCK_AUTO_EXTEND': True,
        'DISTRIBUTED_LOCK_EXTEND_INTERVAL': 10,  # seconds
        
        # State Consistency
        'DISTRIBUTED_STATE_CONSISTENCY': 'eventual',  # strong, eventual
        'DISTRIBUTED_STATE_VERSION_VECTORS': True,
        
        # ===== Health Monitoring =====
        'HEALTH_MONITOR_ENABLED': False,
        'HEALTH_CHECK_INTERVAL': 30,  # seconds
        'HEALTH_CHECK_TIMEOUT': 5,  # seconds
        'HEALTH_FAILURE_THRESHOLD': 3,  # consecutive failures
        'HEALTH_RECOVERY_ENABLED': True,
        
        # Component Health Checks
        'HEALTH_CHECK_NODES': True,
        'HEALTH_CHECK_DATABASE': True,
        'HEALTH_CHECK_CACHE': True,
        'HEALTH_CHECK_QUEUE': True,
        'HEALTH_CHECK_STORAGE': True,
        'HEALTH_CHECK_API': True,
        
        # Health Check Endpoints
        'HEALTH_NODE_CHECK_URL': '/health',
        'HEALTH_DATABASE_CHECK_TIMEOUT': 5,
        'HEALTH_CACHE_CHECK_TIMEOUT': 3,
        'HEALTH_QUEUE_CHECK_TIMEOUT': 5,
        
        # ===== High Availability Strategy =====
        'HA_STRATEGY': 'active_passive',  # active_passive, active_active, distributed
        'HA_MIN_NODES': 2,
        'HA_QUORUM_SIZE': 2,  # Minimum nodes for cluster operations
        
        # ===== Split-Brain Prevention =====
        'SPLIT_BRAIN_PREVENTION': True,
        'SPLIT_BRAIN_QUORUM_REQUIRED': True,
        'SPLIT_BRAIN_FENCING': False,  # Aggressive - forcefully stop split nodes
        
        # ===== Data Consistency =====
        'DATA_CONSISTENCY_LEVEL': 'eventual',  # strong, eventual, causal
        'DATA_CONSISTENCY_TIMEOUT': 30,  # seconds
        'DATA_CONFLICT_RESOLUTION': 'last_write_wins',
        
        # ===== Backup and Recovery =====
        'HA_BACKUP_ENABLED': True,
        'HA_BACKUP_INTERVAL': 3600,  # seconds (1 hour)
        'HA_BACKUP_RETENTION': 7,  # days
        'HA_POINT_IN_TIME_RECOVERY': False,
        
        # ===== Network and Communication =====
        'HA_NETWORK_TIMEOUT': 10,  # seconds
        'HA_RETRY_ATTEMPTS': 3,
        'HA_RETRY_BACKOFF': 'exponential',  # linear, exponential
        'HA_COMPRESSION_ENABLED': False,
        'HA_ENCRYPTION_ENABLED': False,
        
        # ===== Monitoring and Alerting =====
        'HA_MONITORING_ENABLED': True,
        'HA_ALERT_ON_FAILOVER': True,
        'HA_ALERT_ON_NODE_DOWN': True,
        'HA_ALERT_ON_SPLIT_BRAIN': True,
        'HA_ALERT_ON_REPLICATION_LAG': True,
        'HA_REPLICATION_LAG_THRESHOLD': 60,  # seconds
        
        # ===== Performance Tuning =====
        'HA_CONNECTION_POOL_SIZE': 10,
        'HA_MAX_CONCURRENT_OPERATIONS': 100,
        'HA_OPERATION_TIMEOUT': 30,  # seconds
        'HA_BATCH_OPERATIONS': True,
        
        # ===== Debug and Logging =====
        'HA_DEBUG_MODE': False,
        'HA_LOG_LEVEL': 'INFO',  # DEBUG, INFO, WARNING, ERROR
        'HA_LOG_CLUSTER_EVENTS': True,
        'HA_LOG_FAILOVER_EVENTS': True,
        'HA_LOG_REPLICATION_EVENTS': False,
        'HA_METRICS_ENABLED': True,
    }


def validate_phase5_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate Phase 5 configuration and return warnings/errors"""
    warnings = []
    errors = []
    
    # Cluster validation
    if config.get('CLUSTER_ENABLED'):
        if config.get('CLUSTER_PORT', 0) < 1024:
            warnings.append("CLUSTER_PORT < 1024 may require elevated privileges")
        
        if not config.get('CLUSTER_SEED_NODES') and not config.get('CLUSTER_NODE_ID'):
            warnings.append("No CLUSTER_SEED_NODES defined - starting standalone cluster")
    
    # Failover validation
    if config.get('FAILOVER_ENABLED'):
        if not config.get('CLUSTER_ENABLED'):
            errors.append("FAILOVER_ENABLED requires CLUSTER_ENABLED=True")
        
        if config.get('FAILOVER_FAILURE_THRESHOLD', 0) < 1:
            errors.append("FAILOVER_FAILURE_THRESHOLD must be at least 1")
        
        if config.get('FAILOVER_MODE') not in ['automatic', 'manual']:
            errors.append("FAILOVER_MODE must be 'automatic' or 'manual'")
    
    # Replication validation
    if config.get('REPLICATION_ENABLED'):
        if not config.get('CLUSTER_ENABLED'):
            errors.append("REPLICATION_ENABLED requires CLUSTER_ENABLED=True")
        
        mode = config.get('REPLICATION_MODE')
        if mode not in ['master_slave', 'multi_master']:
            errors.append("REPLICATION_MODE must be 'master_slave' or 'multi_master'")
        
        consistency = config.get('REPLICATION_CONSISTENCY')
        if consistency not in ['strong', 'eventual', 'quorum']:
            errors.append("REPLICATION_CONSISTENCY must be 'strong', 'eventual', or 'quorum'")
    
    # Distributed state validation
    if config.get('DISTRIBUTED_STATE_ENABLED'):
        if not config.get('CLUSTER_ENABLED'):
            errors.append("DISTRIBUTED_STATE_ENABLED requires CLUSTER_ENABLED=True")
        
        backend = config.get('DISTRIBUTED_STATE_BACKEND')
        if backend not in ['memory', 'redis', 'etcd']:
            errors.append("DISTRIBUTED_STATE_BACKEND must be 'memory', 'redis', or 'etcd'")
    
    # HA strategy validation
    if config.get('CLUSTER_ENABLED'):
        strategy = config.get('HA_STRATEGY')
        if strategy not in ['active_passive', 'active_active', 'distributed']:
            errors.append("HA_STRATEGY must be 'active_passive', 'active_active', or 'distributed'")
        
        min_nodes = config.get('HA_MIN_NODES', 0)
        if min_nodes < 1:
            errors.append("HA_MIN_NODES must be at least 1")
        
        quorum = config.get('HA_QUORUM_SIZE', 0)
        if quorum < (min_nodes // 2 + 1):
            warnings.append(f"HA_QUORUM_SIZE ({quorum}) should be at least {min_nodes // 2 + 1} for majority")
    
    # Health monitoring validation
    if config.get('HEALTH_MONITOR_ENABLED'):
        interval = config.get('HEALTH_CHECK_INTERVAL', 0)
        timeout = config.get('HEALTH_CHECK_TIMEOUT', 0)
        
        if interval <= timeout:
            warnings.append("HEALTH_CHECK_INTERVAL should be greater than HEALTH_CHECK_TIMEOUT")
        
        if config.get('HEALTH_FAILURE_THRESHOLD', 0) < 1:
            errors.append("HEALTH_FAILURE_THRESHOLD must be at least 1")
    
    return {
        'valid': len(errors) == 0,
        'warnings': warnings,
        'errors': errors
    }


def get_ha_preset_configs() -> Dict[str, Dict[str, Any]]:
    """Get preset HA configurations for common scenarios"""
    
    base_config = get_phase5_config()
    
    presets = {
        # Simple active-passive with 2 nodes
        'simple_failover': {
            **base_config,
            'CLUSTER_ENABLED': True,
            'FAILOVER_ENABLED': True,
            'HEALTH_MONITOR_ENABLED': True,
            'HA_STRATEGY': 'active_passive',
            'HA_MIN_NODES': 2,
        },
        
        # Full HA with replication
        'full_ha': {
            **base_config,
            'CLUSTER_ENABLED': True,
            'FAILOVER_ENABLED': True,
            'REPLICATION_ENABLED': True,
            'DISTRIBUTED_STATE_ENABLED': True,
            'HEALTH_MONITOR_ENABLED': True,
            'HA_STRATEGY': 'active_active',
            'HA_MIN_NODES': 3,
            'HA_QUORUM_SIZE': 2,
            'REPLICATION_CONSISTENCY': 'quorum',
        },
        
        # Distributed cluster
        'distributed': {
            **base_config,
            'CLUSTER_ENABLED': True,
            'FAILOVER_ENABLED': True,
            'REPLICATION_ENABLED': True,
            'REPLICATION_MODE': 'multi_master',
            'DISTRIBUTED_STATE_ENABLED': True,
            'DISTRIBUTED_LOCKS_ENABLED': True,
            'HEALTH_MONITOR_ENABLED': True,
            'HA_STRATEGY': 'distributed',
            'HA_MIN_NODES': 5,
            'HA_QUORUM_SIZE': 3,
        },
        
        # Development/testing
        'development': {
            **base_config,
            'CLUSTER_ENABLED': True,
            'HEALTH_MONITOR_ENABLED': True,
            'HA_DEBUG_MODE': True,
            'HA_LOG_LEVEL': 'DEBUG',
            'HA_MIN_NODES': 1,
        }
    }
    
    return presets


# Export configuration
PHASE5_CONFIG = get_phase5_config()
PHASE5_PRESETS = get_ha_preset_configs()
