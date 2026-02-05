# Phase 2 Implementation Guide
## Enhanced Logging, Monitoring & Recovery System

**Safe Innovation Path - Phase 2**  
**Date:** February 5, 2026  
**Status:** Ready for Implementation

---

## 📦 What's Included in Phase 2

### Core Infrastructure (5 Managers)

| Component | File | Purpose | Status |
|-----------|------|---------|--------|
| **Logger Manager** | `bot/core/logger_manager.py` | Structured JSON logging | ✅ Ready |
| **Alert Manager** | `bot/core/alert_manager.py` | Error detection & alerts | ✅ Ready |
| **Backup Manager** | `bot/core/backup_manager.py` | Automated backups | ✅ Ready |
| **Profiler** | `bot/core/profiler.py` | Performance monitoring | ✅ Ready |
| **Recovery Manager** | `bot/core/recovery_manager.py` | Data integrity & recovery | ✅ Ready |

### Configuration & Testing

- **Configuration:** `config_enhancements_phase2.py` (900+ lines)
- **Tests:** `tests/test_phase2_integration.py` (400+ lines)
- **Requirements:** `requirements-phase2.txt`
- **Documentation:** `PHASE_2_FEATURES.md` & `PHASE_2_IMPLEMENTATION_GUIDE.md`

### Total Additions

- **Core Code:** 1,900+ lines
- **Tests:** 400+ lines
- **Configuration:** 900+ lines
- **Documentation:** 1,500+ lines
- **Total:** 4,700+ lines of new code

---

## 🚀 Quick Implementation

### Step 1: Install Dependencies

```bash
# Install Phase 2 requirements
pip install -r requirements-phase2.txt

# Optional: ELK stack support
pip install -r requirements-phase2.txt[elk]
```

### Step 2: Enable Features in Config

Edit your `config.py` or create `.env`:

```python
# Minimal setup (just logging)
ENABLE_ENHANCED_LOGGING = True
ENABLE_ALERT_SYSTEM = True

# Full setup (all features)
ENABLE_ENHANCED_LOGGING = True
ENABLE_ALERT_SYSTEM = True
ENABLE_BACKUP_SYSTEM = True
ENABLE_PROFILER = True
ENABLE_RECOVERY_MANAGER = True
```

### Step 3: Initialize in Startup

Add to `bot/__main__.py` or startup script:

```python
from bot.core.enhanced_startup import initialize_enhanced_services
from bot.core.enhanced_startup_phase2 import initialize_phase2_services

# Initialize Phase 1
phase1_status = await initialize_enhanced_services()

# Initialize Phase 2
phase2_status = await initialize_phase2_services()

print("Phase 1 Status:", phase1_status)
print("Phase 2 Status:", phase2_status)
```

### Step 4: Run Tests

```bash
# Run Phase 2 tests
python run_tests.py tests/test_phase2_integration.py

# Or with pytest directly
pytest tests/test_phase2_integration.py -v
```

---

## 📋 Feature Activation Checklist

### Logging

- [ ] Install requirements
- [ ] Set `ENABLE_ENHANCED_LOGGING = True`
- [ ] Configure `LOG_DIR` and `LOG_LEVEL`
- [ ] Test with `logger_manager.log_download(...)`
- [ ] Verify logs appear in `logs/` directory

### Alerts

- [ ] Set `ENABLE_ALERT_SYSTEM = True`
- [ ] Configure alert thresholds
- [ ] Set up notification channels
- [ ] Register alert handlers
- [ ] Test with `alert_manager.trigger_alert(...)`

### Backups

- [ ] Set `ENABLE_BACKUP_SYSTEM = True`
- [ ] Define `CRITICAL_BACKUP_PATHS`
- [ ] Configure `BACKUP_DIR` and retention
- [ ] Test backup creation: `await backup_manager.create_backup(...)`
- [ ] Test restoration: `await backup_manager.restore_backup(...)`
- [ ] Schedule automated backups with Celery

### Profiling

- [ ] Set `ENABLE_PROFILER = True`
- [ ] Configure `PROFILE_THRESHOLD`
- [ ] Add profiling to critical operations
- [ ] Test with `profiler.profile_sync()` / `profile_async()`
- [ ] Review slow operations: `profiler.get_slow_operations()`

### Recovery

- [ ] Set `ENABLE_RECOVERY_MANAGER = True`
- [ ] Define `RECOVERY_CRITICAL_PATHS`
- [ ] Test integrity check: `await recovery_manager.verify_integrity(...)`
- [ ] Test auto-recovery: `await recovery_manager.auto_recover(...)`
- [ ] Review recovery status: `recovery_manager.get_recovery_status()`

---

## 🔌 Integration with Phase 1

### Redis + Logger Manager

```python
from bot.core.redis_manager import redis_client
from bot.core.logger_manager import logger_manager

# Cache log metadata in Redis
async def cache_log_stats():
    stats = logger_manager.get_log_stats()
    await redis_client.set("log_stats", stats, ttl=300)
```

### Celery + Backup Manager

```python
from bot.core.celery_app import app
from bot.core.backup_manager import backup_manager

@app.task
def scheduled_backup():
    """Celery task for scheduled backups"""
    result = await backup_manager.create_backup(
        source_paths=["config.py", "bot/"],
        backup_name=f"scheduled_{datetime.now().isoformat()}"
    )
    return result
```

### Prometheus + Profiler

```python
from bot.core.profiler import profiler
from bot.core.metrics import metrics

async def log_performance_metrics():
    """Export profiler stats to Prometheus"""
    stats = profiler.get_stats()
    slow_ops = profiler.get_slow_operations()
    
    for op in slow_ops:
        metrics.record_performance_event(
            "slow_operation",
            op["average_duration"],
            operation=op["operation"]
        )
```

---

## 🌐 Docker & Kubernetes Support

### Docker Compose Update (docker-compose.yml)

```yaml
services:
  # Existing services...
  
  # Phase 2 services
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager:/etc/alertmanager

volumes:
  elasticsearch_data:
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mltb-phase2-config
data:
  ENABLE_ENHANCED_LOGGING: "true"
  ENABLE_ALERT_SYSTEM: "true"
  ENABLE_BACKUP_SYSTEM: "true"
  ENABLE_PROFILER: "true"
  ENABLE_RECOVERY_MANAGER: "true"
  LOG_DIR: "/var/log/mltb"
  BACKUP_DIR: "/var/backups/mltb"
```

---

## 🔒 Security Best Practices

### 1. Log Filtering

```python
from bot.core.logger_manager import LoggerManager

# Filter sensitive data before logging
class SensitiveDataFilter(logging.Filter):
    SENSITIVE_PATTERNS = [
        r"token=[\w\-]+",
        r"password=[\w\-]+",
        r"api_key=[\w\-]+",
    ]
    
    def filter(self, record):
        for pattern in self.SENSITIVE_PATTERNS:
            record.msg = re.sub(pattern, "***REDACTED***", str(record.msg))
        return True

# Add filter to logger
logging.getLogger().addFilter(SensitiveDataFilter())
```

### 2. Backup Encryption

```python
from bot.core.backup_manager import BackupManager
from cryptography.fernet import Fernet

# Encrypt backups
async def create_encrypted_backup(paths, password):
    backup = await backup_manager.create_backup(paths)
    
    # Encrypt backup directory
    cipher = Fernet(Fernet.generate_key())
    # ... encryption logic ...
    
    return backup
```

### 3. Alert Authentication

```python
import os
from bot.core.alert_manager import alert_manager

# Use environment variables for credentials
alert_config = {
    "smtp_username": os.getenv("SMTP_USER"),
    "smtp_password": os.getenv("SMTP_PASS"),
    "telegram_token": os.getenv("TELEGRAM_TOKEN"),
}
```

---

## 📊 Monitoring & Observability

### Log Aggregation Setup

```bash
# Start Elasticsearch and Kibana
docker-compose up -d elasticsearch kibana

# Configure log shipping (in PHASE_2_FEATURES.md)
# Access Kibana at http://localhost:5601
```

### Create Alerts in Alertmanager

```yaml
# monitoring/alertmanager/config.yml
route:
  receiver: 'telegram'
  group_by: ['alertname']

receivers:
  - name: 'telegram'
    webhook_configs:
      - url: 'http://telegram-bot:8000/alerts'
        send_resolved: true
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "Phase 2 Monitoring",
    "panels": [
      {
        "title": "Slow Operations",
        "targets": [{"expr": "profiler_operation_duration_seconds"}]
      },
      {
        "title": "Backup Status",
        "targets": [{"expr": "backup_last_created_timestamp"}]
      }
    ]
  }
}
```

---

## 🧪 Testing Strategy

### Unit Tests

```bash
# Test individual managers
pytest tests/test_phase2_integration.py::TestLogger -v
pytest tests/test_phase2_integration.py::TestAlertSystem -v
pytest tests/test_phase2_integration.py::TestBackupSystem -v
```

### Integration Tests

```bash
# Test managers working together
pytest tests/test_phase2_integration.py::TestPhase2Integration -v

# Test backward compatibility
pytest tests/test_phase2_integration.py::TestBackwardCompatibility -v
```

### Load Tests

```bash
# Test under high logging/alerting load
python tests/load_tests/phase2_load_test.py
```

---

## 🆘 Troubleshooting

### Issue: Logs not appearing

**Solution:**
```python
# Enable debug logging
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Verify logger is enabled
from bot.core.logger_manager import logger_manager
print(f"Logger enabled: {logger_manager.is_enabled}")
```

### Issue: Alerts not sending

**Solution:**
```python
# Check alert manager is enabled
from bot.core.alert_manager import alert_manager
print(f"Alert system enabled: {alert_manager.is_enabled}")

# Verify subscribers are registered
print(f"Subscribers: {alert_manager._subscribers}")
```

### Issue: Backups creating errors

**Solution:**
```python
# Verify backup directory exists
from pathlib import Path
backup_dir = Path("backups")
backup_dir.mkdir(exist_ok=True)

# Check disk space
import shutil
stat = shutil.disk_usage(".")
print(f"Available space: {stat.free / (1024**3)} GB")
```

---

## 📈 Performance Tuning

### Optimize Logging

```python
# Use async logging for better performance
ENABLE_ASYNC_LOGGING = True
LOG_BATCH_SIZE = 100
LOG_FLUSH_INTERVAL = 1.0  # seconds
```

### Tune Backup Settings

```python
# Compress backups to save space
BACKUP_COMPRESSION = "gzip"
BACKUP_COMPRESSION_LEVEL = 6

# Incremental backups (only changed files)
BACKUP_INCREMENTAL = True
```

### Profile-Guided Optimization

```python
# Run profiler to find bottlenecks
slow_ops = profiler.get_slow_operations(threshold=2.0, limit=5)

# Then optimize top 5 slowest operations
for op in slow_ops:
    print(f"{op['operation']}: {op['average_duration']}s")
```

---

## 🚀 Deployment Checklist

- [ ] Dependencies installed (`pip install -r requirements-phase2.txt`)
- [ ] Configuration updated (all ENABLE flags set)
- [ ] Tests passing (`pytest tests/test_phase2_integration.py`)
- [ ] Startup code updated (initialize_phase2_services called)
- [ ] Docker Compose updated (if using containers)
- [ ] Monitoring configured (Elasticsearch, Kibana, Alertmanager)
- [ ] Backup paths verified
- [ ] Recovery procedures tested
- [ ] Security review (no sensitive data in logs)
- [ ] Documentation reviewed by team

---

## 📚 Additional Resources

- [Phase 2 Features Guide](PHASE_2_FEATURES.md) - Detailed feature documentation
- [Phase 1 Guide](PHASE_1_COMPLETE.md) - Integration with Phase 1
- [Structured Logging](https://www.rogerstevens.me/python-json-logging/) - JSON logging best practices
- [Prometheus Alerting](https://prometheus.io/docs/alerting/latest/overview/) - Alert management
- [Elasticsearch Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html) - Log aggregation

---

## 💬 Support

- **Issues:** Create GitHub issue with `phase-2` label
- **Questions:** Discuss in GitHub discussions
- **Contributions:** PRs welcome! Please follow guidelines

---

**Last Updated:** February 5, 2026  
**Maintained by:** justadi  
**Status:** Ready to Deploy ✅
