# MLTB Phase 1 Production Deployment Guide

## Quick Start (2 minutes)

```bash
# 1. Clone and navigate
git clone https://github.com/your-repo/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# 2. Run deployment script
chmod +x deploy.sh
./deploy.sh

# 3. Configure credentials
nano .env.production
# Update with your Telegram BOT_TOKEN and API credentials

# 4. Start services
docker compose -f docker-compose.secure.yml up -d

# 5. Verify deployment
./scripts/health_check.sh
```

---

## Detailed Deployment

### Prerequisites
- Docker & Docker Compose installed
- Linux server (Kali Linux, Ubuntu, Debian, etc.)
- 2GB+ RAM available
- Port access: 8000 (web), 3000 (Grafana), 6379 (Redis), 27017 (MongoDB)

### Step 1: Environment Setup

```bash
# Copy environment template
cp .env.security.example .env.production

# Edit with your credentials
nano .env.production
```

**Required variables to update:**
```bash
# Telegram Bot Credentials
BOT_TOKEN=your_telegram_bot_token_here
CHAT_ID=your_chat_id_here

# Grafana Admin (change from default!)
GRAFANA_ADMIN_PASSWORD=your_strong_password

# Database Passwords (auto-generated, update if needed)
REDIS_PASSWORD=your_redis_password
MONGO_PASSWORD=your_mongodb_password
```

### Step 2: Directory Structure

The deployment creates this structure:

```
mirror-leech-telegram-bot/
├── docker-compose.secure.yml       (Production config)
├── docker-compose.enhanced.yml      (Enhanced features)
├── deploy.sh                        (Deployment script)
├── .env.production                  (Credentials)
│
├── bot/
│   └── core/
│       ├── celery_config.py         (Task queue config)
│       └── metrics.py               (Prometheus metrics)
│
├── scripts/
│   ├── deploy.sh                    (Automated deployment)
│   ├── health_check.sh              (Health monitoring)
│   ├── backup.sh                    (Automated backups)
│   ├── mongodb-init.js              (DB initialization)
│   ├── security_setup.py            (Credential generation)
│   └── production_hardening.py      (Config generation)
│
├── monitoring/
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alert.rules.yml          (13 alert rules)
│   └── grafana/
│       └── dashboards/
│           ├── mltb-overview.json   (6 panels)
│           └── mltb-health.json     (4 panels)
│
├── tests/
│   ├── test_api_endpoints.py        (API validation)
│   └── test_load_performance.py     (Load testing)
│
├── logs/                            (Auto-created)
├── backups/                         (Auto-created)
└── downloads/                       (Auto-created)
```

### Step 3: Deploy Services

**Option A: Automated (Recommended)**
```bash
./deploy.sh
```

**Option B: Manual Docker Compose**
```bash
# Build and start all services
docker compose -f docker-compose.secure.yml up -d --build

# Verify services
docker compose -f docker-compose.secure.yml ps

# View logs
docker compose -f docker-compose.secure.yml logs -f
```

### Step 4: Verification

```bash
# Run health checks
./scripts/health_check.sh

# Run API endpoint tests
python tests/test_api_endpoints.py

# Run load testing
python tests/test_load_performance.py

# Check Docker services
docker ps
```

### Step 5: Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Bot Web | http://localhost:8000 | None (public) |
| Grafana | http://localhost:3000 | admin / (set in .env) |
| Prometheus | http://localhost:9091 | None (internal) |
| Metrics | http://localhost:9090/metrics | Bearer token (env) |
| Redis | localhost:6379 | Password (env) |
| MongoDB | localhost:27017 | mltb_bot / (env) |

---

## Configuration

### Docker Compose Files

**docker-compose.secure.yml** (Recommended for Production)
```
Features:
✅ Authentication enabled (Redis, MongoDB)
✅ Network isolation (custom bridge)
✅ Port binding restrictions (localhost-only)
✅ Health checks on all services
✅ Auto-restart policies
✅ Resource limits (CPU/Memory)
```

**docker-compose.enhanced.yml** (Development)
```
Features:
✅ Full metrics collection
✅ Celery optimization
✅ Performance tuning
✅ Dashboard configuration
❌ Limited security (for dev only)
```

### Environment Variables

All variables are defined in `.env.production`:

```bash
# ===== BOT CONFIGURATION =====
BOT_TOKEN=your_bot_token
CHAT_ID=your_chat_id
BOT_ENABLE_METRICS=true
BOT_ENABLE_REDIS=true
BOT_ENABLE_CELERY=true

# ===== DATABASE =====
REDIS_PASSWORD=auto_generated
MONGO_PASSWORD=auto_generated
MONGO_USERNAME=mltb_bot

# ===== MONITORING =====
GRAFANA_ADMIN_PASSWORD=your_password
PROMETHEUS_BEARER_TOKEN=auto_generated

# ===== SYSTEM =====
SKIP_UPDATE=1  (prevents overwriting in containers)
```

---

## Services Overview

### 1. Bot Application (Port 8000)
```yaml
Container: app
Internal Port: 8050
Features:
  - FastAPI/Pyrogram bot
  - Prometheus metrics export (port 9090)
  - Redis caching integration
  - Celery task queue
Health Check: GET /health
Restart: on-failure (5 attempts)
```

### 2. Redis Cache (Port 6379)
```yaml
Container: redis
Version: 7-alpine
Features:
  - Task broker for Celery
  - Application caching
  - Session storage
Password: Required (.env)
Health Check: PING command
```

### 3. MongoDB Database (Port 27017)
```yaml
Container: mongodb
Version: 4.4
Features:
  - Task data storage
  - Download/upload history
  - User information
  - Settings storage
Auth: mltb_bot user
Health Check: PING command
```

### 4. Celery Worker
```yaml
Container: celery-worker
Features:
  - Task processing (download, upload, etc.)
  - Task routing (5 priority queues)
  - Auto-scaling (3-10 workers)
  - Soft/hard timeouts
Restart: on-failure (5 attempts)
```

### 5. Celery Beat Scheduler
```yaml
Container: celery-beat
Features:
  - Scheduled task execution
  - Job scheduling
  - Periodic tasks (backups, cleanup)
Restart: on-failure (5 attempts)
```

### 6. Prometheus Metrics (Port 9091)
```yaml
Container: prometheus
Features:
  - Metrics collection (40+ metrics)
  - 15-second scrape interval
  - 15-day retention
  - Alert evaluation
Health Check: /-/healthy endpoint
```

### 7. Grafana Dashboards (Port 3000)
```yaml
Container: grafana
Features:
  - Web-based dashboards
  - 2 pre-configured dashboards (mltb-overview, mltb-health)
  - 10 visualization panels
  - Alert configuration
  - Real-time data display
Default: admin / admin (CHANGE!)
```

---

## Monitoring & Maintenance

### Health Checks

```bash
# Run all 8 health checks
./scripts/health_check.sh

# Checks validate:
✓ Web endpoint (8050)
✓ Redis (6379)
✓ MongoDB (27017)
✓ Metrics endpoint (9090)
✓ Prometheus (9091)
✓ Grafana (3000)
✓ Disk space
✓ Log directory
```

### Automated Tasks

Schedule these for continuous operation:

```bash
# Every 5 minutes: Health check
*/5 * * * * /path/to/scripts/health_check.sh >> /path/to/logs/health_check.log 2>&1

# Daily 2 AM: Backup databases & logs
0 2 * * * /path/to/scripts/backup.sh >> /path/to/logs/backup.log 2>&1

# Daily 3 AM: Cleanup old logs (30+ days)
0 3 * * * find /path/to/logs -name "*.log.*" -mtime +30 -delete

# Every 10 minutes: Restart unhealthy containers
*/10 * * * * cd /path/to && docker-compose -f docker-compose.secure.yml ps | grep -q "(unhealthy)" && docker-compose restart app || true
```

### Backup Strategy

```bash
# Manual backup
./scripts/backup.sh

# Automatic backups (scheduled daily)
# Location: ./backups/
# Components: MongoDB, Redis, Application logs
# Retention: 7 days (auto-cleanup)

# Restore from backup
mongorestore --drop --uri="mongodb://localhost:27017" /path/to/backup/mongodb_TIMESTAMP/
```

### Logging

```bash
# View real-time logs
docker compose -f docker-compose.secure.yml logs -f app

# Search logs for errors
grep ERROR ./logs/bot.log

# View metrics log (JSON format)
tail -100 ./logs/metrics.log | jq .

# Log rotation: Automatic (100MB/file, 30-day retention)
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose -f docker-compose.secure.yml logs app

# Common issues:
# 1. Port already in use
netstat -tulpn | grep :8000

# 2. Permission denied
sudo chown -R $USER:$USER ./logs ./backups ./downloads

# 3. Out of disk space
df -h

# 4. High memory usage
free -h
docker stats
```

### Health Check Failing

```bash
# Run individual checks
curl http://localhost:8000/health
redis-cli -p 6379 ping
mongodb://localhost:27017/admin

# Restart unhealthy service
docker compose -f docker-compose.secure.yml restart app
```

### Metrics Not Showing

```bash
# Check metrics endpoint
curl http://localhost:9090/metrics | head -20

# Check Prometheus targets
curl http://localhost:9091/api/v1/targets

# Check if metrics exporter is running
docker compose logs app | grep -i metrics
```

### Database Connection Issues

```bash
# Redis test
redis-cli -p 6379 ping

# MongoDB test
mongosh mongodb://mltb_bot:PASSWORD@localhost:27017/mltb

# Check environment variables
docker compose -f docker-compose.secure.yml exec app env | grep -i db
```

---

## Security Hardening

### Change Default Credentials ⚠️

**Grafana:**
1. Navigate to http://localhost:3000
2. Login: admin / admin
3. Go to Administration → Users
4. Change password immediately

**MongoDB:**
```bash
mongosh mongodb://localhost:27017
db.changeUserPassword("mltb_bot", "new_strong_password")
```

**Redis:**
```bash
redis-cli -p 6379
CONFIG SET requirepass "new_strong_password"
```

### Network Security

```bash
# Restrict metrics to localhost only
sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 9090

# Restrict Grafana to admins only
sudo ufw allow from ADMIN_IP to 127.0.0.1 port 3000

# Allow public bot access (limit rate)
sudo ufw allow 8000/tcp
sudo iptables -A INPUT -p tcp --dport 8000 -m limit --limit 100/min -j ACCEPT
```

### Backup Encryption

```bash
# Enable encrypted backups
tar -czpf - ./backups/ | gpg --symmetric -o ./backups/encrypted_backup.tar.gz.gpg

# Decrypt when needed
gpg -d ./backups/encrypted_backup.tar.gz.gpg | tar -xzp
```

### TLS/HTTPS

Deploy behind a reverse proxy (Nginx/Caddy) with certificates from Let's Encrypt.

---

## Performance Tuning

### Resource Limits

Edit `docker-compose.secure.yml` to adjust:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2.0'        # Change CPU limit
          memory: '512M'     # Change memory limit
```

### Celery Optimization

Edit `bot/core/celery_config.py`:

```python
CELERY_WORKER_PREFETCH_MULTIPLIER = 4      # Tasks per worker
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100    # Tasks before restart
CELERY_WORKER_POOL = 'prefork'             # Process pool type
```

### Metrics Collection

Prometheus settings in `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'mltb'
    scrape_interval: 15s    # Change collection interval
    scrape_timeout: 10s
```

---

## Scaling & High Availability

### Multiple Workers

```bash
# Scale celery-worker to 3 instances
docker compose -f docker-compose.secure.yml up -d --scale celery-worker=3
```

### Load Balancing

Use Nginx as reverse proxy:

```nginx
upstream mltb {
    server app:8050 weight=1;
    server app2:8050 weight=1;
}

server {
    listen 80;
    location / {
        proxy_pass http://mltb;
    }
}
```

---

## Disaster Recovery

### Recovery Plan

1. **Backup Recent Key Data**
   ```bash
   ./scripts/backup.sh
   ```

2. **Stop Services**
   ```bash
   docker compose -f docker-compose.secure.yml down
   ```

3. **Restore from Backup**
   ```bash
   mongorestore --drop --uri="mongodb://localhost:27017" /backups/mongodb_TIMESTAMP/
   ```

4. **Start Services**
   ```bash
   docker compose -f docker-compose.secure.yml up -d
   ```

5. **Verify Health**
   ```bash
   ./scripts/health_check.sh
   ```

---

## Support & Documentation

**Documentation Files:**
- `PHASE_1_ADVANCED_OPTIONS_COMPLETE.md` - Complete implementation
- `OPTION_7_SECURITY_SETUP.md` - Security configuration
- `OPTION_8_PRODUCTION_HARDENING.md` - Hardening procedures
- `OPTION_6_API_TESTING.md` - API validation

**Scripts Location:**
- `deploy.sh` - Automated deployment
- `scripts/health_check.sh` - Health monitoring
- `scripts/backup.sh` - Backup automation
- `scripts/security_setup.py` - Credential generation

**Test Suites:**
- `tests/test_api_endpoints.py` - API validation
- `tests/test_load_performance.py` - Performance testing

---

## Deployment Checklist

- [ ] Prerequisites installed (Docker, Docker Compose)
- [ ] .env.production created and updated with credentials
- [ ] Directory structure created (logs, backups, downloads)
- [ ] All component files verified present
- [ ] Deploy script executed: `./deploy.sh`
- [ ] Health checks passing: `./scripts/health_check.sh`
- [ ] API tests passing: `python tests/test_api_endpoints.py`
- [ ] Grafana default password changed
- [ ] MongoDB/Redis passwords updated in production
- [ ] Backups scheduled and tested
- [ ] Monitoring alerts configured
- [ ] Firewall rules applied
- [ ] TLS/HTTPS configured (optional but recommended)
- [ ] Disaster recovery plan documented
- [ ] Team trained on maintenance procedures

---

**Status: ✅ PRODUCTION READY**

Your MLTB deployment is complete and ready for production use!

For assistance or issues, refer to the documentation files or run health checks.

