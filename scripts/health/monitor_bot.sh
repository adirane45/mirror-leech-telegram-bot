#!/bin/bash
# Bot Health Monitoring Script
# Usage: ./scripts/monitor_bot.sh [watch]

CONTAINER_ID="9ea93d6c31a9"
WATCH_MODE=${1:-once}

monitor_health() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🤖 BOT HEALTH MONITORING - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    
    # Container Status
    echo "📦 CONTAINER STATUS"
    docker ps --filter id=$CONTAINER_ID --format "   Status: {{.Status}}" 2>/dev/null || echo "   ❌ Container not running"
    echo
    
    # Web Health
    echo "🌐 WEB SERVICE"
    HEALTH=$(curl -s http://localhost:8060/health 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   ✅ Web API: $(echo $HEALTH | grep -o '"status":"[^"]*"' | cut -d'"' -f4)"
        echo "   📊 CPU: $(echo $HEALTH | grep -o '"cpu_percent":[0-9.]*' | cut -d':' -f2)%"
        echo "   💾 Memory: $(echo $HEALTH | grep -o '"memory_percent":[0-9.]*' | cut -d':' -f2)%"
        echo "   📀 Disk: $(echo $HEALTH | grep -o '"disk_percent":[0-9.]*' | cut -d':' -f2)%"
    else
        echo "   ❌ Web API: Unreachable"
    fi
    echo
    
    # Category B Status
    echo "⚡ CATEGORY B FEATURES"
    CB_STATUS=$(docker exec $CONTAINER_ID python3 -c "
import sys
sys.path.insert(0, '/app/src')
try:
    from bot.core.category_b_integration import category_b
    print('✅ Initialized')
    print(f'CB_STATE:{category_b.telegram_breaker.state.name}')
    print(f'TG_FAIL:{category_b.telegram_breaker.failure_count}/{category_b.telegram_breaker.failure_threshold}')
    print(f'GD_FAIL:{category_b.gdrive_breaker.failure_count}/{category_b.gdrive_breaker.failure_threshold}')
    print(f'AR_FAIL:{category_b.aria2_breaker.failure_count}/{category_b.aria2_breaker.failure_threshold}')
except Exception as e:
    print('❌ Not initialized')
    print(f'ERROR:{e}')
" 2>/dev/null)
    
    if echo "$CB_STATUS" | grep -q "✅"; then
        echo "   Status: $(echo "$CB_STATUS" | head -1)"
        CB_STATE=$(echo "$CB_STATUS" | grep "CB_STATE:" | cut -d: -f2)
        echo "   Circuit Breakers: $CB_STATE"
        echo "   └─ Telegram: $(echo "$CB_STATUS" | grep "TG_FAIL:" | cut -d: -f2)"
        echo "   └─ GDrive: $(echo "$CB_STATUS" | grep "GD_FAIL:" | cut -d: -f2)"
        echo "   └─ Aria2: $(echo "$CB_STATUS" | grep "AR_FAIL:" | cut -d: -f2)"
    else
        echo "   Status: ❌ Disabled or error"
    fi
    echo
    
    # Recent Errors
    echo "⚠️  RECENT ERRORS (Last 5)"
    ERROR_COUNT=$(docker exec $CONTAINER_ID grep -c "ERROR\|CRITICAL" /app/data/logs/log.txt 2>/dev/null || echo 0)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        docker exec $CONTAINER_ID grep "ERROR\|CRITICAL" /app/data/logs/log.txt 2>/dev/null | tail -5 | while read line; do
            echo "   $(echo $line | cut -c1-100)"
        done
    else
        echo "   ✅ No errors"
    fi
    echo
    
    # Process Info
    echo "🔧 PROCESSES"
    docker exec $CONTAINER_ID ps aux 2>/dev/null | grep -E "(PID|python)" | grep -v grep | head -4 | while read line; do
        echo "   $line"
    done
    echo
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

if [ "$WATCH_MODE" = "watch" ]; then
    echo "👁️  Watching bot health (Ctrl+C to stop)..."
    echo
    while true; do
        clear
        monitor_health
        echo "Refreshing in 10 seconds..."
        sleep 10
    done
else
    monitor_health
fi
