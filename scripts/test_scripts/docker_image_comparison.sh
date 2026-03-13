#!/bin/bash
# ============================================================================
# Docker Image Size Comparison Script
# Compares original vs optimized Docker images
# ============================================================================

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     Docker Image Size Comparison & Build Benchmark            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to format bytes to human readable
format_bytes() {
    local bytes=$1
    if [ "$bytes" -lt 1024 ]; then
        echo "${bytes}B"
    elif [ "$bytes" -lt 1048576 ]; then
        echo "$(( bytes / 1024 ))KB"
    elif [ "$bytes" -lt 1073741824 ]; then
        echo "$(( bytes / 1048576 ))MB"
    else
        printf "%.2fGB\n" "$(echo "scale=2; $bytes / 1073741824" | bc)"
    fi
}

# Function to calculate percentage reduction
calc_reduction() {
    local original=$1
    local optimized=$2
    echo "scale=1; (($original - $optimized) / $original) * 100" | bc
}

# Build images
echo "${BLUE}📦 Building Docker images...${NC}"
echo ""

echo "${YELLOW}1/4 Building: Original Dockerfile${NC}"
start_orig=$(date +%s)
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile -t mltb-test:original . > /tmp/build_original.log 2>&1 || {
    echo "${RED}❌ Original build failed. See /tmp/build_original.log${NC}"
}
end_orig=$(date +%s)
build_time_orig=$((end_orig - start_orig))

echo "${YELLOW}2/4 Building: Optimized Dockerfile${NC}"
start_opt=$(date +%s)
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.optimized -t mltb-test:optimized . > /tmp/build_optimized.log 2>&1 || {
    echo "${RED}❌ Optimized build failed. See /tmp/build_optimized.log${NC}"
}
end_opt=$(date +%s)
build_time_opt=$((end_opt - start_opt))

echo "${YELLOW}3/4 Building: No-JDownloader Dockerfile${NC}"
start_nojd=$(date +%s)
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.no-jdownloader -t mltb-test:no-jd . > /tmp/build_nojd.log 2>&1 || {
    echo "${RED}❌ No-JD build failed. See /tmp/build_nojd.log${NC}"
}
end_nojd=$(date +%s)
build_time_nojd=$((end_nojd - start_nojd))

echo "${YELLOW}4/4 Building: Alpine Dockerfile${NC}"
start_alpine=$(date +%s)
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.alpine -t mltb-test:alpine . > /tmp/build_alpine.log 2>&1 || {
    echo "${RED}❌ Alpine build failed (this is optional). See /tmp/build_alpine.log${NC}"
}
end_alpine=$(date +%s)
build_time_alpine=$((end_alpine - start_alpine))

echo ""
echo "${GREEN}✅ Builds complete!${NC}"
echo ""

# Get image sizes
echo "${BLUE}📊 Analyzing image sizes...${NC}"
echo ""

size_original=$(docker images mltb-test:original --format "{{.Size}}" | head -1)
size_optimized=$(docker images mltb-test:optimized --format "{{.Size}}" | head -1)
size_nojd=$(docker images mltb-test:no-jd --format "{{.Size}}" | head -1)
size_alpine=$(docker images mltb-test:alpine --format "{{.Size}}" | head -1)

# Convert to bytes for calculation (approximate)
size_original_mb=$(echo "$size_original" | sed 's/GB/*1024/;s/MB/*1/;s/KB*0.001/' | sed 's/[^0-9.*]//g' | bc)
size_optimized_mb=$(echo "$size_optimized" | sed 's/GB/*1024/;s/MB/*1/;s/KB*0.001/' | sed 's/[^0-9.*]//g' | bc)
size_nojd_mb=$(echo "$size_nojd" | sed 's/GB/*1024/;s/MB/*1/;s/KB*0.001/' | sed 's/[^0-9.*]//g' | bc)
size_alpine_mb=$(echo "$size_alpine" | sed 's/GB/*1024/;s/MB/*1/;s/KB*0.001/' | sed 's/[^0-9.*]//g' | bc)

# Calculate reductions
reduction_opt=$(calc_reduction $size_original_mb $size_optimized_mb)
reduction_nojd=$(calc_reduction $size_original_mb $size_nojd_mb)
reduction_alpine=$(calc_reduction $size_original_mb $size_alpine_mb)

# Print results table
echo "┌────────────────────────────┬─────────────┬──────────────┬──────────────┐"
echo "│ Variant                    │ Size        │ Reduction    │ Build Time   │"
echo "├────────────────────────────┼─────────────┼──────────────┼──────────────┤"
printf "│ %-26s │ %-11s │ %-12s │ %10ss │\n" "Original" "$size_original" "0%" "$build_time_orig"
printf "│ %-26s │ ${GREEN}%-11s${NC} │ ${GREEN}%-12s${NC} │ %10ss │\n" "Optimized (Recommended)" "$size_optimized" "${reduction_opt}%" "$build_time_opt"
printf "│ %-26s │ ${GREEN}%-11s${NC} │ ${GREEN}%-12s${NC} │ %10ss │\n" "No-JDownloader" "$size_nojd" "${reduction_nojd}%" "$build_time_nojd"
printf "│ %-26s │ ${GREEN}%-11s${NC} │ ${GREEN}%-12s${NC} │ %10ss │\n" "Alpine" "$size_alpine" "${reduction_alpine}%" "$build_time_alpine"
echo "└────────────────────────────┴─────────────┴──────────────┴──────────────┘"
echo ""

# Savings analysis
echo "${BLUE}💰 Deployment Cost Savings (AWS Example):${NC}"
echo ""
echo "Container Registry Storage (ECR):"
echo "  Original:  $size_original × $0.10/GB/month"
echo "  Optimized: $size_optimized × $0.10/GB/month"
echo ""
echo "Image Pull Bandwidth (10 deployments/day × 30 days):"
original_transfer=$(echo "scale=2; $size_original_mb * 10 * 30 / 1024" | bc)
optimized_transfer=$(echo "scale=2; $size_optimized_mb * 10 * 30 / 1024" | bc)
echo "  Original:  ${original_transfer}GB/month"
echo "  Optimized: ${optimized_transfer}GB/month"
echo ""

# Layer analysis
echo "${BLUE}🔍 Layer Analysis:${NC}"
echo ""
echo "${YELLOW}Original Image Layers:${NC}"
docker history mltb-test:original --format "{{.Size}}\t{{.CreatedBy}}" | head -10
echo ""
echo "${YELLOW}Optimized Image Layers:${NC}"
docker history mltb-test:optimized --format "{{.Size}}\t{{.CreatedBy}}" | head -10
echo ""

# Recommendations
echo "${BLUE}💡 Recommendations:${NC}"
echo ""
if (( $(echo "$reduction_opt > 70" | bc -l) )); then
    echo "  ${GREEN}✓${NC} Optimized build achieved >70% reduction - Deploy to production!"
else
    echo "  ${YELLOW}⚠${NC} Reduction less than expected. Review build logs."
fi

if (( build_time_opt > build_time_orig * 2 )); then
    echo "  ${YELLOW}⚠${NC} Build time increased significantly. Consider caching strategies."
else
    echo "  ${GREEN}✓${NC} Build time acceptable"
fi

echo ""
echo "${GREEN}🎉 Comparison complete!${NC}"
echo ""
echo "Build logs saved to /tmp/build_*.log"
echo "To use optimized image: docker-compose -f deployment/compose/docker-compose.optimized.yml up -d"
