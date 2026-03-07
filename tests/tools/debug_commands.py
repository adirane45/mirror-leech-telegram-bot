#!/usr/bin/env python3
"""
Command Debug Script for Mirror Leech Telegram Bot
This script helps diagnose why mirror, leech, ytdl commands are not working
"""

import sys
import os

# Add src/bot to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def diagnose():
    from bot.core.config_manager import Config
    from bot.helper.telegram_helper.bot_commands import BotCommands
    from bot import user_data, auth_chats, sudo_users
    
    print("="*60)
    print("🔍 MIRROR LEECH TELEGRAM BOT - COMMAND DIAGNOSTIC")
    print("="*60)
    print()
    
    # 1. Check Config
    print("1️⃣  CONFIGURATION:")
    print(f"   BOT_TOKEN: {'✅ Set' if Config.BOT_TOKEN else '❌ Missing'}")
    print(f"   OWNER_ID: {Config.OWNER_ID}")
    print(f"   CMD_SUFFIX: '{Config.CMD_SUFFIX}' (empty = no suffix)")
    print(f"   AUTHORIZED_CHATS: {Config.AUTHORIZED_CHATS}")
    print(f"   SUDO_USERS: {Config.SUDO_USERS}")
    print()
    
    # 2. Check Commands
    print("2️⃣  COMMAND DEFINITIONS:")
    print(f"   mirror: {BotCommands.MirrorCommand}")
    print(f"   leech: {BotCommands.LeechCommand}")
    print(f"   ytdl: {BotCommands.YtdlCommand}")
    print(f"   ytdlleech: {BotCommands.YtdlLeechCommand}")
    print()
    
    # 3. Check Authorization Status
    print("3️⃣  AUTHORIZATION STATUS:")
    print(f"   auth_chats: {auth_chats if auth_chats else 'Empty dict/set'}")
    print(f"   sudo_users: {sudo_users if sudo_users else 'Empty set'}")
    print(f"   user_data entries: {len(user_data)}")
    print()
    
    # 4. Check if bot is reachable
    print("4️⃣  TELEGRAM CONNECTION:")
    try:
        from bot.core.telegram_manager import TgClient
        if TgClient.bot:
            print(f"   Bot Instance: ✅ Connected")
            print(f"   Bot Username: @{TgClient.NAME if hasattr(TgClient, 'NAME') and TgClient.NAME else 'Unknown'}")
        else:
            print(f"   Bot Instance: ❌ Not connected")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # 5. Recommendations
    print("5️⃣  DIAGNOSIS & SOLUTIONS:")
    print()
    
    # Check if user needs to be authorized
    owner_id = Config.OWNER_ID
    auth_list = Config.AUTHORIZED_CHATS.split() if hasattr(Config, 'AUTHORIZED_CHATS') and Config.AUTHORIZED_CHATS else []
    
    print("   ISSUE: Commands not responding")
    print("   MOST LIKELY CAUSE: User not authorized")
    print()
    print("   ✅ SOLUTION:")
    print(f"   1. Make sure you're sending commands from user ID: {owner_id}")
    print("   2. OR add your user ID to AUTHORIZED_CHATS in config")
    print("   3. OR send /start to the bot first (if you're the owner)")
    print()
    print("   HOW TO CHECK YOUR USER ID:")
    print("   - Send any message to @userinfobot on Telegram")
    print("   - It will show your user ID")
    print()
    print("   HOW TO AUTHORIZE YOURSELF:")
    print("   Option A - Using the bot (if you're the owner):")
    print(f"     1. Send: /start")
    print(f"     2. Send: /auth YOUR_USER_ID")
    print()
    print("   Option B - Edit config file:")
    print(f"     1. Edit: config/main_config.py")
    print(f"     2. Find: AUTHORIZED_CHATS")
    print(f"     3. Add your user ID (space-separated)")
    print(f"     4. Restart bot: docker restart mltb-app")
    print()
    print("   HOW TO SET COMMANDS IN TELEGRAM MENU:")
    print("   1. Open @BotFather in Telegram")
    print("   2. Send: /setcommands")
    print("   3. Select your bot")
    print("   4. Send: /cmdlist in your bot")
    print("   5. Copy the text file content")
    print("   6. Paste it to BotFather")
    print()
    
    # 6. Test command generation
    print("6️⃣  COMMAND EXAMPLES (copy and try these):")
    suffix = Config.CMD_SUFFIX
    print(f"   /mirror{suffix} https://speed.hetzner.de/10MB.bin")
    print(f"   /leech{suffix} https://speed.hetzner.de/10MB.bin")
    print(f"   /ytdl{suffix} https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    print(f"   /status{suffix}")
    print(f"   /help{suffix}")
    print()
    
    print("="*60)
    print("💡 TIP: If commands still don't work:")
    print("   - Check bot logs: docker logs mltb-app --tail 50")
    print("   - Try /start command first")
    print("   - Verify you're messaging the correct bot")
    print("="*60)

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(diagnose())
    except KeyboardInterrupt:
        print("\n\n👋 Diagnostic cancelled")
    except Exception as e:
        print(f"\n❌ Error running diagnostic: {e}")
        print("Traceback:")
        import traceback
        traceback.print_exc()
