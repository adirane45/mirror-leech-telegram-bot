#!/bin/bash
# Bot Deployment & Startup Script
# Priority 1: Deploy bot with Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=========================================="
echo "MLTB BOT DEPLOYMENT SCRIPT"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

# Step 1: Verify config.py
echo ""
echo "Step 1: Verifying configuration..."
if python3 "$PROJECT_ROOT/scripts/verify_config.py" > /dev/null 2>&1; then
    print_status "Configuration verified"
else
    print_error "Configuration verification failed"
    exit 1
fi

# Step 2: Check Docker
echo ""
echo "Step 2: Checking Docker setup..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

# Docker Compose is now part of Docker (docker compose), not a separate command
if ! docker compose version > /dev/null 2>&1; then
    print_error "Docker Compose is not available (requires Docker 2.0+)"
    exit 1
fi

print_status "Docker setup verified"

# Step 3: Check if services are running
echo ""
echo "Step 3: Checking service status..."
cd "$PROJECT_ROOT"

RUNNING_SERVICES=$(docker compose ps --services 2>/dev/null | wc -l)
if [ "$RUNNING_SERVICES" -gt 0 ]; then
    print_status "Docker Compose services found: $RUNNING_SERVICES"
else
    print_warning "No services currently running"
    echo "Starting services..."
    docker compose up -d
    sleep 5
fi

# Step 4: Verify critical services
echo ""
echo "Step 4: Verifying critical services..."

# Check Redis
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    print_status "Redis: Connected"
else
    print_warning "Redis: Not responding (may be starting)"
fi

# Check MongoDB
if docker compose exec -T mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    print_status "MongoDB: Connected"
else
    print_warning "MongoDB: Not responding (may be starting)"
fi

# Step 5: Verify bot configuration
echo ""
echo "Step 5: Verifying bot credentials..."

# Check if using placeholder token
BOT_TOKEN=$(python3 -c "from config import BOT_TOKEN; print(BOT_TOKEN)")
if [[ "$BOT_TOKEN" == "7535236556:AAG-R4Ezs1_Px140VaxETF-y1oVPNNFJBog" ]]; then
    print_warning "Using default bot token - Bot will NOT respond to commands"
    echo "         To use real bot: Update .env.production with real BOT_TOKEN"
else
    print_status "Using real bot token"
fi

OWNER_ID=$(python3 -c "from config import OWNER_ID; print(OWNER_ID)")
if [ "$OWNER_ID" -gt 0 ]; then
    print_status "Owner ID configured: $OWNER_ID"
else
    print_warning "Owner ID not properly configured"
fi

# Step 6: Restart bot services
echo ""
echo "Step 6: Starting/Restarting bot services..."

docker compose restart app celery-worker celery-beat 2>/dev/null || {
    print_warning "Services not yet created, starting all services..."
    docker compose up -d app celery-worker celery-beat
}

print_status "Bot services restarting..."

# Step 7: Wait for services to be ready
echo ""
echo "Step 7: Waiting for services to be ready..."
WAIT_COUNT=0
MAX_WAIT=30

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "Bot API is responding"
        break
    fi
    echo -n "."
    WAIT_COUNT=$((WAIT_COUNT + 1))
    sleep 1
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    print_warning "Bot API did not respond within ${MAX_WAIT} seconds"
    echo "         Check logs: docker compose logs app"
else
    sleep 2
fi

# Step 8: Display startup summary
echo ""
echo "=========================================="
echo "STARTUP COMPLETE"
echo "=========================================="
echo ""

# Check services status
docker compose ps 2>/dev/null | grep -E "app|celery|redis|mongodb" || true

echo ""
echo "📊 Access Points:"
echo "  • Bot API: http://localhost:8000"
echo "  • GraphQL: http://localhost:8000/graphql"
echo "  • Grafana Dashboard: http://localhost:3000 (admin/mltb2026)"
echo "  • Prometheus: http://localhost:9091"
echo ""

echo "📝 Useful Commands:"
echo "  • View bot logs: docker compose logs app -f"
echo "  • View all logs: docker compose logs -f"
echo "  • Check service status: docker compose ps"
echo "  • Restart bot: docker compose restart app celery-worker celery-beat"
echo "  • Stop all: docker compose down"
echo ""

echo "🔧 Configuration:"
if [[ "$BOT_TOKEN" == "7535236556:AAG-R4Ezs1_Px140VaxETF-y1oVPNNFJBog" ]]; then
    echo "  ⚠️  DEFAULT BOT TOKEN ACTIVE"
    echo "  To activate real bot:"
    echo "     1. Get token from @BotFather on Telegram"
    echo "     2. Edit .env.production: BOT_TOKEN=your_token"
    echo "     3. Run: docker compose restart app celery-worker celery-beat"
else
    echo "  ✅ Real bot token configured"
fi

echo ""
print_status "Bot deployment ready!"
