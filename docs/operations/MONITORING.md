# Bot Monitoring Tools

Quick reference for monitoring your Telegram bot's health and performance.

## Quick Status Check

```bash
./scripts/quick_check.sh
```

Shows instant bot status:
- ✅ Container running
- ✅ Bot process active
- ✅ Web service health
- ✅ Category B status
- 📝 Last log entry

**Use this for:** Quick health verification

---

## Full Health Monitor

```bash
./scripts/monitor_bot.sh
```

Detailed health report including:
- 📦 Container status
- 🌐 Web service (CPU, Memory, Disk)
- ⚡ Category B features & circuit breakers
- ⚠️ Recent errors (last 5)
- 🔧 Running processes

**Watch mode (auto-refresh every 10s):**
```bash
./scripts/monitor_bot.sh watch
```

**Use this for:** Comprehensive health dashboard

---

## Log Viewer

```bash
./scripts/view_logs.sh [lines] [filter]
```

**Examples:**
```bash
# Last 50 lines (default)
./scripts/view_logs.sh

# Last 200 lines
./scripts/view_logs.sh 200

# Filter for errors in last 500 lines
./scripts/view_logs.sh 500 error

# Filter for Category B logs
./scripts/view_logs.sh 200 "category b"
```

**Watch live logs:**
```bash
docker exec 9ea93d6c31a9 tail -f /app/data/logs/log.txt
```

**Use this for:** Log analysis and troubleshooting

---

## Key Locations

### Logs
- **Main log:** `/app/data/logs/log.txt` (inside container)
- **Access:** `docker exec 9ea93d6c31a9 cat /app/data/logs/log.txt`

### Health Endpoints
- **Web Health:** http://localhost:8060/health
- **Metrics:** http://localhost:9090/metrics

### Container
- **Container ID:** `9ea93d6c31a9`
- **Access shell:** `docker exec -it 9ea93d6c31a9 bash`

---

## Monitoring Checklist

### Daily
- [ ] Run `./scripts/quick_check.sh` - Verify all systems operational
- [ ] Check circuit breaker failures (should be 0)
- [ ] Verify CPU < 70%, Memory < 80%

### Weekly
- [ ] Review error logs: `./scripts/view_logs.sh 1000 error`
- [ ] Check disk usage (should be < 80%)
- [ ] Verify backup process completed

### When Issues Occur
1. Run `./scripts/monitor_bot.sh` - Get full status
2. Check logs: `./scripts/view_logs.sh 500 error`
3. Review circuit breaker states (should be CLOSED)
4. Check container: `docker logs 9ea93d6c31a9 | tail -100`
5. Restart if needed: `docker restart 9ea93d6c31a9`

---

## Alerts to Watch For

### ⚠️ Warning Signs
- Circuit breaker state: OPEN or HALF_OPEN
- Failure counts approaching thresholds (Telegram: 5, GDrive: 3, Aria2: 5)
- Memory usage > 80%
- Disk usage > 85%
- Persistent ERROR messages in logs

### ✅ Healthy Signs
- Circuit breakers: CLOSED
- All failure counts: 0
- Web health: "healthy"
- CPU < 50% (idle), < 80% (active)
- No recent ERROR/CRITICAL in logs

---

## Category B Status

Check Category B features:
```bash
docker exec 9ea93d6c31a9 python3 -c "
import sys
sys.path.insert(0, '/app/src')
from bot.core.category_b_integration import category_b
print('Circuit Breakers:', category_b.telegram_breaker.state.name)
print('Failures:', category_b.telegram_breaker.failure_count)
"
```

---

## Troubleshooting

**Bot not responding:**
1. Check container: `docker ps | grep mltb`
2. Check logs: `./scripts/view_logs.sh 100 error`
3. Restart: `docker restart 9ea93d6c31a9`

**High resource usage:**
1. Check processes: `docker exec 9ea93d6c31a9 ps aux`
2. Review active downloads
3. Check for stuck tasks

**Circuit breaker open:**
- Normal recovery time: 60-120 seconds
- Will auto-transition to HALF_OPEN then CLOSED
- If persists, check external service availability

---

## Quick Commands Reference

```bash
# Container status
docker ps | grep mltb

# Container stats
docker stats 9ea93d6c31a9 --no-stream

# Recent logs
docker exec 9ea93d6c31a9 tail -50 /app/data/logs/log.txt

# Container shell
docker exec -it 9ea93d6c31a9 bash

# Restart bot
docker restart 9ea93d6c31a9

# Stop bot
docker stop 9ea93d6c31a9

# Start bot
docker start 9ea93d6c31a9
```

---

**Last Updated:** 2026-02-27  
**Bot Version:** 3.1.0  
**Category B:** ✅ Enabled
