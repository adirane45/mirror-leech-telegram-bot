#!/usr/bin/env python3
"""
Test Authorization Logic - Check if the filter is working
"""

import sys

sys.path.insert(0, '/app/src')

from bot import auth_chats, sudo_users, user_data
from bot.core.config_manager import Config
from bot.helper.telegram_helper.filters import CustomFilters


# Simulate a message object
class FakeUser:
    def __init__(self, user_id):
        self.id = user_id

class FakeMessage:
    def __init__(self, user_id, chat_id):
        self.from_user = FakeUser(user_id)
        self.sender_chat = None
        self.chat = FakeUser(chat_id)
        self.message_thread_id = None

async def test_auth():
    print("="*60)
    print("AUTHORIZATION TEST")
    print("="*60)
    print()
    print("Configuration:")
    print(f"  OWNER_ID: {Config.OWNER_ID}")
    print(f"  AUTHORIZED_CHATS: {Config.AUTHORIZED_CHATS}")
    print(f"  SUDO_USERS: {Config.SUDO_USERS}")
    print()
    print("Runtime State:")
    print(f"  auth_chats: {auth_chats}")
    print(f"  sudo_users: {sudo_users}")
    print(f"  user_data: {len(user_data)} entries")
    print()

    cf = CustomFilters()

    # Test owner
    print("Testing OWNER (1041454699):")
    msg = FakeMessage(1041454699, 1041454699)
    is_auth = await cf.authorized_user(None, msg)
    print(f"  Authorized: {is_auth}")
    print()

    # Test authorized user
    print("Testing AUTHORIZED USER (1025628570):")
    msg = FakeMessage(1025628570, 1025628570)
    is_auth = await cf.authorized_user(None, msg)
    print(f"  Authorized: {is_auth}")
    print()

    # Test random user
    print("Testing RANDOM USER (999999999):")
    msg = FakeMessage(999999999, 999999999)
    is_auth = await cf.authorized_user(None, msg)
    print(f"  Authorized: {is_auth}")
    print()

    print("="*60)
    print("DIAGNOSIS:")
    print("="*60)

    if not auth_chats and not sudo_users and len(user_data) == 0:
        print("❌ PROBLEM: All auth structures are empty!")
        print()
        print("This means update_variables() didn't run properly.")
        print("Commands will only work for OWNER_ID due to hardcoded check.")
        print()
        print("SOLUTION:")
        print("1) Restart bot: docker restart mltb-app")
        print("2) Check logs: docker logs mltb-app | grep update_variables")
        print("3) If still failing, manually authorize:")
        print(f"   - Send /start to bot from user {Config.OWNER_ID}")
        print(f"   - Then send: /auth {Config.OWNER_ID}")
    else:
        print("✅ Authorization structures populated correctly")

    print("="*60)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_auth())
