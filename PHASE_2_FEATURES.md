# Phase 2: Enhanced Logging & Monitoring Infrastructure
## Safe Innovation Path - Production-Ready Enhancements

**Date:** February 5, 2026  
**Status:** Development Ready  
**Version:** Phase 2 (v3.2.0)

---

## 📋 Overview

Phase 2 focuses on **operational excellence** with enhanced logging, error tracking, automated backup systems, and performance monitoring. All features are **disabled by default** and can be independently enabled as needed.

### Key Components

1. **Enhanced Logging Manager** - Structured JSON logging for aggregation
2. **Alert System** - Error detection and notification framework
3. **Backup Manager** - Automated backup and restoration
4. **Performance Profiler** - Operation monitoring and bottleneck detection
5. **Recovery Manager** - Data integrity and auto-recovery

---

## 🚀 Quick Start

### Installation

```bash
# Install Phase 2 dependencies
pip install -r requirements-phase2.txt

# Or for full ELK stack support
pip install -r requirements-phase2.txt[elk]
```

### Enable Features (in config.py)

```python
# Logging
ENABLE_ENHANCED_LOGGING = True
LOG_LEVEL = "INFO"

# Alerts
ENABLE_ALERT_SYSTEM = True

# Backups
ENABLE_BACKUP_SYSTEM = True
BACKUP_FREQUENCY = "daily"

# Profiling
ENABLE_PROFILER = True
PROFILE_THRESHOLD = 1.0  # seconds

# Recovery
ENABLE_RECOVERY_MANAGER = True
ENABLE_AUTO_RECOVERY = True
```

---

## 🔍 Component Details

### 1. Enhanced Logging Manager

**File:** `bot/core/logger_manager.py`  
**Lines:** 350+

Provides structured JSON logging for better log aggregation and analysis.

**Features:**
- JSON-formatted logs for easy parsing
- Log rotation and cleanup
- Multiple log handlers (file, console, errors)
- Custom event logging
- Log statistics

**Usage:**

```python
from bot.core.logger_manager import logger_manager

logger_manager.enable()

# Log custom events
logger_manager.log_download(
    task_id="download_123",
    filename="large_file.zip",
    size_bytes=1073741824,
    duration=3600.0,
    speed=298.0,
    status="completed"
)

# Get statistics
stats = logger_manager.get_log_stats()
print(f"Total logs: {stats['log_file_count']}")
```

**Configuration:**
```python
ENABLE_ENHANCED_LOGGING = True
LOG_DIR = "logs"
LOG_LEVEL = "INFO"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5
```

---

### 2. Alert System

**File:** `bot/core/alert_manager.py`  
**Lines:** 400+

Comprehensive error tracking and alert management.

**Features:**
- Multiple alert severity levels (LOW, MEDIUM, HIGH, CRITICAL)
- Alert types (download failed, disk full, memory high, API errors, etc.)
- Subscriber pattern for notifications
- Alert filtering and retrieval
- Automatic summary generation

**Usage:**

```python
from bot.core.alert_manager import alert_manager, AlertType, AlertSeverity

alert_manager.enable()

# Subscribe to alerts
async def on_download_failed(alert):
    print(f"Alert: {alert.title}")
    await send_telegram_notification(alert)

alert_manager.subscribe(AlertType.DOWNLOAD_FAILED, on_download_failed)

# Trigger alert
await alert_manager.trigger_alert(
    AlertType.DOWNLOAD_FAILED,
    AlertSeverity.HIGH,
    "Download Failed",
    "Failed to download file",
    task_id="task_123",
    details={"error": "Connection timeout"}
)

# Get alerts
recent_alerts = alert_manager.get_alerts(limit=10, severity=AlertSeverity.HIGH)
summary = alert_manager.get_alert_summary()
```

**Configuration:**
```python
ENABLE_ALERT_SYSTEM = True
ALERT_RETENTION_HOURS = 24
ALERT_CHANNELS = {
    "critical": ["telegram", "email"],
    "high": ["telegram"],
    "medium": ["log"],
    "low": ["log"],
}
```

---

### 3. Backup Manager

**File:** `bot/core/backup_manager.py`  
**Lines:** 450+

Automated backup creation, management, and restoration.

**Features:**
- Create backups of critical paths
- Automatic backup scheduling
- Backup verification and integrity checks
- Restore from backup with validation
- Auto-cleanup of old backups
- Backup metadata tracking

**Usage:**

```python
from bot.core.backup_manager import backup_manager

backup_manager.enable()

# Create backup
result = await backup_manager.create_backup(
    source_paths=["config.py", "bot/"],
    backup_name="pre_release_backup",
    description="Configuration backup before release"
)
print(f"Backup created: {result['backup_name']}")

# List backups
backups = backup_manager.list_backups()
for backup in backups:
    print(f"{backup['name']}: {backup['size']} bytes")

# Restore from backup
success = await backup_manager.restore_backup(
    backup_name="pre_release_backup",
    restore_path="/restore/location"
)

# Verify backup
is_valid = backup_manager.verify_backup("pre_release_backup")

# Cleanup old backups
deleted = backup_manager.cleanup_old_backups(days=30)
print(f"Deleted {deleted} old backups")

# Get statistics
stats = backup_manager.get_backup_stats()
```

**Configuration:**
```python
ENABLE_BACKUP_SYSTEM = True
BACKUP_DIR = "backups"
BACKUP_FREQUENCY = "daily"
CRITICAL_BACKUP_PATHS = [
    "config.py",
    "tokens",
    "data",
]
BACKUP_RETENTION = {
    "hourly": 24,
    "daily": 30,
    "weekly": 12,
}
```

---

### 4. Performance Profiler

**File:** `bot/core/profiler.py`  
**Lines:** 350+

Monitor and analyze operation performance to identify bottlenecks.

**Features:**
- Profile sync and async operations
- Operation statistics (avg, min, max, median)
- Slow operation detection
- Manual timing with Timer class
- Auto-cleanup of old metrics

**Usage:**

```python
from bot.core.profiler import profiler

profiler.enable()

# Profile synchronous code
with profiler.profile_sync("download_operation"):
    # ... download code ...
    pass

# Profile async code
async with profiler.profile_async("upload_operation"):
    # ... upload code ...
    pass

# Manual timing
timer = profiler.mark_operation("critical_operation")
# ... code ...
duration = timer.stop()

# Get statistics
stats = profiler.get_stats("download_operation")
# {
#     "operation": "download_operation",
#     "call_count": 42,
#     "average_duration": 123.456,
#     "min_duration": 45.2,
#     "max_duration": 234.1,
#     "std_dev": 32.4
# }

# Find slow operations
slow_ops = profiler.get_slow_operations(threshold=5.0)

# Reset metrics
profiler.reset()
```

**Configuration:**
```python
ENABLE_PROFILER = True
PROFILE_THRESHOLD = 1.0  # seconds
PROFILED_OPERATIONS = None  # None = all
PROFILER_RETENTION_HOURS = 24
```

---

### 5. Recovery Manager

**File:** `bot/core/recovery_manager.py`  
**Lines:** 380+

Data integrity checking and automatic recovery.

**Features:**
- Verify data integrity
- Corruption detection
- Automatic repair procedures
- File hash validation
- Directory structure verification
- Recovery status tracking

**Usage:**

```python
from bot.core.recovery_manager import recovery_manager

recovery_manager.enable()

# Verify integrity
is_valid, details = await recovery_manager.verify_integrity(
    "path/to/data",
    check_hash=True,
    check_structure=True
)

if not is_valid:
    print(f"Errors: {details['errors']}")

# Attempt repair
repaired = await recovery_manager.repair_corrupted_data(
    path="path/to/corrupted/data",
    backup_source="backup/data"
)

# Auto-recovery for critical paths
critical_paths = ["config.py", "bot/"]
recovery_report = await recovery_manager.auto_recover(
    critical_paths=critical_paths,
    backup_dir="backups"
)
print(f"Recovery: {recovery_report['valid_paths']} valid, "
      f"{recovery_report['repaired_paths']} repaired")

# Get history
history = recovery_manager.get_integrity_history(limit=50)

# Get status
status = recovery_manager.get_recovery_status()
```

**Configuration:**
```python
ENABLE_RECOVERY_MANAGER = True
ENABLE_AUTO_RECOVERY = False
RECOVERY_CRITICAL_PATHS = ["config.py", "bot/__main__.py"]
INTEGRITY_CHECK_INTERVAL = 3600  # seconds
```

---

## 🔗 Integration Points

### With Phase 1

Phase 2 enhances Phase 1 infrastructure:

- **Logging → Metrics:** Profiler data feeds into Prometheus metrics
- **Alerts → Celery:** Alert triggers can dispatch Celery tasks
- **Backups → Redis:** Backup metadata stored in Redis cache
- **Recovery → Monitoring:** Recovery events trigger Grafana alerts

### Docker Compose Integration

```yaml
services:
  # Phase 2 services
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
```

---

## 📊 Monitoring Dashboard

Access monitoring at:
- **Logs:** Kibana (`http://localhost:5601`) - View structured logs
- **Alerts:** AlertManager UI (`http://localhost:9093`) - Manage alerts
- **Backups:** API endpoint or CLI tool
- **Performance:** Grafana (`http://localhost:3000`) - View metrics

---

## 🔐 Security Considerations

1. **Log Sensitivity:** Remove sensitive data from logs before enabling
2. **Backup Encryption:** Consider encrypting backups
3. **Alert Credentials:** Use environment variables for SMTP/Telegram
4. **Access Control:** Restrict access to log files and backups

---

## ⚙️ Advanced Configuration

### Conditional Feature Enable

```python
import os

# Enable only in production
if os.getenv("ENV") == "production":
    ENABLE_ENHANCED_LOGGING = True
    ENABLE_BACKUP_SYSTEM = True
    ENABLE_RECOVERY_MANAGER = True
```

### Custom Alert Handlers

```python
from bot.core.alert_manager import alert_manager

async def send_slack_notification(alert):
    # Custom Slack integration
    await slack_client.send_message(alert.title)

alert_manager.register_handler(send_slack_notification)
```

### Backup Scheduling with Celery

```python
from celery import shared_task
from bot.core.backup_manager import backup_manager

@shared_task
def scheduled_backup():
    return await backup_manager.create_backup(
        source_paths=["config.py", "bot/"],
        backup_name=f"backup_{datetime.now().isoformat()}"
    )

# In celery_app.py beat schedule:
backup_manager.create_backup_schedule()
```

---

## 📈 Performance Impact

**Without Features Enabled:**
- Zero overhead (features disabled by default)

**With All Features Enabled:**
- CPU: +2-3%
- Memory: +50-100 MB
- Disk I/O: Minimal (logging batched)

---

## 🧪 Testing

Run Phase 2 tests:

```bash
# All Phase 2 tests
pytest tests/test_phase2_integration.py -v

# Specific component tests
pytest tests/test_phase2_integration.py::TestAlertSystem -v

# With coverage
pytest tests/test_phase2_integration.py --cov=bot.core
```

---

## 📚 Next Steps

1. **Enable Enhanced Logging** - Start collecting structured logs
2. **Setup Alert System** - Configure notification channels
3. **Configure Backups** - Define critical paths and retention
4. **Enable Profiler** - Identify performance bottlenecks
5. **Activate Recovery** - Ensure data integrity

---

## 📝 Troubleshooting

**Logs not appearing in Elasticsearch?**
- Check `ENABLE_ELK_INTEGRATION` is True
- Verify Elasticsearch is running (`curl http://localhost:9200`)

**Alerts not triggering?**
- Verify `ENABLE_ALERT_SYSTEM` is True
- Check subscriber callbacks are registered
- Review alert thresholds in config

**Backups failing?**
- Ensure backup directory exists and is writable
- Check critical paths exist before backup
- Verify disk space is available

---

## 🤝 Contributing

Phase 2 enhancements welcome! Areas for contribution:
- Additional alert notification channels (Slack, Discord, etc.)
- Backup compression and encryption
- Advanced profiling features
- Log visualization improvements

---

## 📄 License

Same as main project (see LICENSE file)

---

**Questions?** Open an issue on GitHub or check [Phase 1 documentation](PHASE_1_COMPLETE.md).
