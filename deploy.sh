#!/bin/bash
# MLTB Phase 1 Production Deployment Script
# Integrates all newly created components for easy deployment

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   MLTB Phase 1 - Production Deployment Automation              ║"
echo "║   All Components Integrated & Ready                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Check Docker
echo -e "${YELLOW}[1/6]${NC} Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗${NC} Docker not found. Please install Docker."
    exit 1
fi
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}✗${NC} Docker Compose not found. Please install Docker Compose."
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker & Docker Compose installed"

# Step 2: Setup environment
echo ""
echo -e "${YELLOW}[2/6]${NC} Setting up environment configuration..."
if [ ! -f .env.production ]; then
    cp .env.security.example .env.production
    echo -e "${GREEN}✓${NC} Created .env.production (edit with your values)"
    echo "   ⚠️  IMPORTANT: Update .env.production with your Telegram bot token and API credentials"
    read -p "   Press Enter to continue, or Ctrl+C to edit .env.production first..."
else
    echo -e "${GREEN}✓${NC} .env.production already exists"
fi

# Step 3: Create required directories
echo ""
echo -e "${YELLOW}[3/6]${NC} Creating required directories..."
mkdir -p backups logs downloads
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/provisioning/datasources
echo -e "${GREEN}✓${NC} Directories created"

# Step 4: Verify all components
echo ""
echo -e "${YELLOW}[4/6]${NC} Verifying all components..."

REQUIRED_FILES=(
    "docker-compose.secure.yml"
    "docker-compose.enhanced.yml"
    "bot/core/celery_config.py"
    "scripts/health_check.sh"
    "scripts/backup.sh"
    "scripts/mongodb-init.js"
    "monitoring/prometheus/alert.rules.yml"
    "monitoring/grafana/dashboards/mltb-overview.json"
    "monitoring/grafana/dashboards/mltb-health.json"
    "tests/test_api_endpoints.py"
    "tests/test_load_performance.py"
)

MISSING=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (MISSING)"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo ""
    echo -e "${RED}✗${NC} $MISSING required files are missing"
    exit 1
fi
echo -e "${GREEN}✓${NC} All components present"

# Step 5: Build & Start Services
echo ""
echo -e "${YELLOW}[5/6]${NC} Building and starting Docker services..."
echo "   Using: docker-compose.secure.yml"
echo ""

COMPOSE_FILE="${1:-docker-compose.secure.yml}"
if [ ! -f "$COMPOSE_FILE" ]; then
    COMPOSE_FILE="docker-compose.enhanced.yml"
fi

docker-compose -f "$COMPOSE_FILE" up -d --build

echo ""
echo -e "${GREEN}✓${NC} Services started"
echo "   Waiting for services to be ready..."
sleep 5

# Step 6: Verify deployment
echo ""
echo -e "${YELLOW}[6/6]${NC} Verifying deployment..."

SERVICES_OK=0
SERVICES_TOTAL=7

# Check each service
services=("app" "redis" "mongodb" "celery-worker" "celery-beat" "prometheus" "grafana")
for service in "${services[@]}"; do
    if docker-compose -f "$COMPOSE_FILE" ps "$service" 2>/dev/null | grep -q "Up"; then
        echo -e "  ${GREEN}✓${NC} $service - Running"
        SERVICES_OK=$((SERVICES_OK + 1))
    else
        echo -e "  ${RED}✗${NC} $service - Not running"
    fi
done

echo ""
if [ $SERVICES_OK -eq $SERVICES_TOTAL ]; then
    echo -e "${GREEN}✓${NC} All $SERVICES_TOTAL services running successfully"
else
    echo -e "${YELLOW}⚠${NC} $SERVICES_OK/$SERVICES_TOTAL services running"
fi

# Test endpoints
echo ""
echo "Testing endpoints..."
sleep 3

WEB_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ 2>/dev/null || echo "000")
METRICS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/metrics 2>/dev/null || echo "000")
PROMETHEUS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9091/-/healthy 2>/dev/null || echo "000")
GRAFANA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health 2>/dev/null || echo "000")

if [ "$WEB_STATUS" = "200" ]; then
    echo -e "  ${GREEN}✓${NC} Web endpoint: HTTP $WEB_STATUS"
else
    echo -e "  ${RED}✗${NC} Web endpoint: HTTP $WEB_STATUS"
fi

if [ "$METRICS_STATUS" = "200" ]; then
    echo -e "  ${GREEN}✓${NC} Metrics endpoint: HTTP $METRICS_STATUS"
else
    echo -e "  ${RED}✗${NC} Metrics endpoint: HTTP $METRICS_STATUS"
fi

if [ "$PROMETHEUS_STATUS" = "200" ]; then
    echo -e "  ${GREEN}✓${NC} Prometheus: HTTP $PROMETHEUS_STATUS"
else
    echo -e "  ${RED}✗${NC} Prometheus: HTTP $PROMETHEUS_STATUS"
fi

if [ "$GRAFANA_STATUS" = "200" ] || [ "$GRAFANA_STATUS" = "302" ]; then
    echo -e "  ${GREEN}✓${NC} Grafana: HTTP $GRAFANA_STATUS"
else
    echo -e "  ${RED}✗${NC} Grafana: HTTP $GRAFANA_STATUS"
fi

# Schedule maintenance tasks
echo ""
echo "Setting up scheduled maintenance tasks..."
CRON_FILE="/tmp/mltb_cron_setup.txt"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat > "$CRON_FILE" << EOF
# MLTB Health Checks (every 5 minutes)
*/5 * * * * $SCRIPT_DIR/scripts/health_check.sh >> $SCRIPT_DIR/logs/health_check.log 2>&1

# MLTB Backups (daily at 2 AM)
0 2 * * * $SCRIPT_DIR/scripts/backup.sh >> $SCRIPT_DIR/logs/backup.log 2>&1

# Log cleanup (daily at 3 AM)
0 3 * * * find $SCRIPT_DIR/logs -name "*.log.*" -mtime +30 -delete

# Docker Compose health check (every 10 minutes)
*/10 * * * * cd $SCRIPT_DIR && docker-compose -f $COMPOSE_FILE ps | grep -q "(unhealthy)" && docker-compose -f $COMPOSE_FILE restart app || true >> $SCRIPT_DIR/logs/docker_health.log 2>&1
EOF

echo -e "${GREEN}✓${NC} Cron tasks configured (review suggested additions above)"
echo ""
echo "To enable automatic tasks, add to your crontab:"
echo "  crontab -e"
echo "  # Then paste the contents of $CRON_FILE"

# Final summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   ✅ DEPLOYMENT COMPLETE                                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Access your services:"
echo ""
echo "  🌐 Bot Web Interface:"
echo "     http://localhost:8000"
echo ""
echo "  📊 Grafana Dashboards:"
echo "     http://localhost:3000"
echo "     Username: admin"
echo "     Password: admin (CHANGE THIS!)"
echo ""
echo "  📈 Prometheus Metrics:"
echo "     http://localhost:9091"
echo ""
echo "  🔧 Metrics Endpoint:"
echo "     curl http://localhost:9090/metrics"
echo ""
echo "🧪 Run tests:"
echo ""
echo "  python tests/test_api_endpoints.py"
echo "  python tests/test_load_performance.py"
echo ""
echo "🏥 Check health:"
echo ""
echo "  ./scripts/health_check.sh"
echo ""
echo "💾 Manual backup:"
echo ""
echo "  ./scripts/backup.sh"
echo ""
echo "📋 View logs:"
echo ""
echo "  docker-compose -f $COMPOSE_FILE logs -f app"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  1. Update .env.production with your credentials"
echo "  2. Change Grafana admin password (http://localhost:3000)"
echo "  3. Configure backups location and retention"
echo "  4. Setup alert notifications (Slack, email, etc.)"
echo "  5. Review and enable cron jobs for automation"
echo ""
echo "Documentation:"
echo "  - PHASE_1_ADVANCED_OPTIONS_COMPLETE.md"
echo "  - OPTION_7_SECURITY_SETUP.md"
echo "  - OPTION_8_PRODUCTION_HARDENING.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
