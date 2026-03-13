#!/bin/bash
# Quick fix script for command issues

echo "🔧 Mirror Leech Bot - Command Fix Script"
echo "=========================================="
echo ""

# Check if bot is running
if ! docker ps | grep -q mltb-app; then
    echo "❌ Bot container is not running!"
    echo "   Starting bot..."
    docker-compose up -d app
    sleep 5
fi

echo "✅ Bot is running"
echo ""

# Get user to authorize
echo "📝 Let's authorize your Telegram user..."
echo ""
read -p "Enter your Telegram User ID (get it from @userinfobot): " USER_ID

if [ -z "$USER_ID" ]; then
    echo "❌ No user ID provided. Exiting."
    exit 1
fi

echo ""
echo "Adding user ID $USER_ID to authorized users..."

# Check current config
if grep -q "AUTHORIZED_CHATS.*$USER_ID" config/main_config.py; then
    echo "✅ User ID already in AUTHORIZED_CHATS"
else
    echo "📝 Adding to config..."

    # Backup config
    cp config/main_config.py config/main_config.py.backup.$(date +%s)

    # Add user to AUTHORIZED_CHATS if not already there
    current_auth=$(grep "AUTHORIZED_CHATS.*=" config/main_config.py | head -1 | cut -d'"' -f2)
    if [ -z "$current_auth" ]; then
        current_auth="$USER_ID"
    elif ! echo "$current_auth" | grep -q "$USER_ID"; then
        current_auth="$current_auth $USER_ID"
    fi

    sed -i "s/AUTHORIZED_CHATS = .*/AUTHORIZED_CHATS = \"$current_auth\"/" config/main_config.py
    echo "✅ Added $USER_ID to AUTHORIZED_CHATS"
fi

echo ""
echo "🔄 Restarting bot to apply changes..."
docker restart mltb-app

echo ""
echo "⏳ Waiting for bot to start..."
sleep 8

echo ""
echo "="*50
echo "✅ FIX APPLIED!"
echo "="*50
echo ""
echo "📱 NOW TRY THESE COMMANDS IN TELEGRAM:"
echo "   /start"
echo "   /help"
echo "   /mirror https://speed.hetzner.de/10MB.bin"
echo "   /leech https://speed.hetzner.de/10MB.bin"
echo "   /status"
echo ""
echo "💡 STILL NOT WORKING?"
echo ""
echo "1. Make sure you're using the correct bot (@$(docker logs mltb-app 2>&1 | grep 'Bot client started' | tail -1 | grep -oP '@\K\w+'))"
echo "2. Check if your user ID is correct (use @userinfobot)"
echo "3. View bot logs: docker logs mltb-app --tail 50"
echo "4. Try sending /start first to initialize the bot"
echo ""
echo "📋 SET TELEGRAM MENU COMMANDS:"
echo "1. Open @BotFather"
echo "2. Send: /setcommands"
echo "3. Select your bot"
echo "4. Send /cmdlist to your bot and copy the file content"
echo "5. Paste to @BotFather"
echo ""
echo "Need more help? Check: docs/guides/COMMANDS.md"
echo "="*50
