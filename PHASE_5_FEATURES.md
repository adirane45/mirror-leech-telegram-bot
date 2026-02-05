# Phase 5: High Availability Features Guide

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

**1.4 Cluster States**
```python
ClusterState:
- FORMING: Initial cluster formation
- STABLE: All nodes healthy
- DEGRADED: Some nodes unhealthy
- SPLIT_BRAIN: Network partition detected
```

### Usage Examples

**Enable Clustering:**
```python
from bot.core.cluster_manager import ClusterManager

cluster = ClusterManager.get_instance()

# Start standalone cluster
await cluster.enable(
    address='192.168.1.100',
    port=7946
)

# Join existing cluster
await cluster.enable(
    address='192.168.1.100',
    port=7946,
    seed_nodes=['192.168.1.101:7946', '192.168.1.102:7946']
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

### Configuration

```python
'CLUSTER_ENABLED': False,
'CLUSTER_NODE_ID': None,  # Auto-generated
'CLUSTER_ADDRESS': '0.0.0.0',
'CLUSTER_PORT': 7946,
'CLUSTER_SEED_NODES': [],
'CLUSTER_HEARTBEAT_INTERVAL': 5,  # seconds
'CLUSTER_NODE_TIMEOUT': 15,  # seconds
'CLUSTER_ELECTION_TIMEOUT': 10,
'CLUSTER_NODE_PRIORITY': 100,
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

**2.4 Health Checks**
- Configurable check intervals
- Failure thresholds
- Automatic recovery attempts

### Usage Examples

**Enable Failover:**
```python
from bot.core.failover_manager import (
    FailoverManager,
    FailoverPolicy,
    FailoverRole
)

failover = FailoverManager.get_instance()

policy = FailoverPolicy(
    auto_failover_enabled=True,
    failure_threshold=3,
    health_check_interval=5,
    recovery_wait_time=60
)

await failover.enable(role=FailoverRole.PRIMARY, policy=policy)
```

**Configure Primary/Secondary:**
```python
# Set primary node
await failover.set_primary('node-1')

# Add secondary nodes
await failover.add_secondary('node-2')
await failover.add_secondary('node-3')
```

**Check Failover Status:**
```python
status = await failover.get_failover_status()
print(f"State: {status['state']}")
print(f"Primary: {status['primary_node']}")
print(f"Secondaries: {status['secondary_nodes']}")
```

**Trigger Manual Failback:**
```python
success = await failover.attempt_failback()
if success:
    print("Failback successful")
```

### Configuration

```python
'FAILOVER_ENABLED': False,
'FAILOVER_MODE': 'automatic',
'FAILOVER_TIMEOUT': 30,
'FAILOVER_HEALTH_CHECK_INTERVAL': 5,
'FAILOVER_FAILURE_THRESHOLD': 3,
'FAILOVER_RECOVERY_WAIT_TIME': 60,
'FAILOVER_MAX_ATTEMPTS': 3,
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

**3.3 Conflict Resolution**
```python
ConflictResolution:
- LAST_WRITE_WINS: Newest timestamp wins
- FIRST_WRITE_WINS: Original value preserved
- MERGE: Attempt to merge changes
- MANUAL: Require manual intervention
```

**3.4 Replication Monitoring**
- Replication lag tracking
- Success/failure statistics
- Conflict history

### Usage Examples

**Enable Replication:**
```python
from bot.core.replication_manager import (
    ReplicationManager,
    ReplicationMode,
    ConsistencyLevel
)

replication = ReplicationManager.get_instance()

await replication.enable(
    mode=ReplicationMode.MASTER_SLAVE,
    consistency=ConsistencyLevel.QUORUM
)
```

**Configure Master/Slaves:**
```python
# Set master
await replication.set_master('node-master')

# Add slaves
await replication.add_slave('node-slave-1')
await replication.add_slave('node-slave-2')
```

**Replicate Data:**
```python
await replication.replicate_data(
    data_id='task_123',
    data_type='download_task',
    data={'url': 'https://example.com/file.zip', 'status': 'downloading'},
    source_node='node-master'
)
```

**Check Replication Status:**
```python
status = await replication.get_replication_status()
print(f"Mode: {status['mode']}")
print(f"Master: {status['master_node']}")

for node_id, node_status in status['nodes'].items():
    print(f"{node_id}: lag={node_status['lag_seconds']}s")
```

**View Conflicts:**
```python
conflicts = await replication.get_conflicts(limit=10)
for conflict in conflicts:
    print(f"Data: {conflict['data_id']}")
    print(f"Resolution: {conflict['resolution']}")
```

### Configuration

```python
'REPLICATION_ENABLED': False,
'REPLICATION_MODE': 'master_slave',
'REPLICATION_CONSISTENCY': 'eventual',
'REPLICATION_CONFLICT_RESOLUTION': 'last_write_wins',
'REPLICATION_SYNC_INTERVAL': 5,
'REPLICATION_BATCH_SIZE': 100,
'REPLICATION_REPLICATE_TASKS': True,
'REPLICATION_REPLICATE_CONFIG': True,
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

**4.3 Version Vectors**
- Conflict detection
- Causal consistency
- Concurrent update tracking

### Usage Examples

**Enable Distributed State:**
```python
from bot.core.distributed_state_manager import DistributedStateManager

state = DistributedStateManager.get_instance()
await state.enable(node_id='node-1')
```

**State Operations:**
```python
# Set state
await state.set_state('config_version', 42)

# Get state
version = await state.get_state('config_version')
print(f"Version: {version}")

# Delete state
await state.delete_state('config_version')

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

**Lock Extension:**
```python
# Extend lock TTL
success = await state.extend_lock(
    resource_key='critical_section',
    lock_id=lock_id,
    ttl_seconds=60
)
```

### Configuration

```python
'DISTRIBUTED_STATE_ENABLED': False,
'DISTRIBUTED_STATE_BACKEND': 'memory',
'DISTRIBUTED_STATE_SYNC_INTERVAL': 5,
'DISTRIBUTED_LOCKS_ENABLED': False,
'DISTRIBUTED_LOCK_DEFAULT_TTL': 30,
'DISTRIBUTED_LOCK_AUTO_EXTEND': True,
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

**5.3 Auto-Recovery**
- Configurable recovery callbacks
- Automatic restart attempts
- Recovery tracking

### Usage Examples

**Enable Health Monitoring:**
```python
from bot.core.health_monitor import (
    HealthMonitor,
    ComponentType,
    HealthStatus
)

health = HealthMonitor.get_instance()
await health.enable()
```

**Register Health Check:**
```python
async def check_database():
    try:
        # Check database connection
        await db.ping()
        return {'status': HealthStatus.HEALTHY}
    except Exception as e:
        return {
            'status': HealthStatus.UNHEALTHY,
            'error': str(e)
        }

await health.register_health_check(
    check_id='mongodb',
    component_type=ComponentType.DATABASE,
    component_name='mongodb',
    check_fn=check_database,
    interval_seconds=30,
    timeout_seconds=5,
    failure_threshold=3
)
```

**Register Recovery Callback:**
```python
async def recover_database(result):
    print(f"Recovering database: {result.error}")
    # Attempt reconnection
    await db.reconnect()

await health.register_recovery_callback(
    component_name='mongodb',
    callback=recover_database
)
```

**Get Overall Health:**
```python
overall = await health.get_overall_health()
print(f"Status: {overall['status']}")
print(f"Healthy: {overall['healthy']}/{overall['total_components']}")

for name, component in overall['components'].items():
    print(f"{name}: {component['status']}")
```

### Configuration

```python
'HEALTH_MONITOR_ENABLED': False,
'HEALTH_CHECK_INTERVAL': 30,
'HEALTH_CHECK_TIMEOUT': 5,
'HEALTH_FAILURE_THRESHOLD': 3,
'HEALTH_RECOVERY_ENABLED': True,
'HEALTH_CHECK_NODES': True,
'HEALTH_CHECK_DATABASE': True,
'HEALTH_CHECK_CACHE': True,
```

---

## 6. Configuration

### Preset Configurations

**Simple Failover (2 nodes):**
```python
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

**Development:**
```python
config = PHASE5_PRESETS['development']
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

**Network Latency:**
- Same datacenter: < 1ms (ideal)
- Same region: < 10ms (acceptable)
- Cross-region: < 100ms (challenges with strong consistency)

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

**Alert Thresholds:**
```python
config = {
    'HA_ALERT_ON_FAILOVER': True,
    'HA_ALERT_ON_NODE_DOWN': True,
    'HA_ALERT_ON_SPLIT_BRAIN': True,
    'HA_REPLICATION_LAG_THRESHOLD': 60,  # seconds
}
```

### 8.5 Testing

**Chaos Testing:**
```python
# Test failover
await cluster.disable()  # Simulate node crash

# Test split-brain
# Partition network temporarily

# Test recovery
await failover.attempt_failback()
```

**Load Testing:**
- Test under production load
- Measure failover time
- Check replication lag under stress

---

## Summary

Phase 5 provides enterprise-grade High Availability with:

✅ **Cluster Management** - Automatic membership and leader election  
✅ **Failover** - Zero-downtime automatic failover  
✅ **Replication** - Multi-node data redundancy  
✅ **Distributed State** - Cluster-wide state with locks  
✅ **Health Monitoring** - Comprehensive health checks  

**Next Steps:**
1. Review [Implementation Guide](PHASE_5_IMPLEMENTATION_GUIDE.md)
2. Choose appropriate HA strategy
3. Test in staging environment
4. Monitor and tune performance

**Questions?** Check the implementation guide or file an issue on GitHub.
