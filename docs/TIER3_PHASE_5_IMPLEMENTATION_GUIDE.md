# TIER 3: Phase 5 - High Availability Implementation Guide

> **Part of TIER 3: Production Deployment**  
> **Status:** ✅ Ready for Implementation  
> **Last Updated:** February 6, 2026

## Overview

This guide provides step-by-step instructions for implementing High Availability in the mirror-leech-telegram-bot. Phase 5 is part of TIER 3 production deployment enhancements.

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

**Step 1: Update `config/main_config.py`**
```python
# Enable basic HA components
CLUSTER_ENABLED = True
HEALTH_MONITOR_ENABLED = True
```

**Step 2: Initialize in bot**
```python
# In bot/__main__.py
from bot.core.enhanced_startup import initialize_phase5
from config.main_config import load_user_config

# Load config
config = load_user_config()

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

Phase 5 High Availability integrates with the existing MLTB architecture:

```
┌──────────────────────────────────────────┐
│     Application Layer (Telegram Bot)     │
│  bot/__main__.py + bot/modules/          │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────┴───────────────────────┐
│   Phase 5: High Availability Layer        │
│   bot/core/                               │
│  ├─ cluster_manager.py                  │
│  ├─ failover_manager.py                 │
│  ├─ replication_manager.py              │
│  ├─ distributed_state_manager.py        │
│  └─ health_monitor.py                   │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────┴───────────────────────┐
│  Existing TIER 2/3 Components             │
│  bot/core/ (QueryOptimizer, etc.)        │
│  bot/helper/ext_utils/db_repositories/   │
└──────────────────┬───────────────────────┘
                   │
┌──────────────────┴───────────────────────┐
│   Infrastructure Layer                    │
│   Docker/MongoDB/Redis/PostgreSQL        │
└──────────────────────────────────────────┘
```

---

## 3. Implementation Steps

### Step 1: Verify Phase 4 Components

Ensure Phase 4 components are working:

```bash
cd /home/kali/mirror-leech-telegram-bot

# Check Phase 4 components exist
ls -la bot/core/query_optimizer.py
ls -la bot/core/cache_manager.py
ls -la bot/helper/ext_utils/db_repositories/

# Run Phase 4 tests
pytest tests/test_phase4_integration.py -v
```

### Step 2: Import Phase 5 Configuration

**In `config/main_config.py`:**
```python
# Import Phase 5 config enhancements
from config_enhancements_phase5 import (
    get_phase5_config,
    validate_phase5_config,
    PHASE5_PRESETS
)

# Merge Phase 5 config with main config
def load_user_config():
    """Load complete configuration including Phase 5"""
    base_config = {
        # ... existing config ...
    }
    
    # Add Phase 5 options (disabled by default)
    phase5_config = get_phase5_config()
    base_config.update(phase5_config)
    
    return base_config
```

### Step 3: Initialize Phase 5 During Startup

**In `bot/__main__.py`:**
```python
import asyncio
from bot.core.enhanced_startup import (
    initialize_phase5,
    get_phase5_status,
    shutdown_phase5
)
from config.main_config import load_user_config

async def start_bot():
    """Start bot with optional HA"""
    try:
        # Load config including Phase 5
        config = load_user_config()
        
        # Initialize Phase 5 (if enabled)
        if config.get('CLUSTER_ENABLED') or config.get('FAILOVER_ENABLED'):
            print("Initializing High Availability...")
            success = await initialize_phase5(config)
            
            if not success:
                print("Warning: HA initialization failed, continuing without HA")
            else:
                print("✅ High Availability initialized successfully")
        
        # Start bot
        print("Starting Telegram bot...")
        await bot.start()
        print("✅ Bot started successfully!")
        
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

**In `web/wserver.py`:**
```python
from bot.core.enhanced_startup import get_phase5_status

@app.get("/health")
async def health_endpoint():
    """Health check endpoint with Phase 5 status"""
    
    # Get Phase 5 status if enabled
    ha_status = await get_phase5_status()
    
    if ha_status.get('enabled'):
        health = ha_status.get('health_status', {})
        return {
            'status': health.get('status', 'healthy'),
            'ha_enabled': True,
            'ha_details': ha_status
        }
    
    return {
        'status': 'healthy',
        'ha_enabled': False
    }
```

### Step 5: Add Status Command to Bot

**In `bot/modules/handler.py` or similar:**
```python
async def ha_status_command(client, message):
    """Show High Availability status"""
    from bot.core.enhanced_startup import get_phase5_status
    
    status = await get_phase5_status()
    
    if not status.get('enabled'):
        await message.reply("High Availability is not enabled")
        return
    
    # Format status message
    text = "🔄 <b>High Availability Status</b>\n\n"
    
    if 'cluster_info' in status:
        cluster = status['cluster_info']
        text += f"<b>Cluster:</b>\n"
        text += f"├ State: {cluster['state']}\n"
        text += f"├ Nodes: {cluster['total_nodes']}\n"
        text += f"└ Leader: {cluster['leader_node']}\n\n"
    
    if 'failover_status' in status:
        failover = status['failover_status']
        text += f"<b>Failover:</b>\n"
        text += f"└ Primary: {failover['primary_node']}\n\n"
    
    if 'health_status' in status:
        health = status['health_status']
        text += f"<b>Health:</b>\n"
        text += f"└ Status: {health['status']}\n"
    
    await message.reply(text)
```

---

## 4. Configuration Guide

All configuration is handled via `config_enhancements_phase5.py`:

### Basic Configuration

**Minimal (Single Node):**
```python
from config_enhancements_phase5 import PHASE5_PRESETS
config = PHASE5_PRESETS['development']
```

**Development (2 Nodes):**
```python
config = PHASE5_PRESETS['simple_failover']
```

**Production (3+ Nodes):**
```python
config = PHASE5_PRESETS['full_ha']
```

**Distributed (5+ Nodes):**
```python
config = PHASE5_PRESETS['distributed']
```

### Validation

```python
from config_enhancements_phase5 import validate_phase5_config

result = validate_phase5_config(config)
if not result['valid']:
    print(f"Configuration errors: {result['errors']}")
else:
    print(f"Warnings: {result['warnings']}")
```

---

## 5. Deployment Scenarios

### Scenario 1: Docker Compose (3 Nodes)

**Update `docker-compose.yml`:**
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
    depends_on:
      - redis
      - mongodb

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
    networks:
      - botnet
    depends_on:
      - redis
      - mongodb

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
    networks:
      - botnet
    depends_on:
      - redis
      - mongodb

  # Shared infrastructure
  redis:
    image: redis:7-alpine
    networks:
      - botnet

  mongodb:
    image: mongo:latest
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

### Scenario 2: Cloud VMs (AWS/GCP/Azure)

**Node 1 (10.0.1.10):**
```bash
export CLUSTER_ENABLED=True
export CLUSTER_NODE_ID=node-1
export CLUSTER_ADDRESS=10.0.1.10
export CLUSTER_SEED_NODES=10.0.1.11:7946,10.0.1.12:7946
export FAILOVER_ENABLED=True
export FAILOVER_PRIMARY_NODE=node-1
python -m bot
```

**Node 2 (10.0.1.11):**
```bash
export CLUSTER_ENABLED=True
export CLUSTER_NODE_ID=node-2
export CLUSTER_ADDRESS=10.0.1.11
export CLUSTER_SEED_NODES=10.0.1.10:7946,10.0.1.12:7946
export FAILOVER_ENABLED=True
export FAILOVER_SECONDARY_NODES=node-1
python -m bot
```

### Scenario 3: Kubernetes StatefulSet

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mltb-cluster
spec:
  serviceName: mltb-cluster
  replicas: 3
  selector:
    matchLabels:
      app: mltb
  template:
    metadata:
      labels:
        app: mltb
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
        - name: CLUSTER_ADDRESS
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        - name: CLUSTER_SEED_NODES
          value: "mltb-cluster-0.mltb-cluster.default.svc.cluster.local:7946,mltb-cluster-1.mltb-cluster.default.svc.cluster.local:7946"
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
  name: mltb-cluster
spec:
  clusterIP: None
  selector:
    app: mltb
  ports:
  - port: 7946
    name: cluster
  - port: 8080
    name: http
```

---

## 6. Testing

### Test 1: Configuration Validation

```python
from config_enhancements_phase5 import validate_phase5_config, PHASE5_PRESETS

# Test each preset
for preset_name, config in PHASE5_PRESETS.items():
    result = validate_phase5_config(config)
    print(f"{preset_name}: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
```

### Test 2: Cluster Formation

```bash
# Start Node 1
python -m bot

# In another terminal, start Node 2
export CLUSTER_NODE_ID=node-2
python -m bot

# Verify cluster
curl http://localhost:8080/health
```

### Test 3: Failover

```bash
# Simulate primary node failure
docker stop bot-node-1

# Wait 15-30 seconds

# Verify failover occurred
curl http://localhost:8081/health
```

### Test 4: Data Replication

```python
from bot.core.replication_manager import ReplicationManager

replication = ReplicationManager.get_instance()

# Replicate test data
await replication.replicate_data(
    data_id='test-123',
    data_type='task',
    data={'test': 'data', 'timestamp': time.time()}
)

# Verify replication
status = await replication.get_replication_status()
assert status['replicated_items'] > 0
```

---

## 7. Troubleshooting

### Issue 1: Nodes Not Joining Cluster

**Symptoms:**
- Nodes stuck in JOINING state
- Cannot connect to seed nodes

**Solutions:**
```bash
# Verify network connectivity
ping <seed_node_ip>
telnet <seed_node_ip> 7946

# Check firewall (if using UFW)
sudo ufw allow 7946/tcp

# Verify environment variables
env | grep CLUSTER
```

### Issue 2: Split-Brain Scenario

**Symptoms:**
- Multiple leaders detected
- Cluster state: SPLIT_BRAIN

**Solutions:**
```bash
# Check quorum configuration
echo $HA_QUORUM_SIZE

# Restart with correct seed nodes
# Ensure all nodes can communicate
```

### Issue 3: High Replication Lag

**Symptoms:**
- `lag_seconds` > 60
- Data inconsistency across nodes

**Solutions:**
```python
# Use eventual consistency if strict is not needed
config = {
    'REPLICATION_CONSISTENCY': 'eventual',
    'REPLICATION_BATCH_SIZE': 200,
}

# Monitor lag continuously
status = await replication.get_replication_status()
for node_id, info in status['nodes'].items():
    print(f"{node_id} lag: {info['lag_seconds']}s")
```

---

## Performance Optimization

### Network Tuning

```python
config = {
    'CLUSTER_HEARTBEAT_INTERVAL': 2,      # Faster detection
    'CLUSTER_NODE_TIMEOUT': 6,            # Lower timeout
    'HA_NETWORK_TIMEOUT': 5,              # Faster network timeout
}
```

### Replication Tuning

```python
config = {
    'REPLICATION_BATCH_SIZE': 250,        # Larger batches
    'REPLICATION_CONSISTENCY': 'eventual', # For performance
    'REPLICATION_ASYNC_WRITES': True,     # Non-blocking
}
```

---

## Integration with Existing Phases

Phase 5 integrates seamlessly with:
- **Phase 4 (TIER 2):** QueryOptimizer, CacheManager, ConnectionPoolManager, RateLimiter
- **Database Repositories:** Full replication support for all repository data types
- **Existing Configuration:** Uses config/main_config.py pattern

See [DOCKER_COMPOSE_HA_SETUP.md](DOCKER_COMPOSE_HA_SETUP.md) for complete Docker setup examples.

---

## Next Steps

1. ✅ Review this guide
2. ⏭️ Start with development preset (`PHASE5_PRESETS['development']`)
3. ⏭️ Test 2-node failover scenario
4. ⏭️ Validate in staging environment
5. ⏭️ Deploy to production with 3+ nodes

For questions, see [PHASE_5_FEATURES.md](PHASE_5_FEATURES.md) or related TIER3 documentation.
