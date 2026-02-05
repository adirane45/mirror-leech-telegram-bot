#!/bin/bash
# Quick Start Script for Enhanced MLTB
# Safe Innovation Path - Phase 1
# Enhanced by: justadi
# Date: February 5, 2026

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Enhanced MLTB v3.1.0 - Quick Start       ║${NC}"
echo -e "${BLUE}║  Safe Innovation Path - Phase 1            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Function to prompt user
prompt_yes_no() {
    while true; do
        read -p "$1 (y/n): " yn
        case $yn in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

echo -e "${YELLOW}📋 Choose your setup mode:${NC}"
echo
echo "1. Basic Mode - No enhancements (same as v3.0.0)"
echo "2. Minimal Enhancement - Only metrics (recommended for first-time)"
echo "3. Full Enhancement - All features (Redis, Celery, Prometheus, Grafana)"
echo
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo -e "${GREEN}✅ Using Basic Mode${NC}"
        USE_ENHANCEMENTS=false
        ;;
    2)
        echo -e "${GREEN}✅ Using Minimal Enhancement${NC}"
        USE_ENHANCEMENTS=true
        MINIMAL_MODE=true
        ;;
    3)
        echo -e "${GREEN}✅ Using Full Enhancement${NC}"
        USE_ENHANCEMENTS=true
        MINIMAL_MODE=false
        ;;
    *)
        echo -e "${RED}❌ Invalid choice${NC}"
        exit 1
        ;;
esac

echo

# Check if config.py exists
if [ ! -f "config.py" ]; then
    echo -e "${YELLOW}⚠️  config.py not found${NC}"
    
    if [ -f "config_sample.py" ]; then
        echo -e "${BLUE}Creating config.py from config_sample.py...${NC}"
        cp config_sample.py config.py
        
        if [ "$USE_ENHANCEMENTS" = true ]; then
            echo -e "${BLUE}Adding enhancement configurations...${NC}"
            cat config_enhancements.py >> config.py
        fi
        
        echo -e "${YELLOW}⚠️  Please edit config.py and add your credentials${NC}"
        echo -e "${YELLOW}Required: BOT_TOKEN, OWNER_ID, TELEGRAM_API, TELEGRAM_HASH${NC}"
        
        if prompt_yes_no "Do you want to edit config.py now?"; then
            ${EDITOR:-nano} config.py
        else
            echo -e "${RED}Please edit config.py before starting the bot${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ config_sample.py not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ config.py found${NC}"
    
    if [ "$USE_ENHANCEMENTS" = true ] && ! grep -q "ENABLE_REDIS_CACHE" config.py; then
        echo -e "${YELLOW}⚠️  Adding enhancement configurations to config.py...${NC}"
        echo "" >> config.py
        cat config_enhancements.py >> config.py
        echo -e "${GREEN}✅ Enhancement configurations added${NC}"
    fi
fi

# Create necessary directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p downloads logs backups monitoring/grafana/dashboards monitoring/grafana/datasources

# Choose Docker Compose file
if [ "$USE_ENHANCEMENTS" = true ] && [ "$MINIMAL_MODE" = false ]; then
    COMPOSE_FILE="docker-compose.enhanced.yml"
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo -e "${RED}❌ $COMPOSE_FILE not found${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Using enhanced Docker Compose configuration${NC}"
    
    # Prompt for MongoDB password
    echo
    echo -e "${YELLOW}🔐 Security Configuration${NC}"
    read -sp "Enter MongoDB password (or press Enter for default 'mltb_secure_pass'): " MONGO_PASSWORD
    echo
    
    if [ -z "$MONGO_PASSWORD" ]; then
        MONGO_PASSWORD="mltb_secure_pass"
    fi
    
    # Update docker-compose file with password
    sed -i.bak "s/MONGO_INITDB_ROOT_PASSWORD: .*/MONGO_INITDB_ROOT_PASSWORD: $MONGO_PASSWORD/" "$COMPOSE_FILE"
    
    # Ask about Grafana password
    read -sp "Enter Grafana admin password (or press Enter for default 'admin'): " GRAFANA_PASSWORD
    echo
    
    if [ ! -z "$GRAFANA_PASSWORD" ]; then
        sed -i.bak "s/GF_SECURITY_ADMIN_PASSWORD: .*/GF_SECURITY_ADMIN_PASSWORD: $GRAFANA_PASSWORD/" "$COMPOSE_FILE"
    fi
    
else
    COMPOSE_FILE="docker-compose.yml"
    echo -e "${BLUE}Using basic Docker Compose configuration${NC}"
fi

# Build and start containers
echo
echo -e "${BLUE}🚀 Building and starting containers...${NC}"
echo

if [ "$USE_ENHANCEMENTS" = true ] && [ "$MINIMAL_MODE" = false ]; then
    docker-compose -f "$COMPOSE_FILE" up -d --build
else
    docker-compose -f "$COMPOSE_FILE" up -d --build
fi

# Wait for services to be ready
echo
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 10

# Check service status
echo
echo -e "${BLUE}📊 Service Status:${NC}"
docker-compose -f "$COMPOSE_FILE" ps

# Display access information
echo
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          ✅ Setup Complete!                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo
echo -e "${BLUE}📍 Access URLs:${NC}"
echo -e "  • Bot Dashboard: http://localhost:8000"
echo -e "  • Health Check: http://localhost:8000/health"

if [ "$USE_ENHANCEMENTS" = true ] && [ "$MINIMAL_MODE" = false ]; then
    echo -e "  • Metrics: http://localhost:9090/metrics"
    echo -e "  • Prometheus: http://localhost:9091"
    echo -e "  • Grafana: http://localhost:3000 (admin/[your-password])"
    echo -e "  • MongoDB: localhost:27017"
fi

echo
echo -e "${BLUE}📝 Useful Commands:${NC}"
echo -e "  • View logs: docker-compose -f $COMPOSE_FILE logs -f app"
echo -e "  • Stop bot: docker-compose -f $COMPOSE_FILE down"
echo -e "  • Restart bot: docker-compose -f $COMPOSE_FILE restart app"
echo -e "  • View all logs: docker-compose -f $COMPOSE_FILE logs -f"

if [ "$USE_ENHANCEMENTS" = true ]; then
    echo
    echo -e "${BLUE}🧪 Testing:${NC}"
    echo -e "  • Run tests: python3 run_tests.py"
    echo -e "  • Run with coverage: python3 run_tests.py --coverage"
fi

echo
echo -e "${GREEN}🎉 Your Enhanced MLTB Bot is now running!${NC}"
echo
echo -e "${YELLOW}📚 Next Steps:${NC}"
echo -e "  1. Test bot with /start command on Telegram"
echo -e "  2. Check logs for any errors"
echo -e "  3. Review MIGRATION_GUIDE.md for advanced configuration"

if [ "$USE_ENHANCEMENTS" = true ] && [ "$MINIMAL_MODE" = false ]; then
    echo -e "  4. Configure Grafana dashboards"
    echo -e "  5. Set up Prometheus alerts (optional)"
fi

echo
