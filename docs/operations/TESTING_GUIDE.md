# 🧪 Testing, Validation & Troubleshooting Guide

Complete guide to verify features work, diagnose problems, and report issues.

---

## 📋 Quick Validation Checklist

Run this **after deployment** to verify everything works:

```bash
# 1. Bot is responsive
Telegram: Send /ping to bot
Expected: "Pong! 🏓"

# 2. Download engine working
Telegram: Send /status
Expected: Shows queue (even if empty)

# 3. Web dashboard
Browser: http://localhost:8060
Expected: Dashboard loads, shows system metrics

# 4. Run automated tests (5 minutes)
Terminal: python -m pytest tests/ -o addopts=""
Expected: All tests pass ✅
```

If all pass → **Your bot is working!** 🎉

---

## 🚀 Phase-by-Phase Testing

### Phase 6: Stream Links & Web Features

#### What It Does
- Stream files via HTTP links
- Web dashboard & API gateway
- Real-time log viewing
- Circuit breaker for reliability
- Auto-update checks

#### Test Commands

```bash
# Test in Telegram:
/streamlink           # Reply to a file with this → get HTTP stream URL

/log                  # Get latest log file

/edash                # Open enhanced web dashboard

/ping                 # Verify bot is running
```

#### Expected Behavior
- `/streamlink`: Returns a URL that works for 24 hours
- `/log`: Sends a .txt file with recent logs (500-1000 lines)
- `/edash`: Shows dashboard statistics, download history, system status
- All commands respond within 5 seconds

#### Validation Script
```bash
# Send these commands in Telegram and verify output:
echo "Testing Phase 6 commands..."
# 1. /ping → Pong!
# 2. /edash → Dashboard loaded with status
# 3. /log → Log file downloaded
# ✅ All working
```

#### If Problems Occur
See [Phase 6 Troubleshooting](#phase-6-troubleshooting) below.

---

### Phase 7: Performance & Reliability Monitoring

#### What It Does
- System health monitoring
- Resource metrics (CPU, RAM, disk)
- Download performance tracking
- Reliability metrics & SLA tracking
- Real-time monitoring dashboard

#### Test Commands

```bash
# Test in Telegram:
/health               # System health summary

/estats               # Extended statistics

/rmon                 # Resource monitoring
```

#### Expected Behavior
- `/health`: Shows uptime, success rate, error count
- `/estats`: Shows download speed, queue depth, cache utilization
- `/rmon`: Shows CPU/RAM/disk usage, temperature if available

#### Validation Script
```bash
# Run in terminal after 2+ minutes uptime:
python -m pytest tests/test_health_monitor.py -v -o addopts=""

# Expected: All health tests pass ✅
```

#### If Problems Occur
See [Phase 7 Troubleshooting](#phase-7-troubleshooting) below.

---

### Phase 8: Advanced Intelligence

#### What It Does
- Metadata extraction and analysis
- Download source classification
- Cross-seed recommendations
- Performance prediction
- Smart caching decisions

#### Test Commands

```bash
# Test in Telegram:
/eanalytics           # Show analytics dashboard

/equick               # Quick overview
```

#### Expected Behavior
- `/eanalytics`: Shows download trends, success rates, performance graphs
- `/equick`: Shows summary of queue, recent completions, system state

#### Validation Script
```bash
# Run tests for Phase 8 features:
python -m pytest tests/test_enhanced_startup_phase5.py -v -o addopts=""

# Expected: All tests pass ✅
```

#### If Problems Occur
See [Phase 8 Troubleshooting](#phase-8-troubleshooting) below.

---

### Phase 9: Enterprise Features

#### What It Does
- Metadata stripping for privacy
- Automatic CAPTCHA solving
- Load balancing across clients
- Cross-seed optimization
- Quota bypass strategies

#### Test Commands

These features are **automatic** in workflows. Enable them in config:

```env
# config/.env.production
ENABLE_METADATA_STRIP=true
ENABLE_CAPTCHA_SOLVER=true
ENABLE_CROSS_SEED=true
ENABLE_QUOTA_BYPASS=true
```

#### Validation Script
```bash
# Run Phase 9 integration tests:
python -m pytest tests/test_phase9_enterprise_features.py -v -o addopts=""

# Expected: All tests pass ✅
```

#### How to Verify It's Working
Check logs for Phase 9 operations:

```bash
# After running a download:
tail -n 500 data/logs/log.txt | grep -i "metadata\|captcha\|quota\|cross"
```

You should see entries like:
```
[INFO] Metadata stripping completed
[INFO] CAPTCHA solved successfully
[INFO] Cross-seed enabled for torrent
[INFO] Quota bypass strategy applied
```

#### If Problems Occur
See [Phase 9 Troubleshooting](#phase-9-troubleshooting) below.

---

### Phase 10: Ecosystem Integrations

#### What It Does
- Index generation (HTML index of downloads)
- Batch operations (process multiple links)
- Link bypassers (resolve shortened/ad URLs)
- Debrid integrations (Real-Debrid, AllDebrid, Premiumize)

#### Configuration

```env
# config/.env.production
DEBRID_CLIENTS=real-debrid,alldebrid    # Enable integrations
REAL_DEBRID_API_KEY=your_key_here
ALLDEBRID_API_KEY=your_key_here
PREMIUMIZE_API_KEY=your_key_here
```

#### Validation Script

Run the Phase 10 integration test suite:

```bash
python -m pytest tests/test_phase10_ecosystem_integrations.py -v -o addopts=""

# Expected output:
# test_index_generation PASSED              [16.67%]
# test_batch_operations PASSED              [33.33%]
# test_link_bypassing PASSED                [50.00%]
# test_debrid_integration PASSED            [66.67%]
# test_error_handling PASSED                [83.33%]
# test_edge_cases PASSED                    [100%]
# 
# ======================== 6 passed in 2.45s ========================
```

#### How to Verify Features Working

**Index Generation:**
```bash
# Check for generated indices:
ls -la data/indices/
# Should contain .html files with download listings
```

**Link Bypassers:**
```bash
# In logs, look for:
grep "Bypasser" data/logs/log.txt

# Example:
[INFO] ShortenerBypasser: Resolved bit.ly/abc123 → actual-download-url
[INFO] AdBypasser: Stripped 4 ad redirects from chain
```

**Debrid Integration:**
```bash
# Check if debrid was used:
grep "Debrid\|Real-Debrid\|AllDebrid" data/logs/log.txt

# Example:
[INFO] Real-Debrid: Magnet hashed and cached
[INFO] AllDebrid: 2 links resolved in 1.23s
```

#### If Problems Occur
See [Phase 10 Troubleshooting](#phase-10-troubleshooting) below.

---

### Phase 11: Optimization & Scaling

#### What It Does
- Zero-copy transfers (efficient file moves)
- MTProto parallel uploading (faster Telegram uploads)
- Google Drive batch operations
- Recursive archive extraction
- Salvage mode (recover corrupted files)

#### Validation Script

Run the Phase 11 optimization test suite:

```bash
python -m pytest tests/test_phase11_optimization_scaling.py -v -o addopts=""

# Expected output:
# test_zero_copy_transfer PASSED            [16.67%]
# test_mtproto_parallel_upload PASSED       [33.33%]
# test_gdrive_batch_operations PASSED       [50.00%]
# test_recursive_extraction PASSED          [66.67%]
# test_salvage_mode PASSED                  [83.33%]
# test_error_recovery PASSED                [100%]
#
# ======================== 6 passed in 2.26s ========================
```

#### How to Verify Features Working

**Zero-Copy Transfer:**
```bash
# Check logs for zero-copy operations:
grep "zero-copy\|sendfile" data/logs/log.txt

# Example:
[INFO] Zero-Copy: Transferred file.iso (1.2 GB) via os.sendfile
```

**MTProto Parallel Upload:**
```bash
# Monitor a Telegram upload:
grep "MTProto\|parallel" data/logs/log.txt

# Example:
[INFO] MTProto: Uploading 4 chunks in parallel
[INFO] MTProto: Chunk 1/4 (256 MB) ✓
[INFO] MTProto: Upload completed: 1.5 GB in 45s
```

**Batch Operations:**
```bash
# Check for batch operation logs:
grep "batch\|Batch" data/logs/log.txt

# Example:
[INFO] Batch: Processing 15 Google Drive copies
[INFO] Batch: 15/15 completed in 23s
```

**Recursive Extraction:**
```bash
# Look for archive extraction logs:
grep "extract\|recursive" data/logs/log.txt

# Example:
[INFO] Recursive: Extracting archive.zip (depth=2)
[INFO] Recursive: Found nested archive.tar.gz
[INFO] Recursive: Extraction complete, 145 files extracted
```

**Salvage Mode:**
```bash
# Check for salvage operations:
grep -i "salvage\|recover\|corruption" data/logs/log.txt

# Example:
[INFO] Salvage: Detected 3 corrupted chunks in file.rar
[INFO] Salvage: Recovered 98% of data
```

#### If Problems Occur
See [Phase 11 Troubleshooting](#phase-11-troubleshooting) below.

---

## 🔍 Troubleshooting by Symptom

### General Issues

#### Bot Not Responding

**Symptom:** Send `/ping` → no response for 30+ seconds

**Quick Fix:**
```bash
# Check if bot is running
docker compose ps
# Should show: app   RUNNING

# Check logs
docker compose logs app --tail=50

# Restart
docker compose restart app
```

**If Still Broken:**
```bash
# Check Python errors
docker compose logs app | grep -i "error\|exception\|traceback"

# Check database connection
docker compose logs mongo

# Check Redis
docker compose logs redis
```

**Report It:** See [Reporting Issues](#reporting-issues) section.

---

#### Dashboard Not Loading (Port 8060)

**Symptom:** http://localhost:8060 shows "Connection refused"

**Quick Fix:**
```bash
# Check if service is running
docker compose ps web

# Should show: web   RUNNING

# If not running, restart:
docker compose restart web

# Check port is open
netstat -tlnp | grep 8060
```

**If Still Broken:**
```bash
# Check for port conflicts
sudo lsof -i :8060

# If occupied, kill process:
sudo kill -9 <PID>

# Restart bot
docker compose restart web
```

---

#### Download Stuck/Not Starting

**Symptom:** `/status` shows task "Downloading..." but no progress

**Quick Fix:**
```bash
# Check download client status
curl http://localhost:6800/jsonrpc  # Aria2
# or
curl http://localhost:8090          # qBittorrent

# Verify files are being written
ls -lh data/downloads/ | head -20

# Check if disk is full
df -h data/downloads/
```

**If Still Broken:**
```bash
# Restart download clients
docker compose restart aria2c qbittorrent

# Clear stuck tasks
docker compose exec app python -m bot --reset-cache

# Try small download
# Send: /leech https://example.com/small-file.txt
```

---

### Phase 6 Troubleshooting

#### `/streamlink` Returns Error

**Check Configuration:**
```bash
# Verify STREAM_BASE_URL is set
grep STREAM_BASE_URL config/.env.production

# Should output:
# STREAM_BASE_URL=http://your-server:8060/stream
```

**Check Logs:**
```bash
docker compose logs app | grep -i streamlink
```

**Expected:** `[INFO] Stream link generated for file.mp4`

---

#### `/log` Not Sending Log File

**Check Logs Directory:**
```bash
ls -la data/logs/
# Should contain: log.txt (recent log)

# Check file size
ls -lh data/logs/log.txt
```

**Check Permissions:**
```bash
# Logs should be readable
docker compose exec app python -c "
import os
path = 'data/logs/log.txt'
print(f'Exists: {os.path.exists(path)}')
print(f'Readable: {os.access(path, os.R_OK)}')
"
```

---

### Phase 7 Troubleshooting

#### `/health` Shows "Unknown" or "Offline"

**Check Uptime:**
```bash
docker compose logs app | grep "Bot started\|initialized"
# Bot needs 2+ minutes before health is accurate
```

**Check System Resources:**
```bash
# Verify no resource exhaustion
free -h          # RAM usage
df -h           # Disk usage
top -bn1 | head  # CPU usage
```

**If High Usage:**
```bash
# Restart and monitor
docker compose restart app
docker compose stats

# If memory grows unbounded → memory leak likely
# Check code for: while True loops without breaks,
# unclosed file handles, or growing lists
```

---

#### `/estats` Missing Metrics

**Common Cause:** Insufficient uptime or no completed downloads

**Fix:**
1. Let bot run for 5+ minutes
2. Complete at least one download
3. Try `/estats` again

---

### Phase 8 Troubleshooting

#### `/eanalytics` Returns Empty Data

**Check Uptime:**
Analytics need 10+ minutes and multiple downloads to populate

**Verify Database:**
```bash
docker compose exec mongo mongosh --eval "
  db.downloads.countDocuments()
"
# Should show: >0 downloads recorded
```

**If Empty:**
```bash
# Can't analyze empty database
# Complete a test download first:
# /leech https://example.com/file.txt
# Wait for completion → try /eanalytics again
```

---

### Phase 9 Troubleshooting

#### CAPTCHA Solver Not Working

**Check Configuration:**
```bash
grep CAPTCHA config/.env.production
# Should show: CAPTCHA_SOLVER=true
```

**Check Solver Service:**
```bash
# Verify external captcha service is running
curl https://your-captcha-api/status

# If failing → disable or use alternative
# Set: CAPTCHA_SOLVER=false
```

**Check Logs:**
```bash
docker compose logs app | grep -i captcha
# Should show: [INFO] CAPTCHA solved successfully
```

---

#### Metadata Stripping Not Active

**Check Configuration:**
```bash
grep ENABLE_METADATA_STRIP config/.env.production
# Must be: ENABLE_METADATA_STRIP=true
```

**Verify in Logs:**
```bash
# After a download:
docker compose logs app | grep -i "metadata"
# Should show: [INFO] Metadata stripping completed
```

---

### Phase 10 Troubleshooting

#### Debrid Integration Not Working

**Check API Keys:**
```bash
grep "API_KEY\|DEBRID" config/.env.production

# Should have:
# REAL_DEBRID_API_KEY=valid_key
# ALLDEBRID_API_KEY=valid_key
```

**Test Connection:**
```bash
docker compose exec app python -c "
from bot.core.debrid_manager import DebridManager, RealDebridClient
client = RealDebridClient('YOUR_API_KEY')
print(client.test_connection())  # Should print: True
"
```

**If Connection Fails:**
```bash
# Check API key validity
# Get fresh key from: https://real-debrid.com/account
# Update config and restart

docker compose restart app
```

---

#### Link Bypasser Not Resolving URLs

**Check Logs:**
```bash
docker compose logs app | grep -i "bypasser\|resolve"
```

**Test Manually:**
```bash
docker compose exec app python -c "
from bot.core.link_bypassers import LinkBypassEngine
engine = LinkBypassEngine()

# Test with a real shortened URL
url = 'https://bit.ly/example'
resolved = engine.bypass_url(url)
print(f'Original: {url}')
print(f'Resolved: {resolved}')
"
```

---

### Phase 11 Troubleshooting

#### Zero-Copy Transfer Failing on Some Files

**Symptom:** Large files transfer slowly, or `os.sendfile` errors in logs

**Root Cause:** Some filesystems don't support `os.sendfile` (e.g., network mounts)

**Fix:**
Zero-copy module automatically falls back to socket.send() on error.
Check logs for:
```bash
docker compose logs app | grep -i "sendfile\|fallback"
# Expected: [INFO] Zero-Copy: Using fallback socket.send() for file.iso
```

**If Always Failing:**
File system issue. Run filesystem check:
```bash
# On host machine (not in Docker)
sudo fsck -n /data/downloads
```

---

#### MTProto Parallel Upload Very Slow

**Symptom:** Upload to Telegram takes longer than expected

**Check Configuration:**
```bash
grep "TELETHON_WORKERS\|PARALLEL_CHUNKS" config/.env.production
```

**Increase Parallelism:**
```env
# config/.env.production
TELETHON_WORKERS=4        # Default: 1
PARALLEL_CHUNKS=8         # Default: 4
```

**Restart:**
```bash
docker compose restart app
```

**Monitor Performance:**
```bash
# During upload:
docker compose logs app | grep -i "mtproto\|chunk"
# Should show multiple chunks in progress
```

---

#### Recursive Extraction Going Infinite

**Symptom:** Extraction never completes or fills disk

**Check Depth Limit:**
```bash
grep "EXTRACT_MAX_DEPTH" config/.env.production
# Should be: EXTRACT_MAX_DEPTH=3 or similar (not too high)
```

**Kill Stuck Process:**
```bash
# Find the extraction process
ps aux | grep -i extract

# Kill it
kill -9 <PID>

# Reduce max depth in config
# EXTRACT_MAX_DEPTH=2
# Restart bot

docker compose restart app
```

---

#### Salvage Mode Not Recovering Files

**Symptom:** Corrupted file remains corrupted after salvage attempt

**Root Cause:** File too damaged or salvage not triggered automatically

**Manual Trigger:**
```bash
docker compose exec app python -c "
from bot.core.salvage_mode import SalvageMode

salvage = SalvageMode(
    file_path='data/downloads/corrupted.rar',
    skip_bad_blocks=True
)
result = salvage.recover()
print(f'Recovery successful: {result.recovered}')
print(f'Data recovered: {result.bytes_recovered / 1e9:.2f} GB')
"
```

---

## ✅ Validation Checklist By Role

### For Users / Bot Operators

**Before putting bot in production:**

- [ ] `/ping` works
- [ ] `/status` shows queue
- [ ] Web dashboard loads (http://localhost:8060)
- [ ] Can send files to bot via `/leech`
- [ ] Can start a download from URL via `/mirror`
- [ ] `/health` shows healthy status
- [ ] `/log` can fetch logs
- [ ] Received notifications for download completion
- [ ] `/help` shows all commands
- [ ] `/cmdlist` returns command list + file

**When deploying to production:**

- [ ] Run full test suite: `python -m pytest tests/ -o addopts=""`
- [ ] All tests pass (expected: ~35 tests across all phases)
- [ ] No warnings or deprecations in test output
- [ ] Database is backed up: `docker compose exec mongo mongodump`
- [ ] Logs are being written: `ls -la data/logs/`
- [ ] Authorized users can command bot
- [ ] Unauthorized users get "Access Denied"
- [ ] Download clients are functional (aria2, qBittorrent, etc.)
- [ ] Storage has adequate space (`df -h data/downloads/`)

---

### For System Administrators

**Before production deployment:**

- [ ] All docker compose services running: `docker compose ps`
- [ ] No resource exhaustion: `docker compose stats`
- [ ] Ports are firewalled properly (only 8060, 8090 exposed)
- [ ] SSL certificates valid (if using https)
- [ ] MongoDB backup job is scheduled
- [ ] Log rotation is configured
- [ ] Monitoring is in place (memory, disk, CPU)
- [ ] Database replication is working (if multi-instance)
- [ ] Redis is configured for caching
- [ ] Run health check script: `bash scripts/health_check.sh`

**Daily operations:**

- [ ] Check logs daily for errors: `tail -n 100 data/logs/log.txt`
- [ ] Monitor disk space: `df -h data/downloads/`
- [ ] Verify no hung processes: `docker compose ps`
- [ ] Check bot responsiveness: `/ping`
- [ ] Review failed downloads: `grep ERROR data/logs/log.txt`

---

### For Developers

**Before pushing code:**

- [ ] All tests pass locally: `python -m pytest tests/ -o addopts=""`
- [ ] No lint errors: `flake8 bot/ --max-line-length=120`
- [ ] Type hints present: `mypy bot/ --ignore-missing-imports`
- [ ] Docstrings added to new functions
- [ ] Log statements use appropriate levels (DEBUG/INFO/WARNING/ERROR)
- [ ] No sensitive data in logs
- [ ] Code follows project style (see [DEVELOPMENT_JOURNEY.md](docs/DEVELOPMENT_JOURNEY.md))

---

## 📞 Reporting Issues

### How to Get Help

**Before reporting, check:**

1. [ ] Is the bot actually running? `docker compose ps`
2. [ ] Are all services healthy? `docker compose logs`
3. [ ] Is there disk space? `df -h data/`
4. [ ] Have you restarted? `docker compose restart app`
5. [ ] Are all tests passing? `python -m pytest tests/ -o addopts=""`

---

### Gathering Debug Information

When you have an issue, collect this info:

```bash
#!/bin/bash
# Debug Info Collector

echo "=== Environment ==="
cat config/.env.production | grep -v "KEY\|TOKEN" | head -20

echo -e "\n=== Service Status ==="
docker compose ps

echo -e "\n=== Resource Usage ==="
docker compose stats --no-stream

echo -e "\n=== Recent Errors (last 100 lines) ==="
docker compose logs app --tail=100 | grep -i "error\|exception\|traceback"

echo -e "\n=== Test Results ==="
python -m pytest tests/ -q -o addopts="" 2>&1 | tail -20

echo -e "\n=== Disk Usage ==="
du -sh data/*
df -h data/

echo -e "\n=== Bot Version ==="
git log --oneline -n 5
```

Run this and **save the output to a file**.

---

### Creating a GitHub Issue

1. Go to [GitHub Issues](https://github.com/adirane45/mirror-leech-telegram-bot/issues)
2. Click "New Issue"
3. Fill in:

```markdown
## Title
[Brief description of issue]

## Environment
- OS: Ubuntu 22.04 (or your OS)
- Docker: version X.XX
- Python: 3.13
- Bot version: (run `git log --oneline -n 1`)

## Steps to Reproduce
1. Send `/command`
2. Expected: [what should happen]
3. Actual: [what actually happened]

## Error Output
[Paste error from logs, test suite, or terminal]

## Debug Info
[Paste output from debug script above]

## Relevant Files
- config/.env.production (with secrets removed)
- data/logs/log.txt (last 50 lines with error)
```

---

### Where to Report

| Issue Type | Report To |
|----------|-----------|
| **Bug in code** | [GitHub Issues](https://github.com/adirane45/mirror-leech-telegram-bot/issues) |
| **Feature request** | [GitHub Discussions](https://github.com/adirane45/mirror-leech-telegram-bot/discussions) |
| **Security issue** | Email: (see [SECURITY.md](docs/LICENSE) if exists) |
| **Question / How-to** | GitHub Discussions / Wiki |
| **Performance issue** | GitHub Issues with perf data |

---

## 🧩 Running Specific Tests

### Run All Tests

```bash
python -m pytest tests/ -v -o addopts=""
# -v for verbose output
# -o addopts="" to ignore pytest warnings
```

### Run Specific Phase Tests

```bash
# Phase 6
python -m pytest tests/test_enhanced_startup.py -v

# Phase 7
python -m pytest tests/test_health_monitor.py tests/test_metrics.py -v

# Phase 8
python -m pytest tests/test_enhanced_startup_phase5.py -v

# Phase 9
python -m pytest tests/test_phase9_enterprise_features.py -v

# Phase 10
python -m pytest tests/test_phase10_ecosystem_integrations.py -v

# Phase 11
python -m pytest tests/test_phase11_optimization_scaling.py -v
```

### Run Single Test

```bash
python -m pytest tests/test_phase10_ecosystem_integrations.py::test_index_generation -v
```

### Run with Coverage

```bash
pip install pytest-cov
python -m pytest tests/ --cov=bot --cov-report=html
open htmlcov/index.html
```

---

## 🔄 Common Recovery Procedures

### Recovery From Database Corruption

```bash
# 1. Stop bot
docker compose down

# 2. Backup current database
docker compose exec mongo mongodump --out /data/backup/

# 3. Drop database
docker compose exec mongo mongosh --eval "db.dropDatabase()"

# 4. Restore from backup
docker compose up -d mongo
sleep 10
docker compose exec mongo mongorestore /data/backup/

# 5. Restart bot
docker compose up -d app
```

### Recovery From Full Disk

```bash
# 1. Free space
docker container prune -f        # Remove stopped containers
docker image prune -a -f         # Remove unused images
docker volume prune -f           # Remove unused volumes

# 2. Clean old logs
find data/logs/ -mtime +30 -delete  # Delete logs older than 30 days

# 3. Clean old downloads (CAUTION: deletes downloads older than 7 days)
find data/downloads/ -mtime +7 -delete

# 4. Rebuild cache
docker compose exec app python -c "
from bot.core.advanced_cache import CacheManager
cache = CacheManager()
cache.rebuild()
print('Cache rebuilt')
"
```

### Recovery From Memory Leak

```bash
# 1. Identify if memory leak exists
watch -n 2 'docker stats app --no-stream | grep memory'

# 2. If memory grows unbounded:
# - Check logs for patterns
grep -i "while.*True\|for.*infinite" bot/**/*.py

# 3. Restart app (will free memory)
docker compose restart app

# 4. If recurs, file a bug with:
docker compose logs app > /tmp/bot_memleak.log
# Attach to GitHub issue
```

---

## 📊 Performance Benchmarking

### Baseline Configuration

```bash
# Establish baseline before changes:
python scripts/setup_performance_baseline.sh

# This:
# - Records system specs
# - Runs sample downloads
# - Measures speeds
# - Saves results to: data/logs/baseline.txt
```

### Benchmark Specific Operations

```bash
# Zero-copy transfer speed
time python -c "
from bot.core.zero_copy_uploader import ZeroCopyUploader
uploader = ZeroCopyUploader()
uploader.transfer_file('test_1gb.iso', 'destination/')
"

# MTProto upload speed
time python -c "
from bot.core.mtproto_parallel_uploader import MTProtoParallelUploader
uploader = MTProtoParallelUploader()
uploader.upload_to_telegram('test_file.mp4')
"
```

---

## 🎯 Success Criteria

Your bot is **production-ready** when:

✅ All 35+ tests pass  
✅ `/ping` responds in <2 seconds  
✅ `/status` shows current queue  
✅ Completed download appears in designated location  
✅ Web dashboard loads without errors  
✅ Logs are being written and rotated  
✅ No warnings in docker compose logs  
✅ Resource usage is stable (no memory growth)  
✅ Response time <5 seconds for all commands  
✅ All authorized users can command the bot  

---

## 📚 Additional Resources

- **Full Documentation**: [docs/](docs/)
- **Configuration Reference**: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
- **Command Reference**: [docs/COMMANDS.md](docs/COMMANDS.md)
- **Deployment Guide**: [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)
- **Development Guide**: [docs/DEVELOPMENT_JOURNEY.md](docs/DEVELOPMENT_JOURNEY.md)
- **API Reference**: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)

---

<div align="center">

**Need More Help?**

📖 [Read Docs](docs/) • 🐛 [Report Issue](https://github.com/adirane45/mirror-leech-telegram-bot/issues) • 💬 [Ask Community](https://github.com/adirane45/mirror-leech-telegram-bot/discussions)

Still stuck? Follow the [Reporting Issues](#reporting-issues) guide above.

</div>
