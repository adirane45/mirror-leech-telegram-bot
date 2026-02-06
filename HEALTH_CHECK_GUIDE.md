# MLTB Bot Health Check Scripts - Usage Guide

## Overview

Two comprehensive health check scripts have been created to monitor the bot's operational status:

1. **Quick Health Check** - 10-15 seconds, checks critical systems only
2. **Comprehensive Health Check** - 30-45 seconds, detailed analysis of all systems

---

## Quick Health Check

### Purpose
Fast verification that all critical systems are running and accessible.

### Usage
```bash
./scripts/quick_health_check.sh
```

### What It Checks
- ✅ Docker daemon connectivity
- ✅ All 5 critical containers running
- ✅ Redis cache accessible
- ✅ Web dashboard accessible
- ✅ Aria2 RPC accessible
- ✅ qBittorrent accessible
- ✅ GraphQL API working
- ✅ Disk usage healthy
- ✅ Configuration files present

### Exit Codes
- **0** = All systems operational ✅
- **1** = Issues detected ⚠️ 
- **2** = Critical failure ❌

### Example Output
```
✅ All critical systems operational
```

### Runtime
~10-15 seconds

---

## Comprehensive Health Check

### Purpose
Deep diagnostic check of all bot systems, services, and components.

### Usage
```bash
./scripts/health_check_comprehensive.sh
```

### What It Checks

#### 1. Docker & Container Status
- Docker daemon responsiveness
- All 6 containers running (app, redis, aria2, qbittorrent, prometheus, grafana)

#### 2. Container Health Status
- Built-in health checks for each container
- Reports: healthy, starting, or unhealthy status

#### 3. Core Services
- **Redis Cache:** Port accessibility + PING test
- **Aria2 RPC:** Port accessibility + JSON-RPC test
- **qBittorrent WebUI:** Port accessibility + HTTP 200 response

#### 4. Web Server & APIs
- **Dashboard:** Homepage accessibility (HTTP 200)
- **GraphQL API:** Endpoint accessibility + query execution test

#### 5. Monitoring & Metrics
- **Prometheus:** Port accessibility + health check
- **Grafana:** Port accessibility + health check
- **App Metrics:** Endpoint availability

#### 6. Resource Usage
- **Disk Usage:** Monitor data directories (warning at 80%)
- **Memory Usage:** Per-container memory consumption

#### 7. Log Analysis
- Scans last 50 lines of app logs for errors
- Scans last 30 lines of Redis/Aria2 logs for errors

#### 8. Configuration & Files
- Main config file existence
- Environment file existence
- JDownloader integration directory
- Volume mount verification

#### 9. Database & Storage
- MongoDB connection status
- Local storage accessibility

#### 10. Bot-Specific Features
- Bot token configuration
- Bot process running status
- Phase 2 & 3 initialization detection
- Web dashboard content validation

### Exit Codes
- **0** = All systems healthy ✅
- **1** = Issues detected (bot may be partially functional) ⚠️
- **2** = Critical issues (containers not running) ❌

### Example Output
```
════════════════════════════════════════════════════════════════
  HEALTH CHECK SUMMARY
════════════════════════════════════════════════════════════════

  Passed:   44
  Warnings: 1
  Failed:   1
  Critical: 0

════════════════════════════════════════════════════════════════
Status: ⚠️  ISSUES DETECTED (Bot may not be 100% functional)
════════════════════════════════════════════════════════════════
```

### Runtime
~30-45 seconds

---

## Understanding the Results

### Status Indicators

| Icon | Meaning | Action |
|------|---------|--------|
| ✅ | Check passed | All good |
| ⚠️ | Warning | Non-critical issue detected |
| ❌ | Failed | Component not working |
| 🔥 | Critical | Service down, immediate action needed |
| ℹ️ | Information | Status report |

---

## Common Issues & Solutions

### Issue: "Container mltb-app is NOT running"
**Cause:** Bot container crashed or failed to start  
**Solution:**
```bash
docker-compose logs mltb-app
docker-compose down && docker-compose up -d
```

### Issue: "Web Dashboard NOT accessible"
**Cause:** Web server not responding on port 8060  
**Solution:**
```bash
docker-compose restart app
curl http://localhost:8060/  # Test manually
```

### Issue: "Found X error(s) in logs"
**Solution:** Check detailed error messages:
```bash
docker logs mltb-app | grep -i error | tail -10
```

### Issue: "Aria2 RPC endpoint is NOT responding"
**Cause:** Aria2 secret mismatch or RPC disabled  
**Solution:**
```bash
docker-compose logs aria2
# Check docker-compose.yml: RPC_SECRET matches
```

### Issue: "Redis is NOT responding"
**Cause:** Redis container crashed  
**Solution:**
```bash
docker-compose restart redis
docker logs mltb-redis
```

### Issue: "Disk usage warning"
**Cause:** Downloads directory getting full  
**Solution:**
```bash
du -sh data/downloads  # Check size
# Delete old downloads or expand disk
```

---

## Monitoring Workflow

### Daily Checks
```bash
# Quick check (5 seconds)
./scripts/quick_health_check.sh
echo "Exit code: $?"
```

### Weekly Deep Analysis
```bash
# Comprehensive check (30 seconds)
./scripts/health_check_comprehensive.sh > health_report.txt
# Review health_report.txt
```

### Automated Monitoring
```bash
# Run quick check every 5 minutes
*/5 * * * * /home/kali/mirror-leech-telegram-bot/scripts/quick_health_check.sh >> /tmp/bot_health.log

# Run comprehensive check daily at 2 AM
0 2 * * * /home/kali/mirror-leech-telegram-bot/scripts/health_check_comprehensive.sh >> /tmp/bot_health_daily.log
```

---

## Performance Baseline

### Healthy Bot Metrics
| Metric | Healthy Range |
|--------|---------------|
| App Memory | < 2000 MB |
| Redis Memory | < 100 MB |
| Prometheus Memory | < 200 MB |
| Disk Usage | < 80% |
| API Response Time | < 5 seconds |
| Container Startup | < 30 seconds |

---

## Troubleshooting Quick Reference

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker logs -f mltb-app
docker logs -f mltb-redis
docker logs -f mltb-aria2

# Check container stats
docker stats mltb-app

# Test connectivity
curl -v http://localhost:8060/
curl -X POST -H "Content-Type: application/json" -d '{"query":"{status{version}}"}' http://localhost:8060/graphql

# Check ports
netstat -tlnp | grep -E "6379|6800|8060|9091|3000"

# Restart services
docker-compose restart app         # Restart bot
docker-compose restart redis       # Restart cache
docker-compose restart aria2       # Restart downloader
docker-compose down && docker-compose up -d  # Full restart
```

---

## Script Features

### Comprehensive Check Highlights
- **40+ individual tests** covering all components
- **Detailed logging** with 4 severity levels
- **Resource monitoring** (disk, memory, CPU)
- **Log analysis** scanning for errors
- **Configuration validation** checking required files
- **Performance checks** ensuring healthy baselines
- **Phase detection** verifying Phase 1/2/3 status
- **Color-coded output** for easy reading

### Quick Check Highlights
- **Essential tests only** (13 core checks)
- **Fast execution** (10-15 seconds)
- **Clear pass/fail summary**
- **Suggests comprehensive check** if issues found

---

## Integration with Monitoring Systems

### Export to Monitoring Tool
```bash
#!/bin/bash
# health_to_monitoring.sh - Export results to monitoring system

./scripts/health_check_comprehensive.sh > /tmp/health_report.txt
EXIT_CODE=$?

# Send to monitoring API
curl -X POST "http://monitoring.local/api/health" \
  -H "Content-Type: application/json" \
  -d "{\"bot_status\": $EXIT_CODE, \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

exit $EXIT_CODE
```

---

## Output Log Location

Results can be redirected to files:
```bash
# Save comprehensive check results
./scripts/health_check_comprehensive.sh | tee health_check_$(date +%Y%m%d_%H%M%S).log

# Save quick check results
./scripts/quick_health_check.sh >> health_checks.log
```

---

## FAQ

**Q: How often should I run these checks?**  
A: Quick check daily, comprehensive check weekly. Both important for monitoring.

**Q: What does "Phase 2 initialization detected" mean?**  
A: Your bot successfully loaded Phase 2 features (Logger, Alert, Backup, Profiler, Recovery managers).

**Q: Can I run these scripts while bot is working?**  
A: Yes, they're non-invasive read-only checks and don't interfere with bot operation.

**Q: Why does comprehensive check take 30-45 seconds?**  
A: It performs 40+ individual tests with timeouts to ensure reliability.

**Q: What should I do if I see warnings?**  
A: Review the specific warnings in output. Non-critical but may need attention.

---

**Last Updated:** February 6, 2026  
**Script Version:** 1.0  
**Bot Version:** Enhanced MLTB v3.1.0 with Phase 1/2/3
