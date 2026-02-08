# Operational Runbook - Mirror Leech Telegram Bot
**Production Operations Guide**

---

## Table of Contents
1. [Deployment Procedures](#deployment-procedures)
2. [Monitoring & Alerts](#monitoring--alerts)
3. [Troubleshooting Guides](#troubleshooting-guides)
4. [Performance Tuning](#performance-tuning)
5. [Emergency Procedures](#emergency-procedures)
6. [Backup & Recovery](#backup--recovery)
7. [Scaling Procedures](#scaling-procedures)

---

## Deployment Procedures

### Prerequisites
- Docker & Docker Compose ≥ 20.10
- 4GB+ RAM, 20GB+ disk space
- Python 3.10+ (if running without Docker)
- MongoDB 5.0+ (or Atlas)
- Redis 6.0+ (or ElastiCache)

### Standard Deployment

#### 1. Pre-Deployment Checklist
```bash
# Verify system requirements
cd /home/kali/mirror-leech-telegram-bot
bash scripts/pre_deployment_checklist.sh

# Expected output:
# ✅ All checks passed
# ✅ Resources available
# ✅ Dependencies installed
```

#### 2. Environment Setup
```bash
# Create environment file
cp config/.env.example .env

# Edit with your configuration
nano .env

# Required variables:
# - TELEGRAM_BOT_TOKEN=<your-token>
# - TELEGRAM_CHAT_ID=<channel-id>
# - MONGO_URL=<mongodb-connection>
# - REDIS_URL=redis://redis:6379
```

#### 3. Security Hardening
```bash
# Run security setup (IMPORTANT: Do this first!)
bash scripts/security_hardening.sh

# This enables:
# ✅ Docker network isolation
# ✅ Volume encryption
# ✅ Secret management
# ✅ Resource limits
# ✅ Health checks
```

#### 4. Deploy Services
```bash
# Start all services
docker-compose -f docker-compose.secure.yml up -d

# Verify startup (wait 30-60 seconds)
bash scripts/health_check.sh

# Expected output:
# 🟢 All services healthy
# 🟢 Core services: 5/5
# 🟢 Support services: 2/2
```

#### 5. Post-Deployment Verification
```bash
# Verify Phase 4 components
docker-compose exec app python3 -c "
from bot.core.cache_manager import CacheManager
from bot.core.query_optimizer import QueryOptimizer

cache = CacheManager.get_instance()
optimizer = QueryOptimizer.get_instance()
print('✅ Phase 4 components loaded')
"

# Run quick tests
python3 -m pytest tests/test_phase4_integration.py -q
```

---

## Monitoring & Alerts

### 1. Dashboard Access
- **Grafana:** http://localhost:3000 (admin/admin by default)
- **Prometheus:** http://localhost:9090
- **Health Check:** http://localhost:8060/health

### 2. Key Metrics to Monitor

#### Phase 4 Performance
```
Cache Hit Rate:              Target >70%
Connection Pool Usage:       Target <80%
Query Response Time:         Target <100ms
Rate Limiter Block Rate:     Target <5%
```

#### System Health
```
Memory Usage:                Alert if >85%
CPU Usage:                   Alert if >80%
Disk Usage:                  Alert if >85%
Container Restarts:          Alert if >0 in 1 hour
```

### 3. Health Check Commands
```bash
# Quick health check (1-2 minutes)
bash scripts/quick_health_check.sh

# Comprehensive health check (5-10 minutes)
bash scripts/health_check_comprehensive.sh

# Specific service check
curl http://localhost:8060/health | jq .
curl http://localhost:9090/-/healthy
```

### 4. Alert Response Procedures

#### 🔴 Critical: API Down
**Metric:** `up{job="mltb-app"} == 0`  
**Steps:**
```bash
# 1. Check container status
docker-compose ps

# 2. Check logs
docker-compose logs -f app --tail=50

# 3. Verify health endpoint
curl -v http://localhost:8060/health

# 4. Restart service
docker-compose restart app

# 5. Verify recovery
sleep 10 && bash scripts/quick_health_check.sh
```

#### 🟠 Warning: High Memory Usage
**Metric:** `container_memory_usage_bytes > 85%`  
**Steps:**
```bash
# 1. Check memory breakdown
docker stats --no-stream

# 2. Identify problematic process
ps aux | sort -rk 3,3 | head -5

# 3. Options:
#    - Increase container memory limit in docker-compose.yml
#    - Reduce cache size: CacheManager.max_size_mb = 150
#    - Clear old logs: rm -rf data/logs/*

# 4. Redeploy if needed
docker-compose restart app
```

#### 🟠 Warning: High CPU Usage
**Metric:** `CPU > 80%`  
**Steps:**
```bash
# 1. Check what's running
top -n 1 | head -20

# 2. Check if download spike
curl http://localhost:8060/api/tasks | jq '.total_tasks'

# 3. Options:
#    - This is normal during heavy downloads (expected)
#    - Add worker nodes for distributed load
#    - Implement request throttling

# 4. Monitor for >30 minutes sustained
```

#### 🟠 Warning: Cache Hit Rate < 60%
**Metric:** `mltb_cache_hit_rate < 0.60`  
**Steps:**
```bash
# 1. Check cache statistics
curl http://localhost:9090/api/v1/query?query=mltb_cache_statistics

# 2. Check for cache churn
curl http://localhost:9090/api/v1/query?query=rate(mltb_cache_evictions_total[5m])

# 3. Options:
#    - Increase cache size
#    - Review cache TTL settings
#    - Check for cache key misses
```

---

## Troubleshooting Guides

### Issue: Download Stuck in "Processing"
**Symptoms:**
- Task status shows "processing" for >30 minutes
- No progress in logs

**Diagnosis:**
```bash
# 1. Check logs
docker-compose logs --tail=100 app | grep -i "stuck\|timeout\|error"

# 2. Check download client status
curl http://localhost:6800/jsonrpc  # aria2
curl http://localhost:8080/api/v2/app/webapiVersion  # qBittorrent

# 3. Check database
docker-compose exec mongo mongosh --eval "
db.downloads.find({status: 'processing', updated_at: {$lt: new Date(Date.now() - 1800000)}})
"
```

**Resolution:**
```bash
# Option 1: Reset stuck download
curl http://localhost:8060/api/reset-task/<task-id>

# Option 2: Force cleanup
docker-compose exec app python3 -c "
from bot.core.recovery_manager import RecoveryManager
recovery = RecoveryManager.get_instance()
recovery.cleanup_stuck_tasks(timeout_minutes=30)
"

# Option 3: Restart download client
docker-compose restart aria2 qbittorrent

# Option 4: Full reset (last resort)
bash scripts/backup.sh  # Backup first!
docker-compose exec mongo mongosh --eval "
db.downloads.deleteMany({status: 'processing'})
"
```

### Issue: Memory Leak
**Symptoms:**
- Memory usage increases linearly
- CPU stays high
- Response times degrade over hours

**Diagnosis:**
```bash
# 1. Check memory growth
docker stats --no-stream | grep app
sleep 60
docker stats --no-stream | grep app
# Compare values - if growing, we have a leak

# 2. Check Phase 4 caches
curl http://localhost:9090/api/v1/query?query=mltb_cache_size_bytes

# 3. Check connection count
netstat -an | grep ESTABLISHED | wc -l
```

**Resolution:**
```bash
# Option 1: Clear caches safely
docker-compose exec app python3 -c "
from bot.core.cache_manager import CacheManager
cache = CacheManager.get_instance()
cache.clear()
"

# Option 2: Restart app (rolling restart, no downtime)
docker-compose up -d --force-recreate app

# Option 3: Debug leak with profiler
docker-compose exec app python3 -c "
from bot.core.profiler import Profiler
profiler = Profiler.get_instance()
profiler.enable_memory_profiling()
# Monitor for 5 minutes, then:
profiler.get_memory_growth_report()
"

# Option 4: Increase memory limit (temporary)
# Edit docker-compose.yml: mem_limit: 2g
```

### Issue: Database Connection Errors
**Symptoms:**
```
pymongo.errors.ServerSelectionTimeoutError
redis.exceptions.ConnectionError
```

**Diagnosis:**
```bash
# 1. Check DB connectivity
docker-compose exec app python3 -c "
import pymongo
client = pymongo.MongoClient('mongodb://mongo:27017')
print('MongoDB:', client.server_info())
"

# 2. Check Redis connectivity
docker-compose exec app redis-cli -h redis ping
# Expected: PONG

# 3. Check network
docker network inspect mirror-leech-telegram-bot_default
```

**Resolution:**
```bash
# Option 1: Restart databases
docker-compose restart mongo redis

# Option 2: Rebuild network
docker-compose down
docker-compose up -d

# Option 3: Check volume mounts
docker volume ls | grep mongo
docker volume inspect mirror-leech-telegram-bot_mongo_data

# Option 4: Reset (WARNING: DATA LOSS)
docker-compose down -v  # Remove volumes
docker-compose up -d
bash scripts/mongodb-init.js  # Reinitialize
```

### Issue: Slow API Responses
**Symptoms:**
- API requests take >1000ms
- Timeouts occur
- Cascade failures from timeouts

**Diagnosis:**
```bash
# 1. Check Query Optimizer
curl http://localhost:8060/api/performance/queries | jq '.slow_queries'

# 2. Check connection pool
curl http://localhost:8060/api/performance/pools | jq '.wait_time_ms'

# 3. Check cache efficiency
curl http://localhost:8060/api/performance/cache | jq '.hit_rate'

# 4. Profile request
curl -H "X-Profile: true" http://localhost:8060/api/tasks
```

**Resolution:**
```bash
# Option 1: Analyze with codescene
bash scripts/codescene_analyze.sh

# Option 2: Add missing indexes
docker-compose exec mongo mongosh < scripts/mongodb-init.js

# Option 3: Increase connection pool size
# Edit bot/core/connection_pool_manager.py
# Change: max_size=20 -> max_size=50

# Option 4: Enable query caching
docker-compose exec app python3 -c "
from bot.core.query_optimizer import QueryOptimizer
optimizer = QueryOptimizer.get_instance()
optimizer.enable()
"
```

---

## Performance Tuning

### 1. Cache Tuning
```python
# In bot/core/cache_manager.py

# For Read-Heavy workloads (>80% reads)
max_size_mb = 500          # Larger cache
l1_ttl_seconds = 300       # 5 minutes
eviction_policy = 'lru'

# For Write-Heavy workloads (>50% writes)
max_size_mb = 100          # Smaller cache
l1_ttl_seconds = 60        # 1 minute
eviction_policy = 'lfu'    # Least Frequently Used
```

### 2. Connection Pool Tuning
```python
# In bot/core/connection_pool_manager.py

# For High Concurrency (>500 concurrent connections)
max_size = 100
min_idle = 20
max_wait_ms = 5000

# For Low Concurrency (<100 concurrent connections)
max_size = 20
min_idle = 5
max_wait_ms = 1000
```

### 3. Rate Limiter Tuning
```python
# In bot/core/rate_limiter.py

# For API endpoints (standard)
tokens_per_second = 100
burst_size = 500

# For expensive operations (mirror, ytdlp)
tokens_per_second = 10
burst_size = 50
```

### 4. Database Tuning
```javascript
// In MongoDB
db.settings.updateOne(
    {},
    {$set: {
        "wiredTiger.engineConfig.cacheSizeGB": 2,
        "compression": "snappy",
        "maxConns": 100
    }}
)
```

---

## Emergency Procedures

### 🚨 Complete System Failure
**Objective:** Restore service with minimum data loss

**Steps:**
```bash
# 1. Backup current state (if possible)
bash scripts/backup.sh

# 2. Stop all services
docker-compose down

# 3. Check disk space
df -h

# 4. Clean up old containers/images
docker system prune -a --volumes

# 5. Restart fresh
docker-compose -f docker-compose.secure.yml up -d

# 6. Restore from backup if needed
bash scripts/backup_restore.sh /path/to/backup.tar.gz

# 7. Verify recovery
bash scripts/health_check_comprehensive.sh
```

### 🚨 Security Breach
**Objective:** Isolate, contain, investigate, recover

**Steps:**
```bash
# 1. Isolate system (stop bot, keep monitoring)
docker-compose pause app

# 2. Capture logs for investigation
docker-compose logs > logs/security_incident_$(date +%s).log

# 3. Rotate credentials
# - Telegram bot token
# - Database passwords
# - API keys

# 4. Inspect compromised services
docker-compose exec mongo mongosh
db.users.find() # Check for unauthorized users

# 5. Rebuild from clean images
docker-compose down
docker image rm -f mirror-leech-telegram-bot_app
docker-compose -f docker-compose.secure.yml up -d

# 6. Restore from backup AFTER cleaning
bash scripts/backup_restore.sh /path/to/clean/backup.tar.gz
```

### 🚨 Data Loss
**Objective:** Recover from latest backup

**Steps:**
```bash
# 1. Stop services to prevent further corruption
docker-compose stop

# 2. List available backups
ls -lah data/backups/

# 3. Restore from most recent backup
bash scripts/backup_restore.sh data/backups/backup_latest.tar.gz

# 4. Verify restored data
docker-compose exec mongo mongosh --eval "
db.downloads.countDocuments()
db.tasks.countDocuments()
"

# 5. Resume services
docker-compose start

# 6. Verify service health
bash scripts/quick_health_check.sh
```

---

## Backup & Recovery

### Automated Daily Backup
```bash
# Add to crontab (runs daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /home/kali/mirror-leech-telegram-bot/scripts/backup.sh

# Verify:
crontab -l | grep backup
```

### Manual Backup
```bash
# Full backup
bash scripts/backup.sh

# Output: data/backups/backup_20260206_120000.tar.gz
# Size: Check with: du -h data/backups/backup_*.tar.gz

# Backup verification
tar -tzf data/backups/backup_20260206_120000.tar.gz | head -20
```

### Recovery Procedures
```bash
# List backups
ls -lah data/backups/

# Dry-run restore (don't actually restore)
bash scripts/backup_restore.sh data/backups/backup_latest.tar.gz --dry-run

# Full restore
bash scripts/backup_restore.sh data/backups/backup_latest.tar.gz

# Restore specific database
tar -xzf backup_latest.tar.gz -C data/backups/ mongodump/
mongorestore data/backups/mongodump/
```

### Backup Strategy
**Frequency:** Daily at 2 AM
**Retention:** 7 days
**Location:** `data/backups/`
**Verification:** Monthly restore test to staging

---

## Scaling Procedures

### Horizontal Scaling (Multiple Workers)

#### 1. Add Download Worker Node
```bash
# 1. Prepare second machine
ssh user@machine2
cd /home/kali/mirror-leech-telegram-bot

# 2. Deploy worker (no web interface needed)
docker-compose -f docker-compose.worker.yml up -d

# 3. Register with main coordinator
docker-compose exec worker python3 -c "
from bot.core.task_scheduler import TaskScheduler
scheduler = TaskScheduler.get_instance()
scheduler.register_worker('worker-2', 'http://machine2:9090')
"

# 4. Verify worker registration
docker-compose exec app python3 -c "
from bot.core.task_scheduler import TaskScheduler
scheduler = TaskScheduler.get_instance()
print(scheduler.list_workers())
"

# 5. Monitor worker
docker-compose logs -f worker
```

#### 2. Add Database Replica
```bash
# 1. Prepare MongoDB replica set
docker-compose exec mongo mongosh --eval "
rs.initiate({
    _id: 'rs0',
    members: [
        {_id: 0, host: 'mongo:27017'},
        {_id: 1, host: 'mongo-2:27017'}
    ]
})
"

# 2. Add mongo-2 service to docker-compose.yml
# See docker-compose.secure.yml for example

# 3. Redeploy
docker-compose up -d mongo-2

# 4. Verify replication
docker-compose exec mongo mongosh --eval "rs.status()"
```

### Vertical Scaling (Bigger Hardware)

#### 1. Increase Container Resources
```yaml
# docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'          # Was 1
          memory: 2G         # Was 1G
        reservations:
          cpus: '1'
          memory: 1G
```

#### 2. Redeploy with New Resources
```bash
docker-compose up -d
docker stats --no-stream  # Verify new limits
```

#### 3. Adjust Tuning for New Capacity
```python
# Increase cache size with more memory
max_size_mb = 1000  # From 200

# Increase pool size with more CPU
pool_max_size = 100  # From 20
```

---

## Runbook Checklist

- [ ] **Daily Operations**
  - [ ] Check health dashboards (Grafana)
  - [ ] Review overnight logs
  - [ ] Verify backup completion
  - [ ] Monitor resource usage

- [ ] **Weekly Operations**
  - [ ] Full health check: `bash scripts/health_check_comprehensive.sh`
  - [ ] Review metrics trends
  - [ ] Test backup restore (staging)
  - [ ] Update documentation

- [ ] **Monthly Operations**
  - [ ] Performance analysis: `bash scripts/codescene_analyze.sh`
  - [ ] Security audit
  - [ ] Capacity planning review
  - [ ] Disaster recovery drill

- [ ] **Quarterly Operations**
  - [ ] Major version updates
  - [ ] Architecture review
  - [ ] Security hardening refresh
  - [ ] Performance optimization drive

---

## Contact & Escalation

| Issue | Response | Contact |
|-------|----------|---------|
| API Down | 15 min | On-call Engineer |
| Database Down | 20 min | Database Admin |
| Performance Degradation | 30 min | Performance Team |
| Security Alert | 5 min | Security Team |

---

**Last Updated:** February 6, 2026  
**Tier 2.3 - Operational Runbook**
