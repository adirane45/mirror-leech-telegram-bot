#!/bin/bash
# Health Check Script for MLTB Production Deployment
# Verifies all services are running and healthy

set -e

# Define colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🏥 Running health checks..."
echo ""

# Check web service
echo -n "Checking Web Service (8050)... "
if curl -f -s http://localhost:8050/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
    exit 1
fi

# Check Redis
echo -n "Checking Redis (6379)... "
if redis-cli -p 6379 ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
    exit 1
fi

# Check MongoDB
echo -n "Checking MongoDB (27017)... "
if mongosh mongodb://localhost:27017 --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
    exit 1
fi

# Check metrics endpoint
echo -n "Checking Metrics Endpoint (9090)... "
if curl -f -s http://localhost:9090/metrics > /dev/null 2>&1; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
    exit 1
fi

# Check Prometheus
echo -n "Checking Prometheus (9091)... "
if curl -f -s http://localhost:9091/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
    exit 1
fi

# Check Grafana
echo -n "Checking Grafana (3000)... "
if curl -f -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ HEALTHY${NC}"
else
    echo -e "${RED}❌ UNHEALTHY${NC}"
    exit 1
fi

# Check disk space
echo -n "Checking Disk Space... "
DISK_USAGE=$(df /app | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${GREEN}✅ ${DISK_USAGE}% used${NC}"
else
    echo -e "${YELLOW}⚠️  ${DISK_USAGE}% used (critical)${NC}"
    exit 1
fi

# Check log directory
echo -n "Checking Log Directory... "
if [ -w /app/logs ]; then
    echo -e "${GREEN}✅ WRITABLE${NC}"
else
    echo -e "${RED}❌ NOT WRITABLE${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✨ All health checks passed!${NC}"
exit 0
