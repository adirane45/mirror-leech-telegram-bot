#!/usr/bin/env python3
"""
Test script to verify command handling
"""

import sys
sys.path.insert(0, '/app/src')

async def test_handler():
    from bot.core.telegram_manager import TgClient
    from bot.core.config_manager import Config
    from bot import auth_chats, sudo_users, LOGGER
    
    print("="*70)
    print("HANDLER TEST")
    print("="*70)
    
    # Test importing handlers
    try:
        from bot.modules.mirror_leech import mirror, leech
        print("✅ Handlers imported successfully")
    except Exception as e:
        print(f"❌ Failed to import handlers: {e}")
        return
    
    # Create fake message object
    class FakeChat:
        id = 12345
    
    class FakeUser:
        id = 1041454699
    
    class FakeMessage:
        def __init__(self):
            self.chat = FakeChat()
            self.from_user = FakeUser()
            self.text = "/mirror https://example.com/file.zip"
            self.message_id = 999
    
    # Create fake client
    class FakeClient:
        pass
    
    fake_msg = FakeMessage()
    fake_client = FakeClient()
    
    print(f"\n📝 Fake message created:")
    print(f"   text: {fake_msg.text}")
    print(f"   from_user.id: {fake_msg.from_user.id}")
    print(f"   chat.id: {fake_msg.chat.id}")
    
    print(f"\n🔐 Authorization check:")
    print(f"   OWNER_ID: {Config.OWNER_ID}")
    print(f"   auth_chats: {dict(auth_chats) if auth_chats else 'EMPTY'}")
    print(f"   sudo_users: {list(sudo_users) if sudo_users else 'EMPTY'}")
    print(f"   User is owner: {fake_msg.from_user.id == Config.OWNER_ID}")
    
    # Try calling the handler
    print(f"\n🚀 Calling mirror() handler...")
    try:
        await mirror(fake_client, fake_msg)
        print("✅ Handler executed without exception")
    except Exception as e:
        print(f"❌ Handler raised exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_handler())
