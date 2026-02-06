#!/bin/bash
# CodeScene Analysis Script
# Analyzes code health and generates actionable insights

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CODESCENE_DIR="$PROJECT_ROOT/.codescene"
REPORT_DIR="$CODESCENE_DIR/reports"
CONFIG_FILE="$CODESCENE_DIR/config.yml"

# Create directories
mkdir -p "$REPORT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    CodeScene-Style Analysis - MLTB Code Health${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""
echo "Using custom Python analyzers (CodeScene-inspired metrics)"
echo ""

# Navigate to project root
cd "$PROJECT_ROOT"

# Analysis type
ANALYSIS_TYPE="${1:-full}"

echo -e "${BLUE}📊 Running CodeScene Analysis...${NC}"
echo "Project: Mirror Leech Telegram Bot"
echo "Type: $ANALYSIS_TYPE"
echo "Config: $CONFIG_FILE"
echo ""

# Timestamp for report
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="$REPORT_DIR/analysis_$TIMESTAMP.json"
HTML_REPORT="$REPORT_DIR/analysis_$TIMESTAMP.html"
SUMMARY_FILE="$REPORT_DIR/summary_$TIMESTAMP.txt"

case "$ANALYSIS_TYPE" in
    "full")
        echo -e "${BLUE}Running full analysis (all metrics)...${NC}"
        
        # Run complexity analysis
        echo ""
        echo -e "${YELLOW}1️⃣  Analyzing code complexity...${NC}"
        python3 "$SCRIPT_DIR/analyze_complexity.py" > "$REPORT_DIR/complexity_$TIMESTAMP.json" 2>&1 || true
        
        # Run hotspot analysis
        echo -e "${YELLOW}2️⃣  Analyzing hotspots (frequently changed complex files)...${NC}"
        python3 "$SCRIPT_DIR/analyze_hotspots.py" > "$REPORT_DIR/hotspots_$TIMESTAMP.json" 2>&1 || true
        
        # Run code health analysis
        echo -e "${YELLOW}3️⃣  Analyzing code health...${NC}"
        python3 "$SCRIPT_DIR/analyze_code_health.py" > "$REPORT_DIR/health_$TIMESTAMP.json" 2>&1 || true
        
        # Run technical debt analysis
        echo -e "${YELLOW}4️⃣  Analyzing technical debt...${NC}"
        python3 "$SCRIPT_DIR/analyze_tech_debt.py" > "$REPORT_DIR/tech_debt_$TIMESTAMP.json" 2>&1 || true
        
        ;;
        
    "quick")
        echo -e "${BLUE}Running quick analysis (complexity only)...${NC}"
        python3 "$SCRIPT_DIR/analyze_complexity.py"
        ;;
        
    "hotspots")
        echo -e "${BLUE}Running hotspot analysis...${NC}"
        python3 "$SCRIPT_DIR/analyze_hotspots.py"
        ;;
        
    *)
        echo -e "${RED}❌ Unknown analysis type: $ANALYSIS_TYPE${NC}"
        echo "Usage: $0 [full|quick|hotspots]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ CodeScene Analysis Complete${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""
echo "Reports saved to:"
echo "  📁 $REPORT_DIR/"
echo ""
echo "View latest reports:"
echo "  cat $REPORT_DIR/complexity_*.json | tail -1"
echo "  cat $REPORT_DIR/hotspots_*.json | tail -1"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  1. Review complexity hotspots"
echo "  2. Refactor high-complexity functions"
echo "  3. Run tests after changes"
echo "  4. Re-run analysis to track improvements"
echo ""
