#!/bin/bash

################################################################################
# MLTB Bot Quick Health Check
#
# Lightweight version of the comprehensive health check
# Usage: ./scripts/quick_health_check.sh
# Exit Codes:
#   0 = All critical systems healthy ✅
#   1 = One or more issues detected ⚠️
#   2 = Critical failure ❌
################################################################################

set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

PASSED=0
FAILED=0

# Output functions
pass() { echo -e "${GREEN}✅${NC} $1"; ((PASSED++)); }
fail() { echo -e "${RED}❌${NC} $1"; ((FAILED++)); }
warn() { echo -e "${YELLOW}⚠️${NC} $1"; }
info() { echo -e "${BLUE}ℹ️${NC} $1"; }

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     MLTB Bot - Quick Health Check                       ║"
echo "║     $(date '+%Y-%m-%d %H:%M:%S')                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo

# 1. Docker and containers
info "Checking Docker and containers..."
if ! docker ps > /dev/null 2>&1; then
    fail "Docker is not responding"
    exit 2
fi
pass "Docker daemon responsive"

# Check critical containers
for container in mltb-app mltb-redis mltb-aria2 mltb-qbittorrent; do
    if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "^$container$"; then
        pass "Container $container running"
    else
        fail "Container $container NOT running"
    fi
done

echo

# 2. Core services
info "Checking core services..."

# Redis
if timeout 5 bash -c "echo >/dev/tcp/localhost/6379" 2>/dev/null; then
    pass "Redis accessible (port 6379)"
else
    fail "Redis NOT accessible"
fi

# Web Server
if timeout 5 curl -s http://localhost:8060/ > /dev/null 2>&1; then
    pass "Web Dashboard accessible (port 8060)"
else
    fail "Web Dashboard NOT accessible"
fi

# Aria2 RPC
if timeout 5 bash -c "echo >/dev/tcp/localhost/6800" 2>/dev/null; then
    pass "Aria2 RPC accessible (port 6800)"
else
    fail "Aria2 RPC NOT accessible"
fi

# qBittorrent
if timeout 5 bash -c "echo >/dev/tcp/localhost/8090" 2>/dev/null; then
    pass "qBittorrent accessible (port 8090)"
else
    fail "qBittorrent NOT accessible"
fi

# GraphQL API
if timeout 5 curl -s -X POST -H "Content-Type: application/json" --data '{"query":"{status{version}}"}' http://localhost:8060/graphql 2>/dev/null | grep -q '"data"'; then
    pass "GraphQL API working"
else
    fail "GraphQL API NOT working"
fi

echo

# 3. Storage
info "Checking storage..."
local_usage=$(df /home/kali/mirror-leech-telegram-bot/data 2>/dev/null | awk 'NR==2 {print $5}' | sed 's/%//')
if [ -n "$local_usage" ] && [ "$local_usage" -lt 80 ]; then
    pass "Disk usage healthy (${local_usage}%)"
else
    warn "Disk usage warning (${local_usage}%)"
fi

echo

# 4. Configuration
info "Checking configuration..."
[ -f "config/main_config.py" ] && pass "Config file exists" || fail "Config file missing"
[ -f "config/.env.production" ] && pass "Environment file exists" || fail "Environment file missing"

echo

# Summary
echo "════════════════════════════════════════════════════════════"
echo -e "Passed: ${GREEN}${PASSED}${NC}  |  Failed: ${RED}${FAILED}${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}Status: ✅ All critical systems operational${NC}"
    echo "════════════════════════════════════════════════════════════"
    exit 0
else
    echo -e "${RED}Status: ⚠️ Issues detected - run comprehensive check${NC}"
    echo "  Run: ./scripts/health_check_comprehensive.sh"
    echo "════════════════════════════════════════════════════════════"
    exit 1
fi
