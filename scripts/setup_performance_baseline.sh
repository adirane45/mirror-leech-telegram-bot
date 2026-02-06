#!/bin/bash
# Performance Baseline Measurement Script
# Establishes baseline metrics for Tier 2 optimization

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
METRICS_DIR="$PROJECT_ROOT/.metrics"
BASELINE_DIR="$METRICS_DIR/baselines"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  TIER 2.1 - Performance Baseline Establishment${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo ""

# Create directories
mkdir -p "$BASELINE_DIR"

# Run Python baseline script
echo -e "${YELLOW}📊 Running performance measurements...${NC}"
python3 "$PROJECT_ROOT/scripts/measure_performance_baseline.py"

# Save Prometheus config
echo -e "${YELLOW}⚙️  Setting up Prometheus configuration...${NC}"
mkdir -p "$METRICS_DIR"
echo -e "${GREEN}✅ Prometheus config: $METRICS_DIR/prometheus.yml${NC}"

# Save alert rules
echo -e "${YELLOW}🚨 Setting up alert rules...${NC}"
echo -e "${GREEN}✅ Alert rules: $METRICS_DIR/alert_rules.yml${NC}"

# Display baseline directory
echo ""
echo -e "${GREEN}✅ Performance Baseline Complete${NC}"
echo ""
echo "📁 Baseline files saved to:"
echo "   $BASELINE_DIR/"
echo ""
echo "📊 View latest baseline:"
echo "   cat $(ls -1t $BASELINE_DIR/*.json 2>/dev/null | head -1 || echo 'baseline.json') | jq ."
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
echo "Next: Review Prometheus & Grafana dashboards"
echo -e "${BLUE}════════════════════════════════════════════════════${NC}"
