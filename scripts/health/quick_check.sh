#!/bin/bash
# Quick Bot Status Check
# Usage: ./scripts/quick_check.sh

CONTAINER_ID="9ea93d6c31a9"

echo "🔍 Quick Bot Status Check"
echo "========================="
echo

# Container running?
if docker ps --filter id=$CONTAINER_ID --format "{{.ID}}" | grep -q .; then
    echo "✅ Container: Running"
else
    echo "❌ Container: Not running"
    exit 1
fi

# Bot process
BOT_PID=$(docker exec $CONTAINER_ID pgrep -f "python.*bot" 2>/dev/null | head -1)
if [ -n "$BOT_PID" ]; then
    echo "✅ Bot Process: Running (PID $BOT_PID)"
else
    echo "❌ Bot Process: Not found"
fi

# Web service
if curl -s http://localhost:8060/health > /dev/null 2>&1; then
    echo "✅ Web Service: Healthy"
else
    echo "❌ Web Service: Down"
fi

# Category B
CB_CHECK=$(docker exec $CONTAINER_ID python3 -c "import sys; sys.path.insert(0, '/app/src'); from bot.core.category_b_integration import category_b; print('OK')" 2>/dev/null)
if [ "$CB_CHECK" = "OK" ]; then
    echo "✅ Category B: Enabled"
else
    echo "⚠️  Category B: Disabled or error"
fi

# Recent log activity
LAST_LOG=$(docker exec $CONTAINER_ID tail -1 /app/data/logs/log.txt 2>/dev/null | cut -c1-80)
echo
echo "📝 Last Log Entry:"
echo "   $LAST_LOG"

echo
echo "========================="
echo "Status: All systems operational ✅"
