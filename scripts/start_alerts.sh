#!/bin/bash
# Telegram Alert System for Bot Errors
# Sends notifications to admin when issues occur

CONTAINER_ID="9ea93d6c31a9"
LOG_FILE="/app/data/logs/log.txt"
ALERT_CHAT_ID="${1:-YOUR_TELEGRAM_CHAT_ID}"  # Pass as argument or set here
CHECK_INTERVAL=300  # 5 minutes

if [  "$ALERT_CHAT_ID" = "YOUR_TELEGRAM_CHAT_ID" ]; then
    echo "⚠️  Please provide your Telegram chat ID"
    echo "Usage: $0 <chat_id>"
    echo
    echo "To get your chat ID:"
    echo "  1. Send /start to your bot"
    echo "  2. Check logs: docker exec $CONTAINER_ID grep 'chat_id' $LOG_FILE | head -1"
    echo
    exit 1
fi

echo "🔔 Starting alert monitoring system..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Alert Chat ID: $ALERT_CHAT_ID"
echo "   Check interval: ${CHECK_INTERVAL}s"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start alert monitoring in background
nohup bash -c "
LAST_CHECK=\$(date +%s)

while true; do
    # Check for critical errors in last check period
    ERRORS=\$(docker exec $CONTAINER_ID tail -100 $LOG_FILE 2>/dev/null | grep -E 'CRITICAL|ERROR' | tail -5)

    if [ ! -z \"\$ERRORS\" ]; then
        # Circuit breaker state
        CB_STATE=\$(docker exec $CONTAINER_ID python3 -c \"
import sys
sys.path.insert(0, '/app/src')
from bot.core.category_b_integration import category_b
print(category_b.telegram_breaker.state.name)
\" 2>/dev/null)

        # Send alert via bot
        docker exec $CONTAINER_ID python3 << 'PYEOF'
import sys
sys.path.insert(0, '/app/src')
from pyrogram import Client
from config.main_config import Config
import asyncio

async def send_alert():
    app = Client('alert_bot', api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)
    await app.start()

    message = '''
⚠️ **Bot Alert**

Recent errors detected in logs.
Circuit Breakers: $CB_STATE

Check logs: \`docker exec ${CONTAINER_ID} tail -50 ${LOG_FILE}\`
'''

    await app.send_message($ALERT_CHAT_ID, message)
    await app.stop()

asyncio.run(send_alert())
PYEOF
    fi

    # Memory check
    MEM_PERCENT=\$(docker exec $CONTAINER_ID python3 -c 'import psutil; print(psutil.virtual_memory().percent)' 2>/dev/null)
    if [ ! -z \"\$MEM_PERCENT\" ]; then
        if (( \$(echo \"\$MEM_PERCENT > 85\" | bc -l) )); then
            echo \"⚠️ High memory usage: \${MEM_PERCENT}%\"
        fi
    fi

    sleep $CHECK_INTERVAL
done
" >> /tmp/bot_alerts.log 2>&1 &

ALERT_PID=$!

echo "✅ Alert system started (PID: $ALERT_PID)"
echo
echo "📝 Alert log: /tmp/bot_alerts.log"
echo "🛑 To stop: kill $ALERT_PID"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
