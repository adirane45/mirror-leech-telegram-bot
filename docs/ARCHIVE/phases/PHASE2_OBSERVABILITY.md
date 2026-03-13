# Phase 2 Implementation - Observability & Monitoring

## ✅ Completed Implementation

### 1. Structured Logging System
**File:** [bot/core/logging_config.py](../bot/core/logging_config.py)

**Features:**
- **JSON formatted logs** for easy parsing and aggregation
- **Request ID tracking** across all services
- **Log rotation** (50MB files, 10 backups)
- **Separate error logs** for easier debugging
- **Performance logging** with dedicated handler
- **Environment-based configuration** (LOG_LEVEL, LOG_DIR)
- **Thread-safe** logging with request context

**Usage:**
```python
from bot.core.logging_config import setup_logging, log_performance, set_request_id

# Setup logging
logger = setup_logging("my-service", log_level="INFO", json_logs=True)

# Set request ID for tracking
request_id = set_request_id()

# Log with context
logger.info("Processing download", extra={"user_id": 123, "file_size": 1024})

# Log performance
log_performance("download_file", duration=5.2, extra={"file_size": 1024})
```

### 2. Prometheus Alerting Rules
**File:** [integrations/monitoring/prometheus/alerts.yml](../integrations/monitoring/prometheus/alerts.yml)

**Alert Categories:**
- **Application Alerts**: High error rate, service down, memory/CPU usage
- **Download Alerts**: High failure rate, slow speeds, queue backlog
- **Database Alerts**: Connection issues, slow queries
- **Redis Alerts**: Connection failures, memory usage, cache hit rate
- **Celery Alerts**: Task failures, worker status, queue length

**Severity Levels:**
- **Critical**: Immediate action required (service down, connections failed)
- **Warning**: Action needed soon (high resource usage, slow performance)
- **Info**: Informational (slow downloads, low cache hit rate)

### 3. Alertmanager Configuration
**File:** [integrations/monitoring/alertmanager/alertmanager.yml](../integrations/monitoring/alertmanager/alertmanager.yml)

**Features:**
- **Smart routing** by severity level
- **Telegram notifications** with formatted messages
- **Alert grouping** to reduce noise
- **Inhibition rules** to suppress lower-severity alerts
- **Repeat intervals** based on severity
- **Templated messages** for clarity

**Notification Timing:**
- Critical: Immediate (repeat every 5m)
- Warning: Group 30s, repeat every 3h
- Info: Group 5m, repeat every 24h

### 4. Enhanced Docker Compose
**File:** [docker-compose.yml](../docker-compose.yml)

**Added Services:**
- **Alertmanager** - Alert routing and notifications
- **Updated Prometheus** - With alerting rules
- **Persistent storage** for alertmanager data

**Configuration:**
```bash
# Start monitoring stack
docker-compose up -d prometheus alertmanager grafana

# View alerts
open http://localhost:9093

# View metrics
open http://localhost:9091

# View dashboards
open http://localhost:3000
```

---

## 🎯 **Key Improvements Achieved**

### Observability:
- ✅ Structured JSON logs for easy parsing
- ✅ Request ID tracking across services
- ✅ Separate performance logs
- ✅ Automatic log rotation (50MB files)
- ✅ Environment-based configuration

### Monitoring:
- ✅ 25+ alert rules covering all components
- ✅ Smart alert routing by severity
- ✅ Telegram notifications with rich formatting
- ✅ Alert grouping to reduce noise
- ✅ Prometheus metrics retention (15 days)

### Alerting:
- ✅ Critical alerts sent immediately
- ✅ Warnings grouped every 30s
- ✅ Info alerts summarized daily
- ✅ Lower-severity alerts suppressed when critical
- ✅ Automatic alert resolution tracking

---

## 🚀 **Setup Instructions**

### 1. Configure Environment Variables
```bash
# Add to config/.env.production
LOG_LEVEL=INFO
LOG_DIR=data/logs

# Alertmanager (for Telegram notifications)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ALERT_CHAT_ID=your_chat_id_here
```

### 2. Initialize Logging in Your Application
```python
# In bot/__main__.py or bot/__init__.py
from bot.core.logging_config import setup_logging

# Setup logging at application startup
logger = setup_logging("mirror-leech-bot", log_level="INFO")
logger.info("Application started")
```

### 3. Start Monitoring Stack
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f alertmanager
docker-compose logs -f prometheus
```

### 4. Access Dashboards
- **Prometheus**: http://localhost:9091
- **Alertmanager**: http://localhost:9093
- **Grafana**: http://localhost:3000 (admin/mltbadmin)

### 5. Test Alerts
```bash
# Trigger a test alert
curl -X POST http://localhost:9093/api/v1/alerts -d '[{
  "labels": {"alertname": "TestAlert", "severity": "warning"},
  "annotations": {"summary": "Test alert", "description": "Testing alerting system"}
}]'
```

---

## 📊 **Monitoring Metrics**

### Application Metrics:
- HTTP request rate and errors
- Response time percentiles
- Active connections
- Memory and CPU usage

### Download Metrics:
- Download success/failure rate
- Download speed (bytes/sec)
- Queue length
- Active downloads

### Database Metrics:
- Query duration
- Connection pool usage
- Operations per second
- Lock wait time

### Cache Metrics:
- Hit/miss rate
- Memory usage
- Eviction rate
- Key count

### Worker Metrics:
- Task success/failure rate
- Task duration
- Active workers
- Queue depth

---

## 🔔 **Alert Examples**

### Critical Alert (Telegram):
```
🚨 CRITICAL ALERT

Alert: ServiceDown
Component: infrastructure

⚠️ Service is down
mirror-leech-bot has been down for more than 2 minutes

Started: 18:45:23

Action required immediately!
```

### Warning Alert (Telegram):
```
⚠️ Warning

Alert: HighMemoryUsage
Component: resources

Memory usage is 87% (threshold: 85%)
```

### Info Alert (Telegram):
```
ℹ️ Info

Alert: SlowDownloadSpeed

Downloads are slow
Average speed is 850KB/s (threshold: 1MB/s)
```

---

## 📈 **Performance Logging Examples**

```python
import time
from bot.core.logging_config import log_performance, get_logger

logger = get_logger(__name__)

# Time an operation
start = time.time()
result = download_file(url)
duration = time.time() - start

# Log performance
log_performance(
    operation="download_file",
    duration=duration,
    extra={
        "url": url,
        "file_size": result.size,
        "speed_mbps": (result.size / duration) / 1024 / 1024
    }
)
```

**Log Output (JSON):**
```json
{
  "timestamp": "2026-02-08T18:30:45Z",
  "level": "INFO",
  "logger": "mirror-leech-bot.performance",
  "message": "Performance: download_file",
  "module": "downloader",
  "function": "process_download",
  "line": 156,
  "extra": {
    "operation": "download_file",
    "duration_seconds": 12.3456,
    "duration_ms": 12345.6,
    "url": "https://example.com/file.zip",
    "file_size": 104857600,
    "speed_mbps": 8.09
  }
}
```

---

## 🔧 **Troubleshooting**

### Logs not appearing:
```bash
# Check log directory exists
ls -la data/logs/

# Check file permissions
chmod 755 data/logs/

# Check log level
grep LOG_LEVEL config/.env.production
```

### Alerts not sending:
```bash
# Verify Alertmanager is running
docker-compose ps alertmanager

# Check Alertmanager logs
docker-compose logs alertmanager

# Verify Telegram token
docker-compose exec alertmanager cat /etc/alertmanager/alertmanager.yml | grep bot_token

# Test alert firing
docker-compose exec prometheus promtool check rules /etc/prometheus/alerts.yml
```

### Prometheus not scraping:
```bash
# Check Prometheus targets
open http://localhost:9091/targets

# Verify configuration
docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Check network connectivity
docker-compose exec prometheus wget -O- http://app:8080/metrics
```

---

## 🎯 **Best Practices**

### Logging:
1. **Always use structured logging** with the `extra` parameter
2. **Include request IDs** for tracing across services request
3. **Log at appropriate levels**: DEBUG for dev, INFO for prod
4. **Use performance logging** for operations > 100ms
5. **Don't log sensitive data** (passwords, tokens, keys)

### Alerting:
1. **Set meaningful thresholds** based on actual usage patterns
2. **Use alert grouping** to avoid notification spam
3. **Test alerts regularly** to ensure they work
4. **Document runbooks** for each alert type
5. **Review and tune alerts** based on false positive rate

### Monitoring:
1. **Monitor what matters** - focus on user-impacting metrics
2. **Set up dashboards** for quick problem identification
3. **Use percentiles** (p95, p99) not just averages
4. **Monitor trends** over time, not just current values
5. **Set up SLOs** (Service Level Objectives) for critical services

---

## 📝 **Next Steps - Phase 3**

With Phase 2 complete, consider implementing:

1. **Grafana Dashboards** - Visual monitoring
2. **Log Aggregation** - Loki or ELK stack
3. **Distributed Tracing** - Jaeger or Zipkin
4. **Custom Metrics** - Business-specific KPIs
5. **Automated Remediation** - Self-healing based on alerts

---

**Created:** February 8, 2026
**Phase:** 2 - Observability & Monitoring
**Status:** ✅ Complete and Operational
**Time Taken:** ~2 hours
