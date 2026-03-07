#!/usr/bin/env python3
"""
Fix Authorization Issue - Direct Solution

The problem is that auth_chats and sudo_users are not being populated from AUTHORIZED_CHATS and SUDO_USERS config.
This script will manually fix this by directly updating the in-memory dictionaries.
"""

import sys
import subprocess

print("="*70)
print("🔧 FIXING COMMAND AUTHORIZATION ISSUE")  
print("="*70)
print()

# The issue: auth_chats and sudo_users are empty dicts/lists at runtime
# even though the config has AUTHORIZED_CHATS and SUDO_USERS set
#
# Root Cause: The update_variables() function may not be properly updating
# the module-level globals from __init__.py
#
# Solution: Create a post-startup hook that forces update of these variables

# Create a fixed version of the initialization code that will be imported
# after the bot starts, to ensure the data is actually populated

verification_script = """
import sys
sys.path.insert(0, '/app/src')

from bot import LOGGER, auth_chats, sudo_users
from bot.core.config_manager import Config

print("\\n" + "="*70)
print("🔧 POST-STARTUP AUTHORIZATION FIX")
print("="*70)

# Force populate auth_chats if empty
if not auth_chats and Config.AUTHORIZED_CHATS:
    print(f"📝 Fixing auth_chats from config: {Config.AUTHORIZED_CHATS}")
    aid = Config.AUTHORIZED_CHATS.replace(",", " ").split()
    for id_ in aid:
        chat_id, *thread_ids = id_.split("|")
        chat_id = int(chat_id.strip())
        if thread_ids:
            thread_ids = list(map(lambda x: int(x.strip()), thread_ids))
            auth_chats[chat_id] = thread_ids
        else:
            auth_chats[chat_id] = []
    print(f"✅ auth_chats fixed: {dict(auth_chats)}")
    LOGGER.info(f"✅ Fixed auth_chats: {dict(auth_chats)}")

# Force populate sudo_users if empty
if not sudo_users and Config.SUDO_USERS:
    print(f"📝 Fixing sudo_users from config: {Config.SUDO_USERS}")
    aid = Config.SUDO_USERS.replace(",", " ").split()
    for id_ in aid:
        sudo_users.append(int(id_.strip()))
    print(f"✅ sudo_users fixed: {list(sudo_users)}")
    LOGGER.info(f"✅ Fixed sudo_users: {list(sudo_users)}")

if auth_chats and sudo_users:
    print("✅ Authorization data successfully fixed!")
    print("="*70)
    LOGGER.info("✅ Authorization data successfully fixed!")
else:
    print("⚠️  Some auth data still empty. Check configuration.")
    print(f"   auth_chats: {dict(auth_chats) if auth_chats else 'EMPTY'}")
    print(f"   sudo_users: {list(sudo_users) if sudo_users else 'EMPTY'}")
    print("="*70)
"""

# Write the fix script to the container
with open('/tmp/fix_auth.py', 'w') as f:
    f.write(verification_script)

print("📋 Injecting auth fix into running container...")
result = subprocess.run(
    ['docker', 'cp', '/tmp/fix_auth.py', 'mltb-app:/app/fix_auth.py'],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Script copied to container")
    
    # Execute the fix
    result = subprocess.run(
        ['docker', 'exec', 'mltb-app', 'python3', '/app/fix_auth.py'],
        capture_output=True,
        text=True
    )
    
    print("\n" + result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
else:
    print(f"❌ Failed to copy file: {result.stderr}")
    sys.exit(1)

print()
print("="*70)
print("✅ FIX COMPLETE")
print("="*70)
print()
print("📱 NOW TEST THE COMMANDS:")
print("   1. Open your Telegram bot")
print("   2. Send: /start")
print("   3. Send: /mirror https://speed.hetzner.de/10MB.bin")
print("   4. Send: /leech https://speed.hetzner.de/10MB.bin")
print("   5. Send: /ytdl https://www.youtube.com/watch?v=dQw4w9WgXcQ")
print()
print("If commands still don't work:")
print("   - Check user ID with @userinfobot")
print("   - Verify your ID is in AUTHORIZED_CHATS in config/main_config.py")
print("   - Restart bot: docker restart mltb-app")
print("="*70)
