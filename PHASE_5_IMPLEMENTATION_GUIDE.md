# Phase 5: High Availability Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing High Availability in the mirror-leech-telegram-bot.

**Difficulty:** ⭐⭐⭐⭐ Advanced  
**Time Required:** 2-4 hours  
**Prerequisites:** Phase 1-4 (optional but recommended)

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Architecture Overview](#2-architecture-overview)
3. [Implementation Steps](#3-implementation-steps)
4. [Configuration Guide](#4-configuration-guide)
5. [Deployment Scenarios](#5-deployment-scenarios)
6. [Testing](#6-testing)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Quick Start

### Minimal Setup (Development)

**Step 1: Update `config.py`**
```python
# Enable basic HA components
CLUSTER_ENABLED = True
HEALTH_MONITOR_ENABLED = True
```

**Step 2: Initialize in bot**
```python
# In bot/__main__.py
from bot.core.enhanced_startup_phase5 import initialize_phase5

# Load config
config = {...}  # Your config dict

# Initialize Phase 5
await initialize_phase5(config)
```

**Step 3: Run bot**
```bash
python -m bot
```

### Production Setup (3-Node Cluster)

**Node 1 config:**
```python
CLUSTER_ENABLED = True
CLUSTER_NODE_ID = 'node-1'
CLUSTER_ADDRESS = '10.0.1.10'
CLUSTER_PORT = 7946
CLUSTER_SEED_NODES = ['10.0.1.11:7946', '10.0.1.12:7946']
FAILOVER_ENABLED = True
FAILOVER_PRIMARY_NODE = 'node-1'
REPLICATION_ENABLED = True
REPLICATION_MASTER_NODE = 'node-1'
```

**Node 2 & 3 config:**
```python
# Similar to Node 1, change:
CLUSTER_NODE_ID = 'node-2'  # or 'node-3'
CLUSTER_ADDRESS = '10.0.1.11'  # or '10.0.1.12'
FAILOVER_SECONDARY_NODES = ['node-1']
REPLICATION_SLAVE_NODES = ['node-1']
```

---

## 2. Architecture Overview

### Component Relationships

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│   (Telegram Bot / Web Dashboard)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│         High Availability Layer         │
│                                         │
│  ┌─────────────────┐  ┌──────────────┐ │
│  │ Cluster Manager │  │Health Monitor│ │
│  │ (Membership)    │  │(Monitoring)  │ │
│  └────────┬────────┘  └──────┬───────┘ │
│           │                  │         │
│  ┌────────┴────────┐  ┌──────┴───────┐ │
│  │Failover Manager │  │ Distributed  │ │
│  │(Recovery)       │  │ State Mgr    │ │
│  └────────┬────────┘  └──────┬───────┘ │
│           │                  │         │
│  ┌────────┴──────────────────┴───────┐ │
│  │    Replication Manager             │ │
│  │    (Data Sync)                     │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│       Infrastructure Layer              │
│   (Network / Storage / Database)        │
└─────────────────────────────────────────┘
```

### Data Flow

**Normal Operation:**
```
Client Request
    ↓
Leader Node (Primary)
    ↓
Process Request
    ↓
Replicate to Secondaries
    ↓
Response to Client
```

**Failover Scenario:**
```
Leader Node Fails
    ↓
Health Monitor Detects
    ↓
Failover Manager Triggered
    ↓
Secondary Elected as Leader
    ↓
State Transferred
    ↓
Resume Operations
```

---

## 3. Implementation Steps

### Step 1: Install Dependencies

**Add to `requirements.txt`:**
```
psutil>=5.9.0  # For system metrics
```

**Install:**
```bash
pip install -r requirements.txt
```

### Step 2: Import Phase 5 Components

**In `bot/__main__.py`:**
```python
import asyncio
from bot.core.enhanced_startup_phase5 import (
    initialize_phase5,
    get_phase5_status,
    shutdown_phase5
)
from config_enhancements_phase5 import get_phase5_config
```

### Step 3: Initialize During Startup

**Add to bot initialization:**
```python
async def start_bot():
    """Start bot with HA"""
    try:
        # Load config
        config = {
            **get_phase5_config(),
            **load_user_config()
        }
        
        # Initialize Phase 5
        print("Initializing High Availability...")
        success = await initialize_phase5(config)
        
        if not success:
            print("Warning: HA initialization failed, continuing without HA")
        
        # Start bot
        await bot.start()
        print("Bot started successfully!")
        
        # Keep running
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await shutdown_phase5()
        await bot.stop()

if __name__ == '__main__':
    asyncio.run(start_bot())
```

### Step 4: Add Health Check Endpoint

**For web dashboard (`bot/core/web_dashboard.py`):**
```python
@app.get("/health")
async def health_endpoint():
    """Health check endpoint"""
    from bot.core.enhanced_startup_phase5 import get_phase5_status
    
    status = await get_phase5_status()
    
    if status.get('enabled'):
        health_status = status.get('health_status', {})
        overall_status = health_status.get('status', 'unknown')
        
        return {
            'status': overall_status,
            'details': status
        }
    
    return {'status': 'healthy', 'ha_enabled': False}
```

### Step 5: Add Status Command

**In `bot/modules/stats.py`:**
```python
async def ha_status_command(client, message):
    """Show HA status"""
    from bot.core.enhanced_startup_phase5 import get_phase5_status
    
    status = await get_phase5_status()
    
    if not status.get('enabled'):
        await message.reply("High Availability is not enabled")
        return
    
    # Format status message
    text = "🔄 <b>High Availability Status</b>\n\n"
    
    # Cluster info
    if 'cluster_info' in status:
        cluster = status['cluster_info']
        text += f"<b>Cluster:</b>\n"
        text += f"├ State: {cluster['state']}\n"
        text += f"├ Nodes: {cluster['total_nodes']} ({cluster['active_nodes']} active)\n"
        text += f"└ Leader: {cluster['leader_node']}\n\n"
    
    # Failover info
    if 'failover_status' in status:
        failover = status['failover_status']
        text += f"<b>Failover:</b>\n"
        text += f"├ State: {failover['state']}\n"
        text += f"└ Primary: {failover['primary_node']}\n\n"
    
    # Health info
    if 'health_status' in status:
        health = status['health_status']
        text += f"<b>Health:</b>\n"
        text += f"├ Status: {health['status']}\n"
        text += f"└ Healthy: {health['healthy']}/{health['total_components']}\n"
    
    await message.reply(text)
```

---

## 4. Configuration Guide

### Basic Configuration

**Minimal (Single Node):**
```python
config = {
    'CLUSTER_ENABLED': True,
    'HEALTH_MONITOR_ENABLED': True,
}
```

**Development (2 Nodes):**
```python
config = {
    'CLUSTER_ENABLED': True,
    'FAILOVER_ENABLED': True,
    'HEALTH_MONITOR_ENABLED': True,
    'HA_MIN_NODES': 2,
}
```

**Production (3+ Nodes):**
```python
config = {
    'CLUSTER_ENABLED': True,
    'FAILOVER_ENABLED': True,
    'REPLICATION_ENABLED': True,
    'DISTRIBUTED_STATE_ENABLED': True,
    'HEALTH_MONITOR_ENABLED': True,
    'HA_MIN_NODES': 3,
    'HA_QUORUM_SIZE': 2,
}
```

### Advanced Configuration

**Strong Consistency:**
```python
config = {
    'REPLICATION_CONSISTENCY': 'strong',
    'DATA_CONSISTENCY_LEVEL': 'strong',
}
```

**Automatic Recovery:**
```python
config = {
    'FAILOVER_MODE': 'automatic',
    'HEALTH_RECOVERY_ENABLED': True,
    'FAILOVER_MAX_ATTEMPTS': 3,
}
```

**Monitoring & Alerts:**
```python
config = {
    'HA_MONITORING_ENABLED': True,
    'HA_ALERT_ON_FAILOVER': True,
    'HA_ALERT_ON_NODE_DOWN': True,
    'HA_ALERT_ON_SPLIT_BRAIN': True,
}
```

---

## 5. Deployment Scenarios

### Scenario 1: Docker Compose (3 Nodes)

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  bot-node-1:
    build: .
    environment:
      - CLUSTER_ENABLED=True
      - CLUSTER_NODE_ID=node-1
      - CLUSTER_ADDRESS=bot-node-1
      - CLUSTER_PORT=7946
      - CLUSTER_SEED_NODES=bot-node-2:7946,bot-node-3:7946
      - FAILOVER_ENABLED=True
      - FAILOVER_PRIMARY_NODE=node-1
    ports:
      - "8080:8080"
      - "7946:7946"
    networks:
      - botnet

  bot-node-2:
    build: .
    environment:
      - CLUSTER_ENABLED=True
      - CLUSTER_NODE_ID=node-2
      - CLUSTER_ADDRESS=bot-node-2
      - CLUSTER_SEED_NODES=bot-node-1:7946,bot-node-3:7946
      - FAILOVER_ENABLED=True
      - FAILOVER_SECONDARY_NODES=node-1
    ports:
      - "8081:8080"
      - "7947:7946"
    networks:
      - botnet

  bot-node-3:
    build: .
    environment:
      - CLUSTER_ENABLED=True
      - CLUSTER_NODE_ID=node-3
      - CLUSTER_ADDRESS=bot-node-3
      - CLUSTER_SEED_NODES=bot-node-1:7946,bot-node-2:7946
      - FAILOVER_ENABLED=True
      - FAILOVER_SECONDARY_NODES=node-1
    ports:
      - "8082:8080"
      - "7948:7946"
    networks:
      - botnet

networks:
  botnet:
    driver: bridge
```

**Start cluster:**
```bash
docker-compose up -d
```

### Scenario 2: Kubernetes (StatefulSet)

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: bot-cluster
spec:
  serviceName: bot-cluster
  replicas: 3
  selector:
    matchLabels:
      app: bot
  template:
    metadata:
      labels:
        app: bot
    spec:
      containers:
      - name: bot
        image: mirror-leech-bot:latest
        env:
        - name: CLUSTER_ENABLED
          value: "True"
        - name: CLUSTER_NODE_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: CLUSTER_SEED_NODES
          value: "bot-cluster-0.bot-cluster:7946,bot-cluster-1.bot-cluster:7946,bot-cluster-2.bot-cluster:7946"
        - name: FAILOVER_ENABLED
          value: "True"
        - name: REPLICATION_ENABLED
          value: "True"
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 7946
          name: cluster
---
apiVersion: v1
kind: Service
metadata:
  name: bot-cluster
spec:
  clusterIP: None
  selector:
    app: bot
  ports:
  - port: 7946
    name: cluster
  - port: 8080
    name: http
```

**Deploy:**
```bash
kubectl apply -f deployment.yaml
```

### Scenario 3: Cloud VMs (AWS/GCP/Azure)

**Setup (3 VMs):**
```bash
# Node 1 (10.0.1.10)
export CLUSTER_ENABLED=True
export CLUSTER_NODE_ID=aws-us-east-1a
export CLUSTER_ADDRESS=10.0.1.10
export CLUSTER_SEED_NODES=10.0.1.11:7946,10.0.1.12:7946
export FAILOVER_PRIMARY_NODE=aws-us-east-1a
python -m bot

# Node 2 (10.0.1.11)
export CLUSTER_ENABLED=True
export CLUSTER_NODE_ID=aws-us-east-1b
export CLUSTER_ADDRESS=10.0.1.11
export CLUSTER_SEED_NODES=10.0.1.10:7946,10.0.1.12:7946
export FAILOVER_SECONDARY_NODES=aws-us-east-1a
python -m bot

# Node 3 (10.0.1.12)
export CLUSTER_ENABLED=True
export CLUSTER_NODE_ID=aws-us-east-1c
export CLUSTER_ADDRESS=10.0.1.12
export CLUSTER_SEED_NODES=10.0.1.10:7946,10.0.1.11:7946
export FAILOVER_SECONDARY_NODES=aws-us-east-1a
python -m bot
```

---

## 6. Testing

### Test 1: Cluster Formation

```bash
# Start Node 1
python -m bot

# Verify cluster
curl http://localhost:8080/health

# Start Nodes 2 & 3
# Verify all nodes joined cluster
```

### Test 2: Leader Election

```python
from bot.core.cluster_manager import ClusterManager

cluster = ClusterManager.get_instance()
info = await cluster.get_cluster_info()
print(f"Leader: {info['leader_node']}")
```

### Test 3: Failover

```bash
# Stop primary node
docker stop bot-node-1

# Wait 15 seconds

# Check new leader
curl http://localhost:8081/health
```

### Test 4: Data Replication

```python
from bot.core.replication_manager import ReplicationManager

replication = ReplicationManager.get_instance()

# Replicate data
await replication.replicate_data(
    data_id='test',
    data_type='task',
    data={'test': 'data'}
)

# Check status
status = await replication.get_replication_status()
print(f"Replicated: {status['replicated_items']}")
```

### Test 5: Distributed Locks

```python
from bot.core.distributed_state_manager import DistributedStateManager

state = DistributedStateManager.get_instance()

# Acquire lock
lock_id = await state.acquire_lock('resource', ttl_seconds=30)
assert lock_id is not None

# Try to acquire again (should fail)
lock_id2 = await state.acquire_lock('resource', timeout_seconds=1)
assert lock_id2 is None

# Release
await state.release_lock('resource', lock_id)
```

---

## 7. Troubleshooting

### Issue 1: Nodes Not Joining Cluster

**Symptoms:**
- Nodes remain in JOINING state
- Can't connect to seed nodes

**Solutions:**
```bash
# Check network connectivity
ping <seed_node_ip>
telnet <seed_node_ip> 7946

# Check firewall rules
sudo ufw allow 7946/tcp

# Verify cluster config
echo $CLUSTER_SEED_NODES
```

### Issue 2: Split-Brain Detected

**Symptoms:**
- Multiple leaders elected
- Cluster state: SPLIT_BRAIN

**Solutions:**
```python
# Check quorum settings
config = {
    'HA_QUORUM_SIZE': 2,  # For 3 nodes
    'SPLIT_BRAIN_PREVENTION': True,
}

# Manually trigger re-election
cluster = ClusterManager.get_instance()
await cluster._trigger_election()
```

### Issue 3: High Replication Lag

**Symptoms:**
- `lag_seconds` > 60
- Data inconsistency

**Solutions:**
```python
# Check replication mode
config = {
    'REPLICATION_CONSISTENCY': 'eventual',  # Use eventual for better performance
    'REPLICATION_BATCH_SIZE': 100,
}

# Monitor lag
status = await replication.get_replication_status()
for node, info in status['nodes'].items():
    if info['lag_seconds'] > 60:
        print(f"Warning: {node} lag: {info['lag_seconds']}s")
```

### Issue 4: Failover Not Triggering

**Symptoms:**
- Primary down, no failover
- Failover state stuck

**Solutions:**
```python
# Check failover config
config = {
    'FAILOVER_MODE': 'automatic',  # Ensure automatic
    'FAILOVER_FAILURE_THRESHOLD': 3,  # Lower threshold
    'FAILOVER_HEALTH_CHECK_INTERVAL': 5,
}

# Manually trigger failover
failover = FailoverManager.get_instance()
await failover._trigger_failover()
```

### Issue 5: Lock Deadlocks

**Symptoms:**
- Tasks stuck waiting for locks
- Lock acquisition timeouts

**Solutions:**
```python
# Always use timeouts
lock_id = await state.acquire_lock(
    'resource',
    ttl_seconds=30,
    timeout_seconds=10  # Don't wait forever
)

# Use try-finally
try:
    # Critical section
    pass
finally:
    if lock_id:
        await state.release_lock('resource', lock_id)

# Enable auto-cleanup
config = {
    'DISTRIBUTED_LOCK_AUTO_EXTEND': True,
}
```

---

## Performance Tuning

### Network Optimization

```python
config = {
    'CLUSTER_HEARTBEAT_INTERVAL': 3,  # Faster detection (default: 5)
    'CLUSTER_NODE_TIMEOUT': 10,  # Lower timeout (default: 15)
    'HA_NETWORK_TIMEOUT': 5,  # Faster network timeout
    'HA_COMPRESSION_ENABLED': True,  # Compress cluster messages
}
```

### Replication Optimization

```python
config = {
    'REPLICATION_ASYNC_WRITES': True,  # Don't block on writes
    'REPLICATION_BATCH_SIZE': 200,  # Larger batches
    'REPLICATION_CONSISTENCY': 'eventual',  # Eventual for speed
}
```

### Health Check Optimization

```python
config = {
    'HEALTH_CHECK_INTERVAL': 60,  # Less frequent checks
    'HEALTH_CHECK_TIMEOUT': 3,  # Faster timeout
    'HEALTH_FAILURE_THRESHOLD': 2,  # Faster detection
}
```

---

## Next Steps

1. **Development:** Test with 2-node setup locally
2. **Staging:** Deploy 3-node cluster in test environment
3. **Production:** Roll out to production with monitoring
4. **Optimization:** Tune based on metrics and load

**Complete!** Phase 5 High Availability is now implemented and ready for production use.

For questions or issues, refer to [PHASE_5_FEATURES.md](PHASE_5_FEATURES.md) or create a GitHub issue.
