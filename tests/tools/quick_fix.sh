#!/bin/bash
# Auto-Fix Script for Mirror/Leech/YT-DLP Commands Not Working

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        TELEGRAM BOT COMMAND FIX - AUTO REPAIR              ║"
echo "║    Fixing: /mirror, /leech, /ytdl not working             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Check if bot is running
echo "🔍 Checking bot status..."
if ! docker ps | grep -q mltb-app; then
    echo "❌ Bot is not running!"
    echo "   Starting bot..."
    docker-compose up -d app
    sleep 10
fi
echo "✅ Bot is running"
echo ""

# Step 2: Apply the runtime fix
echo "🔧 Applying authorization fix..."
docker exec mltb-app python3 << 'PYTHON_FIX'
import sys
sys.path.insert(0, '/app/src')

from bot import LOGGER, auth_chats, sudo_users
from bot.core.config_manager import Config

print("\n" + "="*60)
print("APPLYING AUTHORIZATION FIX")
print("="*60)

# Force populate auth_chats if empty
if not auth_chats and Config.AUTHORIZED_CHATS:
    print(f"📝 Fixing auth_chats from config...")
    aid = Config.AUTHORIZED_CHATS.replace(",", " ").split()
    for id_ in aid:
        chat_id, *thread_ids = id_.split("|")
        chat_id = int(chat_id.strip())
        if thread_ids:
            thread_ids = list(map(lambda x: int(x.strip()), thread_ids))
            auth_chats[chat_id] = thread_ids
        else:
            auth_chats[chat_id] = []
    print(f"✅ auth_chats: {dict(auth_chats)}")
    LOGGER.info(f"✅ Fixed auth_chats: {dict(auth_chats)}")

# Force populate sudo_users if empty
if not sudo_users and Config.SUDO_USERS:
    print(f"📝 Fixing sudo_users from config...")
    aid = Config.SUDO_USERS.replace(",", " ").split()
    for id_ in aid:
        sudo_users.append(int(id_.strip()))
    print(f"✅ sudo_users: {list(sudo_users)}")
    LOGGER.info(f"✅ Fixed sudo_users: {list(sudo_users)}")

print("="*60)
print("✅ FIX APPLIED SUCCESSFULLY")
print("="*60 + "\n")
PYTHON_FIX

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ ✅ FIX COMPLETE - Commands should now work!               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📱 TEST THESE COMMANDS IN TELEGRAM:"
echo ""
echo "   /start"
echo "   /help"
echo "   /mirror https://speed.hetzner.de/10MB.bin"
echo "   /leech https://speed.hetzner.de/10MB.bin"
echo "   /ytdl https://www.youtube.com/watch?v=dQw4w9WgXcQ"
echo "   /status"
echo ""
echo "⚠️  NOTE:"
echo "   This fix is temporary and lasts until bot restart."
echo "   For a permanent fix, see COMMAND_FIX_REPORT.md"
echo ""
echo "❓ STILL NOT WORKING?"
echo "   1. Check your Telegram user ID: @userinfobot"
echo "   2. Verify ID is in AUTHORIZED_CHATS: grep AUTHORIZED_CHATS config/main_config.py"
echo "   3. Restart bot: docker restart mltb-app"
echo "   4. Check logs: docker logs mltb-app | tail -50"
echo ""
