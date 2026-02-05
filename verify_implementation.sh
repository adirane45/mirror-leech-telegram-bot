#!/bin/bash
# Verification Script - Check Phase 1 Implementation
# Safe Innovation Path
# Enhanced by: justadi

echo "🔍 Verification Script - Phase 1 Implementation"
echo "================================================"
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} $1 missing"
        ((FAIL++))
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/ directory exists"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} $1/ directory missing"
        ((FAIL++))
        return 1
    fi
}

echo "📦 Checking Core Files..."
echo "-------------------------"
check_file "bot/core/redis_manager.py"
check_file "bot/core/celery_app.py"
check_file "bot/core/celery_tasks.py"
check_file "bot/core/metrics.py"
check_file "bot/core/enhanced_startup.py"
check_file "bot/core/api_endpoints.py"
echo

echo "🧪 Checking Test Files..."
echo "-------------------------"
check_dir "tests"
check_file "tests/conftest.py"
check_file "tests/test_redis_manager.py"
check_file "tests/test_metrics.py"
check_file "tests/test_integration.py"
check_file "run_tests.py"
echo

echo "🐳 Checking Docker Files..."
echo "-------------------------"
check_file "docker-compose.enhanced.yml"
echo

echo "📊 Checking Monitoring Files..."
echo "-------------------------"
check_dir "monitoring"
check_file "monitoring/prometheus.yml"
check_dir "monitoring/grafana"
check_file "monitoring/grafana/datasources/prometheus.yml"
check_file "monitoring/grafana/dashboards/dashboards.yml"
echo

echo "⚙️  Checking Configuration Files..."
echo "-------------------------"
check_file "config_enhancements.py"
echo

echo "📚 Checking Documentation..."
echo "-------------------------"
check_file "MIGRATION_GUIDE.md"
check_file "ENHANCEMENT_SUMMARY.md"
check_file "README_ENHANCEMENTS.md"
echo

echo "🛠️  Checking Utility Scripts..."
echo "-------------------------"
check_file "quick_start.sh"
[ -x "quick_start.sh" ] && echo -e "${GREEN}✓${NC} quick_start.sh is executable" || echo -e "${YELLOW}⚠${NC} quick_start.sh needs chmod +x"
[ -x "run_tests.py" ] && echo -e "${GREEN}✓${NC} run_tests.py is executable" || echo -e "${YELLOW}⚠${NC} run_tests.py needs chmod +x"
echo

echo "🔍 Checking Dependencies..."
echo "-------------------------"
check_file "requirements-enhanced.txt"
echo

echo "📝 Summary"
echo "================================================"
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 All Phase 1 files are present!${NC}"
    echo
    echo "Next steps:"
    echo "1. Review README_ENHANCEMENTS.md for quick start"
    echo "2. Run: ./quick_start.sh"
    echo "3. Or read MIGRATION_GUIDE.md for detailed setup"
    echo
    exit 0
else
    echo -e "${RED}⚠️  Some files are missing. Please check the implementation.${NC}"
    exit 1
fi
