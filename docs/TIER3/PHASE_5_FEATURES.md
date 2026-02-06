# TIER 3: Phase 5 - High Availability Features Guide

> **Part of TIER 3: Production Deployment**  
> **Status:** ✅ Production Ready  
> **Last Updated:** February 6, 2026

## Overview

Phase 5 introduces enterprise-grade High Availability (HA) features to ensure zero-downtime operations, automatic failover, and data consistency across distributed nodes.

**Key Capabilities:**
- Automatic cluster formation and leader election
- Seamless failover on node failure
- Multi-node data replication
- Distributed state management with locks
- Comprehensive health monitoring

**Status:** ✅ Production Ready  
**Backward Compatible:** ✅ All features disabled by default  
**Breaking Changes:** ❌ None

---

## Table of Contents

1. [Cluster Management](#1-cluster-management)
2. [Failover Management](#2-failover-management)
3. [Replication Management](#3-replication-management)
4. [Distributed State](#4-distributed-state)
5. [Health Monitoring](#5-health-monitoring)
6. [Configuration](#6-configuration)
7. [Use Cases](#7-use-cases)
8. [Best Practices](#8-best-practices)

---

## 1. Cluster Management

### Overview
Manages cluster membership, node discovery, and leader election.

### Key Features

**1.1 Automatic Cluster Formation**
- Nodes discover each other via seed nodes
- Automatic registration and deregistration
- Gossip-based membership protocol

**1.2 Leader Election**
- Priority-based election algorithm
- Automatic re-election on leader failure
- Split-brain prevention with quorum

**1.3 Node States**
```python
NodeState:
- JOINING: Node joining cluster
- ACTIVE: Fully operational node
- LEADER: Elected leader node
- DEGRADED: Node experiencing issues
- LEAVING: Graceful shutdown
- UNREACHABLE: Node not responding
```

### Usage Examples

**Enable Clustering:**
```python
from bot.core.cluster_manager import ClusterManager
from config.main_config import load_user_config

config = load_user_config()
cluster = ClusterManager.get_instance()

# Start standalone cluster
await cluster.enable(
    address=config.get('CLUSTER_ADDRESS', '192.168.1.100'),
    port=config.get('CLUSTER_PORT', 7946)
)

# Join existing cluster
await cluster.enable(
    address=config.get('CLUSTER_ADDRESS', '192.168.1.100'),
    port=config.get('CLUSTER_PORT', 7946),
    seed_nodes=config.get('CLUSTER_SEED_NODES', [])
)
```

**Get Cluster Info:**
```python
info = await cluster.get_cluster_info()
print(f"Total nodes: {info['total_nodes']}")
print(f"Leader: {info['leader_node']}")
print(f"Is healthy: {info['is_healthy']}")
```

**Get Leader Node:**
```python
leader = await cluster.get_leader_node()
if leader:
    print(f"Leader: {leader.node_id}")
    print(f"Address: {leader.address}:{leader.port}")
```

---

## 2. Failover Management

### Overview
Automatic failover to secondary nodes when primary becomes unavailable.

### Key Features

**2.1 Failover Modes**
- **Automatic**: Failover triggered automatically on failure
- **Manual**: Failover requires explicit command

**2.2 Failover Roles**
```python
FailoverRole:
- PRIMARY: Active primary node
- SECONDARY: Standby for failover
- STANDBY: Not participating in failover
```

**2.3 Failover States**
```python
FailoverState:
- NORMAL: All healthy
- DETECTING: Failure detected
- FAILING_OVER: Failover in progress
- FAILED_OVER: Failover completed
- RECOVERING: Failback in progress
- FAILED: Failover failed
```

### Usage Examples

**Enable Failover:**
```python
from bot.core.failover_manager import (
    FailoverManager,
    FailoverPolicy,
    FailoverRole
)
from config.main_config import load_user_config

config = load_user_config()
failover = FailoverManager.get_instance()

policy = FailoverPolicy(
    auto_failover_enabled=config.get('FAILOVER_MODE') == 'automatic',
    failure_threshold=config.get('FAILOVER_FAILURE_THRESHOLD', 3),
    health_check_interval=config.get('FAILOVER_HEALTH_CHECK_INTERVAL', 5),
    recovery_wait_time=config.get('FAILOVER_RECOVERY_WAIT_TIME', 60)
)

await failover.enable(role=FailoverRole.PRIMARY, policy=policy)
```

**Check Failover Status:**
```python
status = await failover.get_failover_status()
print(f"State: {status['state']}")
print(f"Primary: {status['primary_node']}")
print(f"Secondaries: {status['secondary_nodes']}")
```

---

## 3. Replication Management

### Overview
Replicate data across multiple nodes for redundancy and consistency.

### Key Features

**3.1 Replication Modes**
- **Master-Slave**: Single master, multiple read replicas
- **Multi-Master**: Multiple writable masters

**3.2 Consistency Levels**
```python
ConsistencyLevel:
- STRONG: Wait for all replicas (slowest, most consistent)
- EVENTUAL: Best effort (fastest, eventually consistent)
- QUORUM: Wait for majority (balanced)
```

### Usage Examples

**Enable Replication:**
```python
from bot.core.replication_manager import (
    ReplicationManager,
    ReplicationMode,
    ConsistencyLevel
)
from config.main_config import load_user_config

config = load_user_config()
replication = ReplicationManager.get_instance()

mode_map = {
    'master_slave': ReplicationMode.MASTER_SLAVE,
    'multi_master': ReplicationMode.MULTI_MASTER
}
consistency_map = {
    'strong': ConsistencyLevel.STRONG,
    'eventual': ConsistencyLevel.EVENTUAL,
    'quorum': ConsistencyLevel.QUORUM
}

mode = mode_map.get(config.get('REPLICATION_MODE', 'master_slave'))
consistency = consistency_map.get(config.get('REPLICATION_CONSISTENCY', 'eventual'))

await replication.enable(mode=mode, consistency=consistency)
```

**Check Replication Status:**
```python
status = await replication.get_replication_status()
print(f"Mode: {status['mode']}")
print(f"Master: {status['master_node']}")

for node_id, node_status in status['nodes'].items():
    print(f"{node_id}: lag={node_status['lag_seconds']}s")
```

---

## 4. Distributed State

### Overview
Manage shared state across cluster with ACID guarantees.

### Key Features

**4.1 Distributed State Operations**
- `set_state()`: Store value
- `get_state()`: Retrieve value
- `delete_state()`: Remove value
- `compare_and_swap()`: Atomic update

**4.2 Distributed Locks**
- Mutex locks with TTL
- Auto-extension
- Deadlock prevention

### Usage Examples

**Enable Distributed State:**
```python
from bot.core.distributed_state_manager import DistributedStateManager
from config.main_config import load_user_config

config = load_user_config()
state = DistributedStateManager.get_instance()
node_id = config.get('CLUSTER_NODE_ID', 'node-default')
await state.enable(node_id=node_id)
```

**State Operations:**
```python
# Set state
await state.set_state('config_version', 42)

# Get state
version = await state.get_state('config_version')
print(f"Version: {version}")

# Atomic compare-and-swap
success = await state.compare_and_swap(
    key='counter',
    expected=10,
    new_value=11
)
```

**Distributed Locks:**
```python
# Acquire lock
lock_id = await state.acquire_lock(
    resource_key='critical_section',
    ttl_seconds=30,
    timeout_seconds=10
)

if lock_id:
    try:
        # Do critical work
        await do_work()
    finally:
        # Release lock
        await state.release_lock('critical_section', lock_id)
```

---

## 5. Health Monitoring

### Overview
Comprehensive health checks with automatic recovery.

### Key Features

**5.1 Health Status**
```python
HealthStatus:
- HEALTHY: Fully operational
- DEGRADED: Partially operational
- UNHEALTHY: Not operational
- UNKNOWN: Status unknown
```

**5.2 Component Types**
```python
ComponentType:
- NODE: Cluster nodes
- DATABASE: Database systems
- CACHE: Cache systems (Redis)
- QUEUE: Message queues
- STORAGE: File storage
- API: API endpoints
- SERVICE: General services
```

### Usage Examples

**Enable Health Monitoring:**
```python
from bot.core.health_monitor import (
    HealthMonitor,
    ComponentType,
    HealthStatus
)
from config.main_config import load_user_config

config = load_user_config()
health = HealthMonitor.get_instance()

if config.get('HEALTH_MONITOR_ENABLED', False):
    await health.enable()
```

**Get Overall Health:**
```python
overall = await health.get_overall_health()
print(f"Status: {overall['status']}")
print(f"Healthy: {overall['healthy']}/{overall['total_components']}")

for name, component in overall['components'].items():
    print(f"{name}: {component['status']}")
```

---

## 6. Configuration

All Phase 5 configuration options are defined in [`config_enhancements_phase5.py`](../../config_enhancements_phase5.py).

### Preset Configurations

**Simple Failover (2 nodes):**
```python
from config_enhancements_phase5 import PHASE5_PRESETS
config = PHASE5_PRESETS['simple_failover']
```

**Full HA (3+ nodes):**
```python
config = PHASE5_PRESETS['full_ha']
```

**Distributed Cluster (5+ nodes):**
```python
config = PHASE5_PRESETS['distributed']
```

### Common Configurations

**Active-Passive (Primary + Standby):**
```python
config = {
    'CLUSTER_ENABLED': True,
    'FAILOVER_ENABLED': True,
    'HEALTH_MONITOR_ENABLED': True,
    'HA_STRATEGY': 'active_passive',
    'HA_MIN_NODES': 2,
}
```

**Active-Active (Load Balanced):**
```python
config = {
    'CLUSTER_ENABLED': True,
    'REPLICATION_ENABLED': True,
    'REPLICATION_MODE': 'multi_master',
    'DISTRIBUTED_STATE_ENABLED': True,
    'HA_STRATEGY': 'active_active',
    'HA_MIN_NODES': 3,
}
```

---

## 7. Use Cases

### Use Case 1: Zero-Downtime Deployments

**Scenario:** Update bot without service interruption

**Solution:**
```python
# Node 1: Primary serving requests
# Node 2: Secondary standby

# 1. Update Node 2 (secondary)
# 2. Trigger failover to Node 2
await failover.attempt_failback()  # Now Node 2 is primary

# 3. Update Node 1 (now secondary)
# 4. Failback to Node 1 when ready
```

### Use Case 2: Geographic Distribution

**Scenario:** Bot instances in multiple regions

**Solution:**
```python
# US East
config_us = {
    'CLUSTER_ENABLED': True,
    'CLUSTER_ADDRESS': 'us-east.example.com',
    'CLUSTER_SEED_NODES': ['eu-west.example.com:7946'],
    'REPLICATION_ENABLED': True,
}

# EU West
config_eu = {
    'CLUSTER_ENABLED': True,
    'CLUSTER_ADDRESS': 'eu-west.example.com',
    'CLUSTER_SEED_NODES': ['us-east.example.com:7946'],
    'REPLICATION_ENABLED': True,
}
```

### Use Case 3: Disaster Recovery

**Scenario:** Automatic recovery from node failures

**Solution:**
```python
config = {
    'FAILOVER_ENABLED': True,
    'FAILOVER_MODE': 'automatic',
    'FAILOVER_FAILURE_THRESHOLD': 3,
    'REPLICATION_ENABLED': True,
    'REPLICATION_CONSISTENCY': 'quorum',
    'HEALTH_MONITOR_ENABLED': True,
    'HEALTH_RECOVERY_ENABLED': True,
}
```

---

## 8. Best Practices

### 8.1 Cluster Size

**Minimum Recommendations:**
- **Simple Failover:** 2 nodes
- **Production HA:** 3 nodes (quorum-based)
- **Distributed:** 5+ nodes (multi-region)

**Why Odd Numbers?**
- Prevents split-brain scenarios
- Ensures clear majority for quorum
- Optimal: 3, 5, 7 nodes

### 8.2 Network Configuration

**Firewall Rules:**
```bash
# Cluster communication
Allow TCP 7946 (cluster port)

# Health check endpoints
Allow TCP 8080 (dashboard/API)
```

### 8.3 Consistency Trade-offs

**Use STRONG consistency when:**
- Financial transactions
- Critical state updates
- Absolute correctness required

**Use EVENTUAL consistency when:**
- Analytics data
- Logs
- Performance > consistency

**Use QUORUM when:**
- Balanced requirements
- Most production scenarios

### 8.4 Monitoring

**Essential Metrics:**
- Cluster membership changes
- Failover events
- Replication lag
- Health check failures
- Lock contention

---

## Next Steps

1. Review [Implementation Guide](PHASE_5_IMPLEMENTATION_GUIDE.md)
2. Choose appropriate HA strategy
3. Test in staging environment
4. Monitor and tune performance

**Integration:** See [TIER3_COMPLETION_FINAL_REPORT.md](TIER3_COMPLETION_FINAL_REPORT.md) for TIER 3 summary.
