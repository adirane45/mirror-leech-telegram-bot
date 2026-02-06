# TIER 3: Phase 5 - High Availability Quick Reference

> **Part of TIER 3: Production Deployment**  
> **Updated:** February 6, 2026

## Quick Start

### Enable Phase 5 (3-step setup)

**1. Update Configuration:**
```python
from config.config_enhancements_phase5 import PHASE5_PRESETS

# Choose your deployment model
config = PHASE5_PRESETS['simple_failover']  # 2 nodes
config = PHASE5_PRESETS['full_ha']          # 3 nodes
config = PHASE5_PRESETS['distributed']      # 5+ nodes
```

**2. Initialize in Bot:**
```python
from bot.core.enhanced_startup import initialize_phase5

await initialize_phase5(config)
```

**3. Run:**
```bash
python -m bot
```

---

## Component Summary

| Component | Purpose | Default | When to Use |
|-----------|---------|---------|-------------|
| **Cluster Manager** | Node discovery & leader election | Disabled | 2+ nodes |
| **Failover Manager** | Automatic node recovery | Disabled | High availability required |
| **Replication Manager** | Data sync across nodes | Disabled | Data consistency required |
| **Distributed State** | Cluster-wide locks & state | Disabled | Distributed operations |
| **Health Monitor** | Continuous health checks | Disabled | Production deployments |

---

## Configuration Presets

### Development (Single Node)
```python
PHASE5_PRESETS['development']
# CLUSTER_ENABLED: True
# Features: Basic cluster + health monitoring
# Use for: Development/testing
```

### Simple Failover (2 Nodes)
```python
PHASE5_PRESETS['simple_failover']
# CLUSTER_ENABLED: True
# FAILOVER_ENABLED: True
# HEALTH_MONITOR_ENABLED: True
# Use for: Simple active-passive setup
```

### Full HA (3+ Nodes)
```python
PHASE5_PRESETS['full_ha']
# All components enabled
# REPLICATION_CONSISTENCY: quorum
# Use for: Production multi-node cluster
```

### Distributed (5+ Nodes)
```python
PHASE5_PRESETS['distributed']
# All features enabled, multi-master replication
# Use for: Large-scale distributed deployments
```

---

## API Quick Reference

### Cluster Management
```python
cluster = ClusterManager.get_instance()

# Get cluster info
info = await cluster.get_cluster_info()
# Returns: {total_nodes, active_nodes, leader_node, state, is_healthy}

# Get leader
leader = await cluster.get_leader_node()
# Returns: {node_id, address, port}
```

### Failover Management
```python
failover = FailoverManager.get_instance()

# Check status
status = await failover.get_failover_status()
# Returns: {state, primary_node, secondary_nodes}

# Manual failback
success = await failover.attempt_failback()
```

### Replication Management
```python
replication = ReplicationManager.get_instance()

# Replicate data
await replication.replicate_data(
    data_id='task-123',
    data_type='download_task',
    data={...}
)

# Check status
status = await replication.get_replication_status()
# Returns: {mode, master_node, nodes, replicated_items}
```

### Distributed Locks
```python
state = DistributedStateManager.get_instance()

# Acquire lock
lock_id = await state.acquire_lock('resource', timeout_seconds=10)

# Release lock
await state.release_lock('resource', lock_id)
```

### Health Monitoring
```python
health = HealthMonitor.get_instance()

# Get overall health
status = await health.get_overall_health()
# Returns: {status, healthy, total_components, components}
```

---

## Configuration Options

All options in `config/config_enhancements_phase5.py`:

### Cluster Options
```python
'CLUSTER_ENABLED': False
'CLUSTER_NODE_ID': None              # Auto-generated
'CLUSTER_ADDRESS': '0.0.0.0'
'CLUSTER_PORT': 7946
'CLUSTER_SEED_NODES': []             # List of seed nodes
'CLUSTER_HEARTBEAT_INTERVAL': 5      # seconds
'CLUSTER_NODE_TIMEOUT': 15           # seconds
'CLUSTER_ELECTION_TIMEOUT': 10       # seconds
'CLUSTER_NODE_PRIORITY': 100         # Higher = more likely leader
```

### Failover Options
```python
'FAILOVER_ENABLED': False
'FAILOVER_MODE': 'automatic'         # automatic or manual
'FAILOVER_TIMEOUT': 30               # seconds
'FAILOVER_HEALTH_CHECK_INTERVAL': 5  # seconds
'FAILOVER_FAILURE_THRESHOLD': 3      # consecutive failures
'FAILOVER_RECOVERY_WAIT_TIME': 60    # seconds
'FAILOVER_MAX_ATTEMPTS': 3
```

### Replication Options
```python
'REPLICATION_ENABLED': False
'REPLICATION_MODE': 'master_slave'   # master_slave or multi_master
'REPLICATION_CONSISTENCY': 'eventual' # strong, eventual, or quorum
'REPLICATION_SYNC_INTERVAL': 5        # seconds
'REPLICATION_BATCH_SIZE': 100
'REPLICATION_ASYNC_WRITES': True
```

### Health Monitor Options
```python
'HEALTH_MONITOR_ENABLED': False
'HEALTH_CHECK_INTERVAL': 30           # seconds
'HEALTH_CHECK_TIMEOUT': 5             # seconds
'HEALTH_FAILURE_THRESHOLD': 3         # consecutive failures
'HEALTH_RECOVERY_ENABLED': True
```

### HA Strategy
```python
'HA_STRATEGY': 'active_passive'  # active_passive, active_active, distributed
'HA_MIN_NODES': 2
'HA_QUORUM_SIZE': 2              # Minimum for quorum
'SPLIT_BRAIN_PREVENTION': True
```

---

## Deployment Quick Links

| Scenario | Setup | Guide |
|----------|-------|-------|
| Docker Compose (3 nodes) | `docker-compose.yml` with 3 services | PHASE_5_IMPLEMENTATION_GUIDE.md #5 |
| Kubernetes | StatefulSet (3 replicas) | PHASE_5_IMPLEMENTATION_GUIDE.md #5 |
| Cloud VMs | Environment variables | PHASE_5_IMPLEMENTATION_GUIDE.md #5 |

---

## Common Tasks

### Enable 3-Node HA Cluster
```python
from config.config_enhancements_phase5 import PHASE5_PRESETS

config = PHASE5_PRESETS['full_ha']
await initialize_phase5(config)
```

### Enable Failover Only
```python
config = {
    'CLUSTER_ENABLED': True,
    'FAILOVER_ENABLED': True,
    'HEALTH_MONITOR_ENABLED': True,
    'HA_MIN_NODES': 2,
}
await initialize_phase5(config)
```

### Enable Multi-Master Replication
```python
config = PHASE5_PRESETS['distributed']
config['REPLICATION_MODE'] = 'multi_master'
config['REPLICATION_CONSISTENCY'] = 'quorum'
await initialize_phase5(config)
```

### Acquire Distributed Lock
```python
lock_id = await state.acquire_lock(
    'critical_section',
    ttl_seconds=30,
    timeout_seconds=10
)
if lock_id:
    try:
        # Do work
        pass
    finally:
        await state.release_lock('critical_section', lock_id)
```

---

## Health Endpoint

```bash
# Check HA status
curl http://localhost:8080/health

# Response (with HA enabled):
{
  "status": "healthy",
  "ha_enabled": true,
  "ha_details": {
    "enabled": true,
    "cluster_info": {...},
    "failover_status": {...},
    "health_status": {...}
  }
}
```

---

## Troubleshooting

### Nodes not joining
```bash
# Check network
ping <seed_node_ip>
telnet <seed_node_ip> 7946

# Check firewall
sudo ufw allow 7946/tcp
```

### High replication lag
```python
# Switch to eventual consistency
config['REPLICATION_CONSISTENCY'] = 'eventual'
config['REPLICATION_BATCH_SIZE'] = 250
```

### Failover not triggering
```python
# Check config
assert config['FAILOVER_MODE'] == 'automatic'
assert config['FAILOVER_FAILURE_THRESHOLD'] <= 5
```

---

## Performance Tuning

### For Low Latency Networks
```python
config = {
    'CLUSTER_HEARTBEAT_INTERVAL': 1,      # Faster detection
    'CLUSTER_NODE_TIMEOUT': 3,
    'FAILOVER_HEALTH_CHECK_INTERVAL': 2,
}
```

### For High Throughput
```python
config = {
    'REPLICATION_BATCH_SIZE': 500,        # Larger batches
    'REPLICATION_CONSISTENCY': 'eventual',
    'HA_CONNECTION_POOL_SIZE': 20,
}
```

### For Eventual Consistency
```python
config = {
    'REPLICATION_CONSISTENCY': 'eventual',
    'REPLICATION_ASYNC_WRITES': True,
    'HEALTH_CHECK_INTERVAL': 60,          # Less frequent
}
```

---

## Files Location

| File | Location | Purpose |
|------|----------|---------|
| Config | `config/config_enhancements_phase5.py` | Configuration functions & presets |
| Features Guide | `docs/TIER3/PHASE_5_FEATURES.md` | Feature documentation |
| Implementation | `docs/TIER3/PHASE_5_IMPLEMENTATION_GUIDE.md` | Step-by-step setup |
| Quick Ref | `docs/TIER3/PHASE_5_QUICK_REFERENCE.md` | This file |

---

## Integration

Phase 5 integrates with:
- ✅ **Phase 4 (TIER 2)** - Query optimization & caching
- ✅ **Database Repositories** - Full replication support
- ✅ **Docker Compose** - Standard setup
- ✅ **Kubernetes** - StatefulSet deployment

See [TIER3_COMPLETION_FINAL_REPORT.md](TIER3_COMPLETION_FINAL_REPORT.md) for complete TIER 3 status.

---

## Next Steps

1. Choose deployment model (development, simple_failover, full_ha, distributed)
2. Update configuration
3. Run Phase 5 initialization
4. Test failover scenarios
5. Monitor and tune
