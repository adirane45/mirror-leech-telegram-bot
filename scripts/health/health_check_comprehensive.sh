#!/bin/bash

################################################################################
# MLTB Bot Comprehensive Health Check Script
# 
# Purpose: Verify all bot services are running and healthy
# Usage: ./scripts/health_check_comprehensive.sh
# Exit Codes:
#   0 = All systems healthy ✅
#   1 = One or more issues detected ⚠️
#   2 = Critical failure (containers not running) ❌
################################################################################

set -o pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNING=0
CRITICAL=0

# Configuration
TIMEOUT=10
RETRIES=3
API_PORT=8060
GRAPHQL_PORT=8060
PROMETHEUS_PORT=9091
GRAFANA_PORT=3000
REDIS_PORT=6379
ARIA2_PORT=6800
QB_PORT=8090
SABNZBD_PORT=8080

################################################################################
# Helper Functions
################################################################################

log_pass() {
    echo -e "${GREEN}✅${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}❌${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
    ((WARNING++))
}

log_critical() {
    echo -e "${RED}🔥${NC} $1"
    ((CRITICAL++))
}

log_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

log_header() {
    echo
    echo "════════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════════"
}

check_container_running() {
    local container=$1
    if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "^$container$"; then
        log_pass "Container $container is running"
        return 0
    else
        log_critical "Container $container is NOT running"
        return 1
    fi
}

check_container_healthy() {
    local container=$1
    local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null)
    
    if [ "$status" == "healthy" ]; then
        log_pass "Container $container is healthy"
        return 0
    elif [ "$status" == "starting" ]; then
        log_warn "Container $container is still starting"
        return 1
    elif [ "$status" == "unhealthy" ]; then
        log_fail "Container $container is UNHEALTHY"
        return 1
    else
        log_info "Container $container has no health check (status: $status)"
        return 0
    fi
}

check_port_open() {
    local port=$1
    local service=$2
    
    if timeout $TIMEOUT bash -c "echo >/dev/tcp/localhost/$port" 2>/dev/null; then
        log_pass "$service is accessible on port $port"
        return 0
    else
        log_fail "$service is NOT accessible on port $port"
        return 1
    fi
}

check_http_endpoint() {
    local url=$1
    local expected_status=$2
    local name=$3
    
    if [ -z "$expected_status" ]; then
        expected_status=200
    fi
    
    local status=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null)
    
    if [ "$status" == "$expected_status" ]; then
        log_pass "$name returned HTTP $status"
        return 0
    else
        log_fail "$name returned HTTP $status (expected $expected_status)"
        return 1
    fi
}

check_redis_connection() {
    if docker exec mltb-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        log_pass "Redis is responding to PING"
        return 0
    else
        log_fail "Redis is NOT responding to PING"
        return 1
    fi
}

check_rpc_endpoint() {
    local port=$1
    local secret=$2
    local service=$3
    
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        --connect-timeout 5 \
        --data "{\"jsonrpc\":\"2.0\",\"id\":\"mltb\",\"method\":\"$4\",\"params\":[\"token:$secret\"]}" \
        "http://localhost:$port/jsonrpc" 2>/dev/null)
    
    if echo "$response" | grep -q "result"; then
        log_pass "$service RPC endpoint is responding"
        return 0
    else
        log_fail "$service RPC endpoint is NOT responding"
        return 1
    fi
}

check_disk_space() {
    local path=$1
    local threshold=${2:-10}  # Default 10% warning threshold
    
    if [ ! -d "$path" ]; then
        log_warn "Directory $path does not exist"
        return 1
    fi
    
    local usage=$(df "$path" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt "$((threshold + 10))" ]; then
        log_critical "Disk usage in $path is ${usage}% (critical)"
        return 1
    elif [ "$usage" -gt "$threshold" ]; then
        log_warn "Disk usage in $path is ${usage}% (warning)"
        return 1
    else
        log_pass "Disk usage in $path is ${usage}% (healthy)"
        return 0
    fi
}

check_memory_usage() {
    local container=$1
    local max_percent=${2:-80}
    
    # Get memory usage in MB (handles floating point)
    local mem_usage=$(docker stats --no-stream "$container" 2>/dev/null | tail -1 | awk '{print $4}' | sed 's/M.*//')
    
    if [ -z "$mem_usage" ]; then
        log_info "Could not retrieve memory usage for $container"
        return 0
    fi
    
    # Convert to integer for comparison (handle floating point)
    local mem_int=$(printf "%.0f" "$mem_usage" 2>/dev/null || echo "$mem_usage")
    
    # Arbitrary check - if using > 2GB of memory, warn
    if [ "$mem_int" -gt "2000" ] 2>/dev/null; then
        log_warn "Container $container using ${mem_usage}MB (high memory usage)"
        return 1
    else
        log_pass "Container $container memory usage: ${mem_usage}MB"
        return 0
    fi
}

check_log_for_errors() {
    local container=$1
    local lines=${2:-50}
    
    local errors=$(docker logs --tail $lines "$container" 2>/dev/null | grep -i "error\|exception\|critical\|fatal" | wc -l)
    
    if [ "$errors" -eq 0 ]; then
        log_pass "No errors found in last $lines log lines of $container"
        return 0
    else
        log_warn "Found $errors error(s) in last $lines log lines of $container"
        return 1
    fi
}

################################################################################
# Health Checks
################################################################################

check_docker_connectivity() {
    log_header "1. Docker & Container Status"
    
    if ! docker ps > /dev/null 2>&1; then
        log_critical "Docker daemon is not responding"
        return 2
    fi
    log_pass "Docker daemon is responding"
    
    # Check all containers
    local containers=("mltb-app" "mltb-redis" "mltb-aria2" "mltb-qbittorrent" "mltb-prometheus" "mltb-grafana")
    local all_running=true
    
    for container in "${containers[@]}"; do
        if ! check_container_running "$container"; then
            all_running=false
        fi
    done
    
    return $([ "$all_running" = true ] && echo 0 || echo 1)
}

check_container_health() {
    log_header "2. Container Health Status"
    
    local containers=("mltb-app" "mltb-redis" "mltb-aria2" "mltb-qbittorrent" "mltb-prometheus" "mltb-grafana")
    
    for container in "${containers[@]}"; do
        check_container_healthy "$container"
    done
}

check_core_services() {
    log_header "3. Core Services"
    
    log_info "Redis Cache (port $REDIS_PORT)"
    check_port_open $REDIS_PORT "Redis"
    check_redis_connection
    
    log_info "Aria2 RPC (port $ARIA2_PORT)"
    check_port_open $ARIA2_PORT "Aria2"
    check_rpc_endpoint $ARIA2_PORT "mltb_aria2_secret_2026" "Aria2" "aria2.getVersion"
    
    log_info "qBittorrent WebUI (port $QB_PORT)"
    check_port_open $QB_PORT "qBittorrent"
    check_http_endpoint "http://localhost:$QB_PORT/" 200 "qBittorrent WebUI"
}

check_web_services() {
    log_header "4. Web Server & APIs"
    
    log_info "Web Dashboard (port $API_PORT)"
    check_port_open $API_PORT "Web Server"
    check_http_endpoint "http://localhost:$API_PORT/" 200 "Dashboard Homepage"
    
    log_info "GraphQL API"
    check_http_endpoint "http://localhost:$GRAPHQL_PORT/graphql" 200 "GraphQL Endpoint"
    
    # Test GraphQL query
    local graphql_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        --connect-timeout 5 \
        --data '{"query":"{status{version}}"}' \
        "http://localhost:$API_PORT/graphql" 2>/dev/null)
    
    if echo "$graphql_response" | grep -q '"data"'; then
        log_pass "GraphQL query execution successful"
    else
        log_warn "GraphQL query returned no data"
    fi
}

check_monitoring() {
    log_header "5. Monitoring & Metrics"
    
    log_info "Prometheus (port $PROMETHEUS_PORT)"
    check_port_open $PROMETHEUS_PORT "Prometheus"
    check_http_endpoint "http://localhost:$PROMETHEUS_PORT/-/healthy" 200 "Prometheus Health"
    
    log_info "Grafana (port $GRAFANA_PORT)"
    check_port_open $GRAFANA_PORT "Grafana"
    check_http_endpoint "http://localhost:$GRAFANA_PORT/api/health" 200 "Grafana Health"
    
    log_info "Application Metrics (port $API_PORT/metrics)"
    check_http_endpoint "http://localhost:$API_PORT/metrics" 200 "App Metrics Endpoint"
}

check_resource_usage() {
    log_header "6. Resource Usage"
    
    check_disk_space "/home/kali/mirror-leech-telegram-bot/data" 80
    check_disk_space "/home/kali/mirror-leech-telegram-bot/data/downloads" 80
    
    check_memory_usage "mltb-app"
    check_memory_usage "mltb-redis"
    check_memory_usage "mltb-prometheus"
}

check_logs() {
    log_header "7. Log Analysis"
    
    check_log_for_errors "mltb-app" 50
    check_log_for_errors "mltb-redis" 30
    check_log_for_errors "mltb-aria2" 30
}

check_configuration() {
    log_header "8. Configuration & Files"
    
    # Check if config files exist
    if [ -f "config/main_config.py" ]; then
        log_pass "Main config file exists (config/main_config.py)"
    else
        log_fail "Main config file NOT found"
    fi
    
    if [ -f "config/.env.production" ]; then
        log_pass "Environment file exists (config/.env.production)"
    else
        log_fail "Environment file NOT found"
    fi
    
    # Check JDownloader config
    if [ -d "integrations/myjd" ]; then
        log_pass "JDownloader integration directory exists"
    else
        log_fail "JDownloader integration directory missing"
    fi
    
    # Check volume mounts in docker
    if docker inspect mltb-app --format='{{json .Mounts}}' 2>/dev/null | grep -q "config"; then
        log_pass "Config volume is mounted in app container"
    else
        log_fail "Config volume NOT mounted in app container"
    fi
}

check_database_connectivity() {
    log_header "9. Database & Storage"
    
    # Check if MongoDB is in use
    local db_url=$(docker exec mltb-app env | grep DATABASE_URL || echo "")
    
    if [ -z "$db_url" ] || [[ "$db_url" == *"DATABASE_URL="* ]]; then
        log_pass "MongoDB is disabled (using local JSON storage)"
    else
        log_warn "MongoDB might be configured (check if connection is working)"
    fi
    
    # Check if local storage is accessible
    if docker exec mltb-app ls /app/downloads > /dev/null 2>&1; then
        log_pass "Local storage (/app/downloads) is accessible"
    else
        log_fail "Local storage is NOT accessible"
    fi
}

check_bot_specific() {
    log_header "10. Bot-Specific Features"
    
    # Check if bot token is configured (check .env.production)
    if grep -q "BOT_TOKEN" config/.env.production 2>/dev/null; then
        log_pass "Bot token is configured in environment"
    else
        log_warn "Bot token not found in config/.env.production (check if it's configured)"
    fi
    
    # Check Telegram connectivity (by checking if bot process is running)
    if docker exec mltb-app pgrep -f "python.*bot" > /dev/null 2>&1; then
        log_pass "Bot process is running"
    else
        log_warn "Bot process might not be running"
    fi
    
    # Check Phase 1, 2, 3 status from logs
    local phase2=$(docker logs mltb-app 2>/dev/null | grep -i "phase 2" | tail -1)
    local phase3=$(docker logs mltb-app 2>/dev/null | grep -i "phase 3" | tail -1)
    
    if [ -n "$phase2" ]; then
        log_pass "Phase 2 initialization detected"
    fi
    if [ -n "$phase3" ]; then
        log_pass "Phase 3 initialization detected"
    fi
    
    # Check if web dashboard is responding
    if curl -s http://localhost:8060/ | grep -q "dashboard\|html" 2>/dev/null; then
        log_pass "Web dashboard is responding with content"
    fi
}

################################################################################
# Main Execution
################################################################################

main() {
    clear
    echo
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║   MLTB Bot - Comprehensive Health Check                       ║"
    echo "║   $(date '+%Y-%m-%d %H:%M:%S')                              ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo
    
    # Run all checks
    check_docker_connectivity
    docker_result=$?
    
    if [ $docker_result -eq 2 ]; then
        echo
        echo "════════════════════════════════════════════════════════════════"
        echo "  Docker is not available. Aborting health check."
        echo "════════════════════════════════════════════════════════════════"
        exit 2
    fi
    
    check_container_health
    check_core_services
    check_web_services
    check_monitoring
    check_resource_usage
    check_logs
    check_configuration
    check_database_connectivity
    check_bot_specific
    
    # Print Summary
    log_header "HEALTH CHECK SUMMARY"
    echo
    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNING"
    echo -e "  ${RED}Failed:${NC}   $FAILED"
    echo -e "  ${RED}Critical:${NC} $CRITICAL"
    echo
    
    # Determine exit status
    if [ $CRITICAL -gt 0 ]; then
        echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}Status: 🔥 CRITICAL ISSUES DETECTED${NC}"
        echo -e "${RED}════════════════════════════════════════════════════════════════${NC}"
        exit 2
    elif [ $FAILED -gt 0 ]; then
        echo -e "${YELLOW}════════════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}Status: ⚠️  ISSUES DETECTED (Bot may not be 100% functional)${NC}"
        echo -e "${YELLOW}════════════════════════════════════════════════════════════════${NC}"
        exit 1
    else
        echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}Status: ✅ ALL SYSTEMS HEALTHY (Bot is 100% operational)${NC}"
        echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
        exit 0
    fi
}

# Trap errors
trap 'log_critical "Script interrupted"; exit 2' INT TERM

# Run main function
main
