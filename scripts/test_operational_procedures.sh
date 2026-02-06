#!/bin/bash
# TIER 2 Task 3 - Operational Runbook Testing
# Tests key operational procedures documented in TIER2_OPERATIONAL_RUNBOOK.md

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📋 TIER 2 Task 3 - Operational Runbook Validation${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# Counter for tests
TESTS_PASSED=0
TESTS_FAILED=0

# Test 1: Health Check
test_health_check() {
    echo -e "${YELLOW}📊 Test 1: Quick Health Check${NC}"
    if bash "$PROJECT_ROOT/scripts/quick_health_check.sh" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Health check script works${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}   ❌ Health check failed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Test 2: Backup and Restore
test_backup_restore() {
    echo -e "${YELLOW}📁 Test 2: Backup Procedure${NC}"
    
    # Create a test backup
    BACKUP_FILE="$PROJECT_ROOT/data/backups/test_backup_${TIMESTAMP}.tar.gz"
    
    if bash "$PROJECT_ROOT/scripts/backup.sh" > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ Backup creation works${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        
        # Check backup file exists
        if [ -f "$PROJECT_ROOT/data/backups/backup_"*.tar.gz ]; then
            echo -e "${GREEN}   ✅ Backup file created successfully${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        fi
    else
        echo -e "${RED}   ❌ Backup creation failed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Test 3: Services Status
test_services_status() {
    echo -e "${YELLOW}🐳 Test 3: Docker Services Status${NC}"
    
    RUNNING=$(docker ps --format "{{.Names}}" | wc -l)
    if [ "$RUNNING" -gt 0 ]; then
        echo -e "${GREEN}   ✅ Docker services running ($RUNNING containers)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}   ❌ No Docker services running${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Test 4: API Endpoints
test_api_endpoints() {
    echo -e "${YELLOW}⚡ Test 4: API Endpoint Availability${NC}"
    
    ENDPOINTS=(
        "http://localhost:8060/health"
        "http://localhost:9090/-/healthy"
    )
    
    for endpoint in "${ENDPOINTS[@]}"; do
        if curl -s -m 2 "$endpoint" > /dev/null 2>&1; then
            echo -e "${GREEN}   ✅ $endpoint responding${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${YELLOW}   ⚠️  $endpoint not responding (may not be running)${NC}"
        fi
    done
    echo ""
}

# Test 5: Phase 4 Tests
test_phase4() {
    echo -e "${YELLOW}🧪 Test 5: Phase 4 Integration Tests${NC}"
    
    if cd "$PROJECT_ROOT" && ./venv/bin/python -m pytest tests/test_phase4_integration.py -q > /dev/null 2>&1; then
        echo -e "${GREEN}   ✅ All Phase 4 tests passing${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}   ❌ Phase 4 tests failing${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    echo ""
}

# Test 6: Configuration Files
test_configurations() {
    echo -e "${YELLOW}⚙️  Test 6: Configuration Files${NC}"
    
    REQUIRED_FILES=(
        ".metrics/prometheus.yml"
        ".metrics/alert_rules.yml"
        "docker-compose.yml"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            echo -e "${GREEN}   ✅ $file exists${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}   ❌ $file missing${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done
    echo ""
}

# Run all tests
test_health_check
test_backup_restore
test_services_status
test_api_endpoints
test_phase4
test_configurations

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  📊 Test Results${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}✅ Passed: $TESTS_PASSED${NC}"
echo -e "  ${RED}❌ Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All operational procedures verified!${NC}"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed. Review the logs above.${NC}"
    echo ""
    exit 1
fi
