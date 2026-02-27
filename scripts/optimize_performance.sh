#!/bin/bash
# Performance Optimization Script
# Applies recommended settings for optimal bot performance

CONTAINER_ID="9ea93d6c31a9"
BOT_DIR="/home/kali/mirror-leech-telegram-bot"

echo "⚡ Bot Performance Optimization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 1. Measure current baseline
echo "📊 Step 1: Measuring current performance..."
echo "   Container stats:"
docker stats $CONTAINER_ID --no-stream --format "   CPU: {{.CPUPerc}} | Memory: {{.MemUsage}} | Network: {{.NetIO}}"

echo
echo "   Bot processes:"
docker exec $CONTAINER_ID ps aux | grep python | grep -v grep | wc -l | xargs echo "   Python processes:"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 2. Database optimization
echo
echo "📋 Step 2: Database optimization..."
docker exec $CONTAINER_ID python3 << 'PYEOF'
import sys
sys.path.insert(0, '/app/src')

try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    
    client = MongoClient()
    db = client['bot_db']
    
    print("   Creating MongoDB indexes...")
    
    # Downloads collection
    if 'downloads' in db.list_collection_names():
        db.downloads.create_index([('user_id', ASCENDING)])
        db.downloads.create_index([('timestamp', DESCENDING)])
        db.downloads.create_index([('status', ASCENDING)])
        print("   ✅ Downloads indexes created")
    
    # Users collection
    if 'users' in db.list_collection_names():
        db.users.create_index([('user_id', ASCENDING)])
        db.users.create_index([('last_active', DESCENDING)])
        print("   ✅ Users indexes created")
    
    client.close()
    print("   ✅ Database optimization complete")
    
except Exception as e:
    print(f"   ⚠️  MongoDB not available or error: {e}")
PYEOF

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 3. Redis optimization
echo
echo "📦 Step 3: Redis cache optimization..."
docker exec $CONTAINER_ID redis-cli CONFIG SET maxmemory 512mb 2>/dev/null && echo "   ✅ Redis max memory: 512MB" || echo "   ⚠️  Redis not available"
docker exec $CONTAINER_ID redis-cli CONFIG SET maxmemory-policy allkeys-lru 2>/dev/null && echo "   ✅ Redis eviction: LRU" || echo "   ⚠️  Redis config skipped"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 4. System optimization
echo
echo "🔧 Step 4: System optimizations..."

# Clear Python cache
echo "   Clearing Python cache..."
docker exec $CONTAINER_ID find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
docker exec $CONTAINER_ID find /app -type f -name "*.pyc" -delete 2>/dev/null
echo "   ✅ Python cache cleared"

# Clear old logs (keep last 1000 lines)
echo "   Rotating logs..."
docker exec $CONTAINER_ID sh -c 'tail -1000 /app/data/logs/log.txt > /tmp/log_temp.txt && mv /tmp/log_temp.txt /app/data/logs/log.txt' 2>/dev/null && echo "   ✅ Logs rotated" || echo "   ⚠️  Log rotation skipped"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 5. Performance report
echo
echo "📈 Step 5: Performance report..."
echo

# Category B status
CB_STATUS=$(docker exec $CONTAINER_ID python3 -c "
import sys
sys.path.insert(0, '/app/src')
from bot.core.category_b_integration import category_b
print(f'Circuit Breakers: {category_b.telegram_breaker.state.name}')
print(f'Telegram failures: {category_b.telegram_breaker.failure_count}')
print(f'GDrive failures: {category_b.gdrive_breaker.failure_count}')
print(f'Aria2 failures: {category_b.aria2_breaker.failure_count}')
" 2>/dev/null)

echo "   Category B Status:"
echo "$CB_STATUS" | sed 's/^/      /'

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "✅ Performance optimization complete!"
echo
echo "📊 Recommendations:"
echo "   1. Monitor for next 24 hours: ./scripts/monitor_bot.sh watch"
echo "   2. Check error rates: ./scripts/view_logs.sh 200 error"
echo "   3. Review tuning guide: cat CONFIGURATION_TUNING.md"
echo
echo "⚡ For further optimization, see CONFIGURATION_TUNING.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
