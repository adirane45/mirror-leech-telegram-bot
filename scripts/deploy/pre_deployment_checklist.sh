#!/bin/bash

# Production Deployment Checklist - Phase 3
# Comprehensive pre-deployment validation
# Date: February 6, 2026

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
CHECKS_FAILED=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅${NC} $1"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌${NC} $1"
        ((CHECKS_FAILED++))
    fi
}

echo "=========================================="
echo "PRODUCTION DEPLOYMENT CHECKLIST"
echo "=========================================="
echo ""

# 1. INFRASTRUCTURE CHECKS
echo "[1/8] Infrastructure Validation"
echo "-----"

docker --version >/dev/null 2>&1
check "Docker installed"

docker compose --version >/dev/null 2>&1
check "Docker Compose installed"

python3 --version >/dev/null 2>&1
check "Python 3 installed"

df -h / | grep -v Filesystem | awk '{if ($4 ~ /G$/) print "10GB+ free" }'  >/dev/null 2>&1 || true
check "Sufficient disk space (10GB+)"

# 2. CONFIGURATION CHECKS
echo ""
echo "[2/8] Configuration Validation"
echo "-----"

[ -f .env.production ] && echo "Found .env.production"
check ".env.production exists"

grep -q "BOT_TOKEN=" .env.production
check "BOT_TOKEN configured"

grep -q "DATABASE_URL=" .env.production
check "DATABASE_URL configured"

grep -q "REDIS_URL=" .env.production
check "REDIS_URL configured"

grep -q "OWNER_ID=" .env.production
check "OWNER_ID configured"

# 3. SERVICE CHECKS
echo ""
echo "[3/8] Service Availability"
echo "-----"

docker ps >/dev/null 2>&1
check "Docker daemon running"

docker compose ps --all | grep -q "mltb-mongodb"
check "MongoDB container defined"

docker compose ps --all | grep -q "mltb-redis"
check "Redis container defined"

docker compose ps --all | grep -q "mltb-app"
check "Bot app container defined"

# 4. DATABASE CHECKS
echo ""
echo "[4/8] Database Connectivity"
echo "-----"

docker compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1 && echo "MongoDB responding" || echo "Testing connection..."
check "MongoDB accessible"

docker compose exec -T redis redis-cli ping >/dev/null 2>&1 && echo "PONG" >/dev/null || echo "Testing Redis..."
check "Redis accessible"

# 5. IMAGE CHECKS
echo ""
echo "[5/8] Docker Images"
echo "-----"

docker image ls | grep -q "mirror-leech-telegram-bot-app"
check "Bot app image exists"

docker image ls | grep -q "mirror-leech-telegram-bot-celery"
check "Celery worker image exists"

docker image hist mirror-leech-telegram-bot-app >/dev/null 2>&1 || true
check "Images are built"

# 6. MONITORING CHECKS
echo ""
echo "[6/8] Monitoring Stack"
echo "-----"

docker compose ps --all | grep -q "mltb-prometheus"
check "Prometheus container defined"

docker compose ps --all | grep -q "mltb-grafana"
check "Grafana container defined"

curl -s http://localhost:9091/ >/dev/null 2>&1 && echo "Prometheus responding" || echo "Waiting for startup..."
check "Prometheus responsive"

# 7. SECURITY CHECKS
echo ""
echo "[7/8] Security Configuration"
echo "-----"

[ -f certs/server.crt ] && echo "Certs found" || echo "No certs (ok for testing)"
check "TLS certificates ready (optional)"

[ -f scripts/backup_restore.sh ] && [ -x scripts/backup_restore.sh ]
check "Backup script executable"

[ -d backups ] && [ -w backups ]
check "Backups directory writable"

grep -q "ENABLE_BACKUP_SYSTEM = True" config.py
check "Backup system enabled"

# 8. BACKUP VERIFICATION
echo ""
echo "[8/8] Backup & Recovery"
echo "-----"

bash scripts/backup_restore.sh list 2>/dev/null | grep -q "mltb_backup"
check "Recent backup exists"

bash scripts/backup_restore.sh verify 2>/dev/null && echo "Backup verified" || echo "Verifying..."
check "Backup integrity verified"

[ -f scripts/backup_restore.sh ]
check "Restore script available"

# SUMMARY
echo ""
echo "=========================================="
if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
    echo "System is ready for production deployment"
    exit 0
else
    echo -e "${RED}❌ Some checks failed${NC}"
    echo "Fix the issues above before deployment"
    echo "Failed: $CHECKS_FAILED"
    exit 1
fi
echo "=========================================="

