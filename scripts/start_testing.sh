#!/bin/bash
# Bot Testing Guide - Run this before manual testing
# Usage: ./scripts/start_testing.sh

CONTAINER_ID="9ea93d6c31a9"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              🧪 BOT TESTING - READY TO START                 ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo

# Pre-test verification
echo "📋 PRE-TEST VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check container
if docker ps --filter id=$CONTAINER_ID --format "{{.ID}}" | grep -q .; then
    echo "✅ Container: Running"
else
    echo "❌ Container: Not running - Start it first!"
    exit 1
fi

# Check bot process
BOT_PID=$(docker exec $CONTAINER_ID pgrep -f "python.*bot" 2>/dev/null | head -1)
if [ -n "$BOT_PID" ]; then
    echo "✅ Bot Process: Active (PID $BOT_PID)"
else
    echo "❌ Bot Process: Not found!"
    exit 1
fi

# Check web service
if curl -s http://localhost:8060/health > /dev/null 2>&1; then
    echo "✅ Web Service: Responding"
else
    echo "⚠️  Web Service: Not responding"
fi

# Check Category B
CB_CHECK=$(docker exec $CONTAINER_ID python3 -c "import sys; sys.path.insert(0, '/app/src'); from bot.core.category_b_integration import category_b; print('OK')" 2>/dev/null)
if [ "$CB_CHECK" = "OK" ]; then
    echo "✅ Category B: Enabled"
else
    echo "⚠️  Category B: Disabled"
fi

# Get bot info
echo
echo "🤖 BOT INFORMATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
BOT_INFO=$(docker exec $CONTAINER_ID python3 << 'PYEOF' 2>/dev/null
import sys
sys.path.insert(0, '/app/src')
try:
    from pyrogram import Client
    from config.main_config import Config
    import os

    # Get bot username if available
    if hasattr(Config, 'BOT_TOKEN') and Config.BOT_TOKEN:
        username = Config.BOT_TOKEN.split(':')[0]
        print(f"Bot Token: Configured (ID: {username})")

    owner = getattr(Config, 'OWNER_ID', 'Not set')
    print(f"Owner ID: {owner}")

except Exception as e:
    print(f"Error: {e}")
PYEOF
)
echo "$BOT_INFO"

echo
echo "📝 TESTING INSTRUCTIONS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Open Telegram and find your bot"
echo "    (Search for the bot username configured in your setup)"
echo
echo "2️⃣  Start conversation:"
echo "    Send: /start"
echo "    Expected: Welcome message with available commands"
echo
echo "3️⃣  Check Category B:"
echo "    Send: /categoryb"
echo "    Expected: Category B features help text"
echo
echo "4️⃣  Test basic info:"
echo "    Send: /help"
echo "    Send: /stats"
echo
echo "5️⃣  Test download (use small file ~10-50MB):"
echo "    Send: /mirror https://speed.hetzner.de/10MB.bin"
echo "    Expected: Download starts, progress updates appear"
echo
echo "6️⃣  Check queue (admin only):"
echo "    Send: /qstatus"
echo "    Expected: Queue statistics"
echo

echo "🔍 MONITORING WHILE TESTING"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Open a second terminal and run:"
echo
echo "  Watch logs live:"
echo "  docker exec $CONTAINER_ID tail -f /app/data/logs/log.txt"
echo
echo "  Or use monitoring tool:"
echo "  ./scripts/monitor_bot.sh watch"
echo

echo "📊 TEST FILES (Use these for testing)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Small (10MB):  https://speed.hetzner.de/10MB.bin"
echo "Medium (100MB): https://speed.hetzner.de/100MB.bin"
echo "Large (1GB):   https://speed.hetzner.de/1GB.bin"
echo

echo "✅ READY TO TEST!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Open Telegram now and start testing..."
echo
echo "💡 Tip: Keep this terminal open and check logs after each command"
echo
