# Next Steps - Production Ready Bot

Your bot is now **fully operational** with Category B features enabled. Here are the recommended next steps:

---

## 🎯 Immediate Actions (Do These First)

### 1. **Backup Current Working State** ✅
```bash
./scripts/backup_current_state.sh
```
Creates a backup of all configuration files and core components. **Do this now** before making any changes.

### 2. **Test Bot with Real Workload** 🧪
Send a test download via Telegram:
```
/start                    # Verify bot responds
/help                     # Check available commands
/mirror <small_file_url>  # Test download functionality
/qstatus                  # Check queue status (admin only)
```

**What to Watch:**
- Download starts successfully
- Queue system assigns priority
- Progress updates appear
- No errors in logs: `./scripts/view_logs.sh 100`

### 3. **Set Up Automated Monitoring** 📊
Add to crontab for regular health checks:
```bash
# Edit crontab
crontab -e

# Add these lines:
*/15 * * * * /home/kali/mirror-leech-telegram-bot/scripts/quick_check.sh >> /tmp/bot_health.log 2>&1
0 */6 * * * /home/kali/mirror-leech-telegram-bot/scripts/backup_current_state.sh
```

This will:
- Check bot health every 15 minutes
- Create backups every 6 hours

---

## ⚙️ Optional Configuration Tuning

### Circuit Breaker Thresholds
**File:** [src/bot/core/category_b_integration.py](src/bot/core/category_b_integration.py#L52-L67)

Current settings:
- Telegram API: 5 failures before opening
- Google Drive: 3 failures before opening  
- Aria2 Client: 5 failures before opening

**Adjust if:**
- Too sensitive: Increase failure_threshold
- Not responsive enough: Decrease failure_threshold
- Different recovery time needed: Change timeout (currently 60/120/30s)

### Queue Priorities
**File:** `src/bot/core/priority_queue.py`

Configure queue weights based on your usage:
- VIP users get higher priority
- Emergency tasks jump the queue
- Batch jobs run in background

### Retry Engine
**File:** `src/bot/core/smart_retry.py`

Current: Exponential backoff 5s → 3600s (1 hour max)

**Tune if:**
- Need faster retries: Reduce max delay
- Want more attempts: Increase max_retries
- Different backoff strategy: Adjust multiplier

---

## 📈 Performance Optimization

### 1. **Monitor Resource Usage**
```bash
# Watch in real-time
./scripts/monitor_bot.sh watch

# Check current usage
docker stats 9ea93d6c31a9 --no-stream
```

**Action if:**
- CPU > 80% sustained: Review parallel download settings
- Memory > 80%: Check for memory leaks in logs
- Disk > 85%: Clean old downloads, enable auto-cleanup

### 2. **Review Parallel Downloads**
Test with different chunk counts:
- Current: 3-5 chunks per download
- Fast connection: Increase to 8-10
- Slow/unstable: Decrease to 2-3

### 3. **Database Optimization**
```bash
# Check MongoDB connection
docker exec 9ea93d6c31a9 python3 -c "from pymongo import MongoClient; print('MongoDB:', 'Connected' if MongoClient().admin.command('ping')['ok'] else 'Failed')"

# Check Redis
docker exec 9ea93d6c31a9 redis-cli ping
```

---

## 🔒 Security Hardening (If Not Done)

### 1. **Restrict Bot Access**
Update authorized users in config:
- Set `OWNER_ID` 
- Configure `USER_SESSION_STRING` for authorized users
- Enable `USERS_ONLY_MODE` if needed

### 2. **Enable HTTPS**
See [deployment/docker-compose.secure.yml](deployment/docker-compose.secure.yml)

### 3. **Set Up Firewall Rules**
```bash
# Allow only necessary ports
ufw allow 8060/tcp  # Web panel
ufw allow 22/tcp    # SSH
ufw enable
```

---

## 📊 Monitoring & Alerts

### Daily Checks
```bash
./scripts/quick_check.sh
```
✅ All green = Healthy  
⚠️ Any yellow/red = Investigate

### Weekly Review
```bash
# Check error trends
./scripts/view_logs.sh 1000 error

# Review circuit breaker performance
./scripts/monitor_bot.sh

# Verify backups exist
ls -lh data/backups/
```

### Set Up Alerts (Optional)
Integrate with monitoring tools:
- Prometheus metrics: http://localhost:9090/metrics
- Health endpoint: http://localhost:8060/health
- Custom alerting via webhook/email

---

## 🧪 Testing Checklist

Before going fully production:

- [ ] Test small file download (<100MB)
- [ ] Test large file download (>1GB)
- [ ] Test mirror to Google Drive (if configured)
- [ ] Test queue priority with multiple downloads
- [ ] Verify retry engine on failed download
- [ ] Test circuit breaker by simulating API failure
- [ ] Confirm authorized users can use bot
- [ ] Verify unauthorized users are blocked
- [ ] Test all admin commands work
- [ ] Monitor for memory leaks over 24h

---

## 🚀 Going Production

### Pre-Flight Checklist

**Configuration:**
- [x] Bot token configured
- [x] Category B enabled
- [x] Circuit breakers set
- [x] Queue system active
- [ ] Authorized users configured
- [ ] Download directory set
- [ ] Storage quota configured

**Monitoring:**
- [x] Health check script working
- [x] Log viewer functional
- [x] Monitoring dashboard ready
- [ ] Automated backups scheduled
- [ ] Alert system configured

**Testing:**
- [x] Bot responds to /start
- [x] Handlers registered
- [x] Web panel accessible
- [ ] Download tested
- [ ] Upload tested
- [ ] Queue tested

**Security:**
- [ ] Non-root user configured
- [ ] Firewall rules set
- [ ] HTTPS enabled (if public)
- [ ] Rate limiting configured

---

## 🆘 If Something Breaks

### Quick Recovery
```bash
# Check what's wrong
./scripts/quick_check.sh

# Review recent errors
./scripts/view_logs.sh 200 error

# Restart bot
docker restart 9ea93d6c31a9

# Restore from backup
tar -xzf data/backups/mltb_working_state_*.tar.gz -C /
docker restart 9ea93d6c31a9
```

### Disable Category B (Emergency)
```bash
# Edit __main__.py
sed -i 's/ENABLE_CATEGORY_B", True/ENABLE_CATEGORY_B", False/' src/bot/__main__.py

# Deploy and restart
docker cp src/bot/__main__.py 9ea93d6c31a9:/app/src/bot/
docker restart 9ea93d6c31a9
```

---

## 📚 Additional Resources

- **Main Docs:** [docs/](docs/)
- **API Reference:** [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **Commands:** [docs/COMMANDS.md](docs/COMMANDS.md)
- **Monitoring Guide:** [MONITORING.md](MONITORING.md)
- **Deployment Guide:** [docs/PRODUCTION_DEPLOYMENT_GUIDE.md](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)

---

## ✅ Current Status

**Last Updated:** 2026-02-27 22:30 UTC  
**Bot Status:** ✅ Operational  
**Category B:** ✅ Enabled  
**Health:** ✅ All systems green  
**Container:** 9ea93d6c31a9  
**Uptime:** 20+ minutes since last restart  

**Current Metrics:**
- Circuit Breakers: All CLOSED (0 failures)
- CPU: ~1-2% (idle)
- Memory: 495MB / 19GB
- Disk: 78GB / 629GB (13%)

**Next Action:** Test download functionality, then proceed with production checklist.

---

**Need help?** Check logs with `./scripts/view_logs.sh` or run health check with `./scripts/monitor_bot.sh`
