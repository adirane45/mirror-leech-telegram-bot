from pyrogram.filters import create

from ... import auth_chats, sudo_users, user_data
from ...core.config_manager import Config


class CustomFilters:
    async def owner_filter(self, _, update):
        user = update.from_user or update.sender_chat
        return user.id == Config.OWNER_ID

    owner = create(owner_filter)

    def _is_owner(self, uid):
        """Check if user is owner"""
        return uid == Config.OWNER_ID
    
    def _is_auth_user(self, uid):
        """Check if user is authorized in user_data"""
        return (
            uid in user_data
            and (
                user_data[uid].get("AUTH", False)
                or user_data[uid].get("SUDO", False)
            )
        )
    
    def _is_auth_chat(self, chat_id, thread_id):
        """Check if chat is authorized"""
        return (
            chat_id in user_data
            and user_data[chat_id].get("AUTH", False)
            and (
                thread_id is None
                or thread_id in user_data[chat_id].get("thread_ids", [])
            )
        )
    
    def _is_in_sudo_or_auth_chats(self, uid):
        """Check if user is in sudo_users or auth_chats"""
        return uid in sudo_users or uid in auth_chats
    
    def _is_chat_in_auth_chats(self, chat_id, thread_id):
        """Check if chat/thread is in auth_chats"""
        return (
            chat_id in auth_chats
            and (
                auth_chats[chat_id]
                and thread_id
                and thread_id in auth_chats[chat_id]
                or not auth_chats[chat_id]
            )
        )
    
    async def authorized_user(self, _, update):
        user = update.from_user or update.sender_chat
        uid = user.id
        chat_id = update.chat.id
        thread_id = getattr(update, 'message_thread_id', None)
        
        return bool(
            self._is_owner(uid)
            or self._is_auth_user(uid)
            or self._is_auth_chat(chat_id, thread_id)
            or self._is_in_sudo_or_auth_chats(uid)
            or self._is_chat_in_auth_chats(chat_id, thread_id)
        )

    authorized = create(authorized_user)

    async def sudo_user(self, _, update):
        user = update.from_user or update.sender_chat
        uid = user.id
        return bool(
            uid == Config.OWNER_ID
            or uid in user_data
            and user_data[uid].get("SUDO")
            or uid in sudo_users
        )

    sudo = create(sudo_user)
