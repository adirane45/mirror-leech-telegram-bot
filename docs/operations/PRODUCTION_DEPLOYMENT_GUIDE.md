# 🚀 Production Deployment Guide

**Status**: Before deploying to any VPS, complete this checklist

---

## ⚠️ CRITICAL - Security Hardening

### 1. **REMOVE EXPOSED CREDENTIALS**
```bash
# ❌ NEVER commit credentials to git
# Your current .env.production has:
# - BOT_TOKEN=7535236556:AAG-R4Ezs1_Px140VaxETF-y1oVPNNFJBog (EXPOSED!)
# - TELEGRAM_API=28965815
# - TELEGRAM_HASH=9baee82bd0eeeaa34ed185ce32128cc4

# ✅ ACTION REQUIRED:
# 1. Rotate your BOT_TOKEN immediately at @BotFather
# 2. Create a new Telegram app to get new API/HASH
# 3. Never add .env.production to git again
```

### 2. **Add .env.production to .gitignore**
```bash
# Edit .gitignore
echo "config/.env.production" >> .gitignore
echo "config/.env.*.example" >> .gitignore

# Remove any .env files from git history
git rm --cached config/.env.production
git commit -m "Remove exposed credentials from git history"
```

### 3. **Create .env.example Template** (TEMPLATE ONLY - NO REAL VALUES)
```bash
# Create config/.env.production.example
cat > config/.env.production.example << 'EOF'
# ===============================================
# TELEGRAM BOT CONFIGURATION
# ===============================================
# Get BOT_TOKEN from @BotFather on Telegram
BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# Get these from https://my.telegram.org/apps
TELEGRAM_API=YOUR_API_ID
TELEGRAM_HASH=YOUR_API_HASH

# Your Telegram user ID (get from @userinfobot)
OWNER_ID=YOUR_USER_ID

# Space-separated list of authorized user/group IDs
AUTHORIZED_CHATS=

# ===============================================
# SECURITY
# ===============================================
# Generate a 32-character random string: openssl rand -hex 16
REDIS_PASSWORD=YOUR_SECURE_REDIS_PASSWORD

# ===============================================
# DATABASE
# ===============================================
DATABASE_URL=mongodb://mltb-mongodb:27017/
DATABASE_ENCRYPTED=true

# ===============================================
# STREAM CONFIGURATION
# ===============================================
ENABLE_STREAM_LINKS=true
STREAM_LINK_TTL_SECONDS=1800

# Domain where your bot is accessible (for stream links)
BASE_URL=https://your-domain.com
BASE_URL_PORT=8060

# ===============================================
# SERVER
# ===============================================
# Enable HTTPS (requires SSL certificates)
ENABLE_HTTPS=false
SSL_CERT_PATH=/app/certs/cert.pem
SSL_KEY_PATH=/app/certs/key.pem

# ===============================================
# LOGGING
# ===============================================
LOG_LEVEL=INFO
EOF

echo "✅ Created .env.production.example (no real credentials)"
```

---

## 📋 Pre-Deployment Checklist (For Each VPS)

### Step 1: Environment Setup
- [ ] Create `.env.production` from `.env.production.example`
- [ ] Fill in ACTUAL values on the VPS (never in git!)
- [ ] Verify BOT_TOKEN is valid with @BotFather
- [ ] Verify OWNER_ID matches your Telegram user ID
- [ ] Generate secure REDIS_PASSWORD: `openssl rand -hex 32`

### Step 2: Certificate Setup (If using HTTPS)
```bash
# Option A: Use Let's Encrypt (Recommended)
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates to data/certs/
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem data/certs/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem data/certs/key.pem
sudo chmod 644 data/certs/*

# Update .env.production:
# ENABLE_HTTPS=true
```

### Step 3: Deploy Services
```bash
# SSH into VPS
ssh user@your-vps.com

# Clone repository (fresh, no git history with credentials)
git clone https://github.com/YOUR_REPO/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Create production configuration
# IMPORTANT: Type values manually or use secure secret injection
nano config/.env.production

# Build and start
docker compose -f deployment/docker-compose.yml up -d --build

# Verify startup
docker compose -f deployment/docker-compose.yml logs app --tail=50
```

### Step 4: Health Checks
```bash
# Wait 30 seconds for services to stabilize
sleep 30

# Run health check
./scripts/quick_health_check.sh

# Expected output:
# ✅ Docker daemon responsive
# ✅ All containers running
# ✅ Redis accessible
# ✅ MongoDB initialized
# ✅ Web server responsive on :8060
# ✅ Bot connected to Telegram
```

### Step 5: Functionality Tests
```bash
# Test bot responsiveness
# Send /ping to your bot on Telegram
# Expected: Bot responds with "Pong!"

# Test stream link generation
# Send /streamlink or reply to a file with /streamlink
# Expected: Generates link like https://your-domain.com:8060/stream/{token}

# Test web dashboard
# Visit http://your-domain.com:8060 in browser
# Expected: Dashboard loads successfully
```

---

## 🔒 Production Security Checklist

### Firewall Configuration
```bash
# Only expose necessary ports
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8060/tcp    # Bot Web Server
sudo ufw enable
```

### Database Backups
```bash
# Automated daily backup (add to crontab)
0 2 * * * docker exec mltb-mongodb mongodump --archive=/backups/mongodb-$(date +\%Y\%m\%d).archive

# Weekly backup to S3 (optional)
0 3 * * 0 aws s3 cp /backups/ s3://your-backup-bucket/ --recursive
```

### Monitoring & Alerts
- [ ] Set up health check: `*/5 * * * * curl -f http://localhost:8060/health || alert`
- [ ] Monitor logs: `docker compose logs app | grep -i error`
- [ ] Alert on crashes: Configure Telegram alerts in config

### Logs Retention
```bash
# Logs auto-rotate (configured in .env)
LOG_ROTATION_SIZE=52428800  # 50MB
LOG_ROTATION_BACKUPS=10
LOG_RETENTION_DAYS=30
```

---

## ✅ Validation Commands (Run on Each VPS)

```bash
# 1. All services running?
docker compose -f deployment/docker-compose.yml ps

# 2. No exposed credentials?
grep -r "YOUR_" config/ && echo "❌ ERROR: Placeholder values still in config"
docker compose -f deployment/docker-compose.yml exec app env | grep BOT_TOKEN | grep -v "^BOT_TOKEN=$" && echo "✅ BOT_TOKEN not visible"

# 3. Bot responsive?
curl -s http://localhost:8060/health | grep -q "ok" && echo "✅ Health check passed"

# 4. Logs clean (no critical errors)?
docker compose -f deployment/docker-compose.yml logs app --since 10m | grep -i critical && echo "⚠️ Critical errors found" || echo "✅ No critical errors"

# 5. Disk space OK?
df -h / | tail -1 | awk '{print $5}' | sed 's/%//' | awk '{if ($1 > 80) print "⚠️ Disk " $1 "% full"; else print "✅ Disk space OK"}'
```

---

## 🚨 Common Production Issues & Fixes

### Issue: Stream links return 413 "File too large"
**Root Cause**: File > 20MB (Telegram Bot API limit)
**Fix**: Only stream files < 20MB or implement User API (future feature)

### Issue: Bot not responding to commands
**Root Cause**:
- Stale pending updates
- BOT_TOKEN invalid
- Webhook conflicts
**Fix**:
```bash
# Clear pending updates
docker compose exec app python -c "
import aiohttp, asyncio
async def drop():
    url = 'https://api.telegram.org/bot{token}/deleteWebhook'
    async with aiohttp.ClientSession() as s:
        async with s.get(url, params={'drop_pending_updates': 'true'}) as r:
            print(await r.text())
asyncio.run(drop())
"
```

### Issue: Database connection fails
**Root Cause**: MongoDB not initialized
**Fix**:
```bash
docker compose -f deployment/docker-compose.yml up -d mltb-mongodb
sleep 10
docker compose -f deployment/docker-compose.yml up -d app
```

---

## 📊 Post-Deployment Monitoring

### Daily Checks
```bash
# Check bot is running
wget -q -O- http://localhost:8060/health

# Count handled updates
docker compose logs app --since 24h | grep -c "Updated from Telegram"

# Disk usage
du -sh /app/downloads/
```

### Performance Baseline
```bash
# Record baseline metrics
docker compose exec app python -c "
from bot.core.metrics import metrics
print('Memory:', metrics.memory_usage())
print('CPU:', metrics.cpu_usage())
print('Handled:', metrics.total_updates())
"
```

---

## 🆘 Emergency Procedures

### If Bot Crashes
```bash
# 1. Check logs
docker compose logs app --tail=100

# 2. Restart
docker compose -f deployment/docker-compose.yml restart app

# 3. If still failing, rebuild
docker compose -f deployment/docker-compose.yml up -d --build app

# 4. If database corrupted
docker compose down
rm -rf data/db/*
docker compose up -d
```

### If Disk Full
```bash
# Find large files
du -sh data/downloads/* | sort -h | tail -5

# Clean old downloads
find /app/downloads -mtime +7 -delete

# Clean Docker images
docker image prune -f --filter "until=720h"
```

---

## ✅ FINAL DEPLOYMENT SIGN-OFF

Before deploying to production, verify:

- [ ] All credentials rotated (new BOT_TOKEN, API/HASH)
- [ ] `.env.production` NEVER committed to git
- [ ] `.env.production.example` in git (template only)
- [ ] HTTPS configured (or explicitly disabled)
- [ ] Firewall rules configured
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured
- [ ] Health checks passing
- [ ] All commands working (test /ping, stream link, etc)
- [ ] First deployment successful on dev VPS
- [ ] Ready for production deployment

---

**Last Updated**: 2026-02-21
**Status**: Ready for first VPS deployment after addressing checklist
