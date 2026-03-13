#!/usr/bin/env bash
#
# Quick Start Script - Week 1: Foundation & Assessment
# Automates baseline measurements and initial audit
#
# Usage: ./scripts/improvement_quick_start.sh

set -e  # Exit on error

echo "=============================================="
echo "  Code Quality Improvement - Quick Start"
echo "  Week 1: Foundation & Assessment"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create output directory
REPORT_DIR="docs/audit_reports"
mkdir -p "$REPORT_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${GREEN}[1/8] Installing required tools...${NC}"
python -m pip install -q radon vulture pytest-cov 2>/dev/null || {
    echo -e "${YELLOW}Warning: Some tools may already be installed${NC}"
}

echo -e "${GREEN}[2/8] Analyzing architecture...${NC}"
echo "Core module count:"
CORE_COUNT=$(find src/bot/core -name "*.py" -type f | wc -l)
echo "  Total files in src/bot/core: $CORE_COUNT"

echo ""
echo "Top 15 largest files:"
find src/bot/core -name "*.py" -exec wc -l {} + | sort -rn | head -16 | tee "$REPORT_DIR/largest_files_${TIMESTAMP}.txt"

echo ""
echo "Module categories (by naming patterns):"
{
    echo "Cache-related: $(find src/bot/core -name "*cache*.py" | wc -l) files"
    echo "Failover-related: $(find src/bot/core -name "*failover*.py" | wc -l) files"
    echo "Dashboard-related: $(find src/bot/core -name "*dashboard*.py" | wc -l) files"
    echo "Alert-related: $(find src/bot/core -name "*alert*.py" | wc -l) files"
    echo "API-related: $(find src/bot/core -name "*api*.py" | wc -l) files"
    echo "Task-related: $(find src/bot/core -name "*task*.py" | wc -l) files"
    echo "Manager-related: $(find src/bot/core -name "*manager*.py" | wc -l) files"
} | tee "$REPORT_DIR/module_categories_${TIMESTAMP}.txt"

echo ""
echo -e "${GREEN}[3/8] Running complexity analysis...${NC}"
radon cc src/ -a -s | tee "$REPORT_DIR/complexity_baseline_${TIMESTAMP}.txt"
echo ""
echo "Complexity summary:"
radon cc src/ -a -s | grep "Average complexity" | tail -5

echo ""
echo -e "${GREEN}[4/8] Calculating maintainability index...${NC}"
radon mi src/ -s | tee "$REPORT_DIR/maintainability_baseline_${TIMESTAMP}.txt"
echo ""
echo "Maintainability by directory:"
radon mi src/ -s | grep "^src/" | head -10

echo ""
echo -e "${GREEN}[5/8] Searching for dead code...${NC}"
vulture src/ --min-confidence 80 | tee "$REPORT_DIR/dead_code_${TIMESTAMP}.txt" || {
    echo -e "${YELLOW}Note: Some unused code detected (see report)${NC}"
}

echo ""
echo -e "${GREEN}[6/8] Running test coverage analysis...${NC}"
if pytest tests/ --cov=src --cov-report=term --cov-report=html --cov-report=json -q 2>&1 | tee "$REPORT_DIR/coverage_baseline_${TIMESTAMP}.txt"; then
    echo -e "${GREEN}Coverage report generated${NC}"
    if [ -f coverage.json ]; then
        COVERAGE=$(python -c "import json; print(json.load(open('coverage.json'))['totals']['percent_covered'])" 2>/dev/null || echo "N/A")
        echo "Current coverage: ${COVERAGE}%"
        mv coverage.json "$REPORT_DIR/coverage_baseline_${TIMESTAMP}.json"
    fi
else
    echo -e "${YELLOW}Warning: Some tests may have failed${NC}"
fi

echo ""
echo -e "${GREEN}[7/8] Checking type coverage...${NC}"
if make type-check 2>&1 | tee "$REPORT_DIR/type_check_baseline_${TIMESTAMP}.txt"; then
    echo -e "${GREEN}Type checking passed${NC}"
else
    echo -e "${YELLOW}Type checking found issues (see report)${NC}"
fi

echo ""
echo -e "${GREEN}[8/8] Finding TODO/FIXME/XXX comments...${NC}"
{
    echo "=== TODO Comments ==="
    grep -r "TODO" src/ --include="*.py" | wc -l | xargs echo "Total TODO comments:"
    echo ""
    echo "=== FIXME Comments ==="
    grep -r "FIXME" src/ --include="*.py" | wc -l | xargs echo "Total FIXME comments:"
    echo ""
    echo "=== XXX Comments ==="
    grep -r "XXX" src/ --include="*.py" | wc -l | xargs echo "Total XXX comments:"
    echo ""
    echo "Sample TODOs:"
    grep -rn "TODO" src/ --include="*.py" | head -10
} | tee "$REPORT_DIR/todos_${TIMESTAMP}.txt"

echo ""
echo "=============================================="
echo -e "${GREEN}✓ Baseline assessment complete!${NC}"
echo "=============================================="
echo ""
echo "Reports saved to: $REPORT_DIR/"
echo ""
echo "Summary:"
echo "--------"
echo "  Core modules: $CORE_COUNT files"
echo "  Reports generated: $(ls -1 $REPORT_DIR/*${TIMESTAMP}* | wc -l)"
echo ""
echo "Next steps:"
echo "  1. Review reports in $REPORT_DIR/"
echo "  2. Open coverage report: firefox htmlcov/index.html"
echo "  3. Review checklist: docs/IMPLEMENTATION_CHECKLIST.md"
echo "  4. Start Week 1 tasks: docs/QUICK_REFERENCE_PRIORITIES.md"
echo ""
echo "Quick commands:"
echo "  View largest files: cat $REPORT_DIR/largest_files_${TIMESTAMP}.txt"
echo "  View complexity: cat $REPORT_DIR/complexity_baseline_${TIMESTAMP}.txt | less"
echo "  View dead code: cat $REPORT_DIR/dead_code_${TIMESTAMP}.txt | less"
echo ""
echo -e "${YELLOW}Tip: Create a branch for your improvements:${NC}"
echo "  git checkout -b refactor/week1-architecture-audit"
echo ""
