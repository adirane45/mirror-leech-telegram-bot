# Configuration Tuning Guide

Based on your bot's current performance and usage patterns, here are recommended configuration optimizations.

## 📋 Current Configuration Status

### ✅ Already Configured:
- Bot Token
- Owner ID
- Database (MongoDB)
- Redis Cache
- Category B Features
- Download Directory

### ⚠️ Recommended Tuning:

---

## 1. Performance Optimization

### Parallel Downloads (Category B)
**File:** `src/bot/core/parallel_download.py`

Current: 3-5 chunks per file

**Tune based on connection:**
```python
# Fast connection (100+ Mbps)
MAX_CHUNKS = 8
CHUNK_SIZE = 10 * 1024 * 1024  # 10MB

# Medium connection (10-100 Mbps)
MAX_CHUNKS = 5  # Current
CHUNK_SIZE = 5 * 1024 * 1024   # 5MB

# Slow/unstable connection
MAX_CHUNKS = 2
CHUNK_SIZE = 2 * 1024 * 1024   # 2MB
```

---

## 2. Circuit Breaker Thresholds

**File:** `src/bot/core/category_b_integration.py` (Lines 52-67)

Current settings:
```python
telegram_breaker:
  - failure_threshold: 5
  - timeout: 60s

gdrive_breaker:
  - failure_threshold: 3
  - timeout: 120s

aria2_breaker:
  - failure_threshold: 5
  - timeout: 30s
```

**Adjust if:**
- **Too sensitive** (opens frequently): Increase `failure_threshold`
- **Not responsive enough**: Decrease `failure_threshold`
- **Recovery too slow**: Decrease `timeout`
- **Recovery too fast**: Increase `timeout`

---

## 3. Queue Priority Weights

**File:** `src/bot/core/priority_queue.py`

Customize based on user importance:
```python
QUEUE_PRIORITIES = {
    'emergency': 1000,  # Highest
    'vip': 100,
    'default': 10,
    'batch': 1          # Lowest
}
```

---

## 4. Retry Engine Settings

**File:** `src/bot/core/smart_retry.py`

Current: Exponential backoff 5s → 3600s

**Tune for your needs:**
```python
# Faster retries (testing/development)
INITIAL_DELAY = 2        # Start at 2s
MAX_DELAY = 300          # Max 5 minutes
MULTIPLIER = 1.5         # Slower growth

# More patient retries (production)
INITIAL_DELAY = 10       # Start at 10s
MAX_DELAY = 7200         # Max 2 hours
MULTIPLIER = 2           # Current setting

# Aggressive retries (unstable network)
INITIAL_DELAY = 1
MAX_DELAY = 60
MULTIPLIER = 1.2
```

---

## 5. Storage & Cleanup

### Download Limits
**File:** `config/main_config.py`

```python
# Maximum file size
MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10GB

# Auto-cleanup after upload
AUTO_DELETE_SUCCESS = True
DELETE_DELAY = 300  # 5 minutes after upload

# Storage threshold (pause downloads)
STORAGE_THRESHOLD = 85  # Stop at 85% disk usage
```

### Auto-Cleanup (Already Configured)
```bash
# Files older than 1 day - Hourly check (Active)
# Files older than 7 days - Daily check (Active in cron)
```

---

## 6. Resource Limits

### Container Resources
**File:** `docker-compose.yml`

```yaml
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '2.0'      # Max 2 CPU cores
          memory: 2G       # Max 2GB RAM
        reservations:
          cpus: '0.5'      # Min 0.5 cores
          memory: 512M     # Min 512MB
```

### Python Worker Threads
```python
# For CPU-intensive tasks
MAX_WORKERS = 4  # Adjust based on CPU cores

# For I/O-intensive tasks
MAX_CONCURRENT_DOWNLOADS = 5
```

---

## 7. Security Settings

### Rate Limiting
```python
# Per user limits
USER_RATE_LIMIT = 10  # downloads per hour
GLOBAL_RATE_LIMIT = 50  # total per hour

# Cooldown between commands
COMMAND_COOLDOWN = 2  # seconds
```

### Access Control
```python
# Restrict to specific users/chats
AUTHORIZED_CHATS = [123456789, 987654321]
OWNER_ID = 123456789

# Or allow all
USERS_ONLY_MODE = False
```

---

## 8. Monitoring & Logging

### Log Levels
```python
# Development
LOG_LEVEL = 'DEBUG'

# Production (current)
LOG_LEVEL = 'INFO'

# Minimal
LOG_LEVEL = 'WARNING'
```

### Metrics Collection
```python
# Enable detailed metrics
ENABLE_METRICS = True
METRICS_PORT = 9090  # Prometheus

# Disable for minimal overhead
ENABLE_METRICS = False
```

---

## 9. Database Optimization

### MongoDB Indexes
```bash
# Create indexes for faster queries
docker exec 9ea93d6c31a9 python3 << 'PYEOF'
from pymongo import MongoClient, ASCENDING, DESCENDING
db = MongoClient()['bot_db']

# Download history
db.downloads.create_index([('user_id', ASCENDING), ('timestamp', DESCENDING)])

# User stats
db.users.create_index([('user_id', ASCENDING)])
db.users.create_index([('last_active', DESCENDING)])
PYEOF
```

### Redis Cache TTL
```python
# Cache duration seconds
CACHE_TTL = 3600  # 1 hour
USER_CACHE_TTL = 86400  # 24 hours
```

---

## 10. Network Optimization

### Connection Pool
```python
# HTTP connections
MAX_CONNECTIONS = 100
MAX_KEEPALIVE_CONNECTIONS = 20
KEEPALIVE_EXPIRY = 30  # seconds

# Timeouts
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 300  # 5 minutes for large files
```

---

## Quick Reference Commands

```bash
# View current config
docker exec 9ea93d6c31a9 python3 -c "import sys; sys.path.insert(0, '/app/src'); from config.main_config import Config; print(dir(Config))"

# Test configuration changes
docker restart 9ea93d6c31a9

# Monitor after changes
./scripts/monitor_bot.sh watch

# Check for errors
./scripts/view_logs.sh 100 error
```

---

## Recommended Next Actions

1. **Measure current performance baseline**
   ```bash
   ./scripts/monitor_bot.sh > baseline_$(date +%Y%m%d).txt
   ```

2. **Make one change at a time**
   - Easier to identify what helps/hurts
   - Document each change

3. **Test after each change**
   - Run test downloads
   - Monitor for 24 hours
   - Check error rates

4. **Keep backups**
   ```bash
   ./scripts/backup_current_state.sh
   ```

---

**Current Status:** Bot is working well with default settings. Only tune if you experience specific issues or have special requirements.
