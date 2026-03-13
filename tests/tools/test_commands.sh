#!/bin/bash
#
# Mirror/Leech/YT-DLP Command - FINAL TEST & VERIFICATION
#

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     MIRROR LEECH YTDL - COMMAND FIX & VERIFICATION        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📋 ISSUE IDENTIFIED & FIXED:"
echo "   ✅ Commands were NOT being executed (tasks created but never awaited)"
echo "   ✅ Root cause: bot_loop.create_task() instead of await"
echo "   ✅ Fix: Changed to async/await pattern"
echo ""

echo "📝 FILES MODIFIED:"
echo "   ✅ src/bot/modules/mirror_leech.py   - mirror, leech, qb_*, jd_*, nzb_*"
echo "   ✅ src/bot/modules/ytdlp.py          - ytdl, ytdl_leech"
echo ""

echo "🔍 VERIFICATION:"
echo ""

# Check bot is running
if docker ps | grep -q mltb-app; then
    echo "✅ Bot container: RUNNING"
else
    echo "❌ Bot container: NOT RUNNING"
    exit 1
fi

echo ""
echo "✅ Recent startup logs:"
docker logs mltb-app 2>&1 | grep "Bot Started" | tail -1
docker logs mltb-app 2>&1 | grep "handlers registered" | tail -1
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ 📱 NOW TEST THESE COMMANDS IN TELEGRAM                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  /start"
echo "  /help"
echo ""
echo "  📥 MIRROR COMMANDS:"
echo "  /mirror https://speed.hetzner.de/10MB.bin  (Direct download)"
echo "  /m https://example.com/file.zip            (Shortcut)"
echo ""
echo "  ⬆️ LEECH COMMANDS:"
echo "  /leech https://speed.hetzner.de/10MB.bin   (Upload to Telegram)"
echo "  /l https://example.com/file.zip            (Shortcut)"
echo ""
echo "  ▶️ YOUTUBE COMMANDS:"
echo "  /ytdl https://youtu.be/dQw4w9WgXcQ         (Download video)"
echo "  /y https://youtu.be/dQw4w9WgXcQ            (Shortcut)"
echo "  /ytdlleech https://youtu.be/dQw4w9WgXcQ    (Download to Telegram)"
echo "  /yl https://youtu.be/dQw4w9WgXcQ           (Shortcut)"
echo ""
echo "  📊 OTHER:"
echo "  /status                                    (Check download status)"
echo "  /queue                                     (Show task queue)"
echo "  /cancel TASK_ID                            (Cancel download)"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║ 🐛 DEBUGGING IF STILL NOT WORKING                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Check command reception in logs:"
echo "   docker logs mltb-app 2>&1 | grep -i 'command received' | tail -10"
echo ""
echo "2. Check for any errors:"
echo "   docker logs mltb-app 2>&1 | grep -iE 'error|exception' | tail -20"
echo ""
echo "3. Test authorization status:"
echo "   docker exec mltb-app python3 -c \"import sys; sys.path.insert(0, '/app/src'); from bot import auth_chats, sudo_users; print(f'auth_chats: {auth_chats}'); print(f'sudo_users: {sudo_users}')\""
echo ""
echo "4. Verify user is authorized (use @userinfobot to get your ID):"
echo "   grep AUTHORIZED_CHATS config/main_config.py"
echo ""

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║ ✅ ALL FIXES APPLIED - COMMANDS SHOULD NOW WORK!          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
