from .. import user_data
from ..helper.ext_utils.bot_utils import new_task, update_user_ldata
from ..helper.ext_utils.db_handler import database
from ..helper.telegram_helper.message_utils import send_message


async def _parse_chat_id_and_thread(message) -> tuple:
    """Parse chat_id and thread_id from message.
    
    Args:
        message: Telegram message object
    
    Returns:
        Tuple of (chat_id, thread_id)
    """
    msg = message.text.split()
    thread_id = None
    
    if len(msg) > 1:
        if "|" in msg:
            chat_id, thread_id = list(map(int, msg[1].split("|")))
        else:
            chat_id = int(msg[1].strip())
    elif (reply_to := message.reply_to_message) and reply_to.id != message.message_thread_id:
        chat_id = reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
    else:
        if message.topic_message:
            thread_id = message.message_thread_id
        chat_id = message.chat.id
    
    return chat_id, thread_id


def _is_already_authorized(chat_id: int, thread_id: int) -> bool:
    """Check if chat_id is already authorized.
    
    Args:
        chat_id: User/chat ID
        thread_id: Thread ID (optional)
    
    Returns:
        True if already authorized, False otherwise
    """
    if chat_id not in user_data or not user_data[chat_id].get("AUTH"):
        return False
    
    if thread_id is None:
        return True
    
    return thread_id in user_data[chat_id].get("thread_ids", [])


async def _authorize_chat(chat_id: int, thread_id: int) -> str:
    """Authorize a chat or thread.
    
    Args:
        chat_id: User/chat ID
        thread_id: Thread ID (optional)
    
    Returns:
        Status message
    """
    if _is_already_authorized(chat_id, thread_id):
        return "Already Authorized!"
    
    if chat_id in user_data and user_data[chat_id].get("AUTH"):
        if "thread_ids" in user_data[chat_id]:
            user_data[chat_id]["thread_ids"].append(thread_id)
        else:
            user_data[chat_id]["thread_ids"] = [thread_id]
    else:
        update_user_ldata(chat_id, "AUTH", True)
        if thread_id is not None:
            update_user_ldata(chat_id, "thread_ids", [thread_id])
    
    await database.update_user_data(chat_id)
    return "Authorized"


async def _unauthorize_chat(chat_id: int, thread_id: int) -> str:
    """Unauthorize a chat or thread.
    
    Args:
        chat_id: User/chat ID
        thread_id: Thread ID (optional)
    
    Returns:
        Status message
    """
    if chat_id not in user_data or not user_data[chat_id].get("AUTH"):
        return "Already Unauthorized! Authorized Chats added from config must be removed from config."
    
    if thread_id is not None and thread_id in user_data[chat_id].get("thread_ids", []):
        user_data[chat_id]["thread_ids"].remove(thread_id)
    else:
        update_user_ldata(chat_id, "AUTH", False)
    
    await database.update_user_data(chat_id)
    return "Unauthorized"


@new_task
async def authorize(_, message):
    try:
        chat_id, thread_id = await _parse_chat_id_and_thread(message)
        msg = await _authorize_chat(chat_id, thread_id)
    except Exception as e:
        msg = f"Error: {e}"
    await send_message(message, msg)


@new_task
async def unauthorize(_, message):
    try:
        chat_id, thread_id = await _parse_chat_id_and_thread(message)
        msg = await _unauthorize_chat(chat_id, thread_id)
    except Exception as e:
        msg = f"Error: {e}"
    await send_message(message, msg)


@new_task
async def add_sudo(_, message):
    id_ = ""
    msg = message.text.split()
    try:
        if len(msg) > 1:
            id_ = int(msg[1].strip())
        elif reply_to := message.reply_to_message:
            id_ = reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
        if id_:
            if id_ in user_data and user_data[id_].get("SUDO"):
                msg = "Already Sudo!"
            else:
                update_user_ldata(id_, "SUDO", True)
                await database.update_user_data(id_)
                msg = "Promoted as Sudo"
        else:
            msg = "Give ID or Reply To message of whom you want to Promote."
    except Exception as e:
        msg = f"Error: {e}"
    await send_message(message, msg)


@new_task
async def remove_sudo(_, message):
    id_ = ""
    msg = message.text.split()
    try:
        if len(msg) > 1:
            id_ = int(msg[1].strip())
        elif reply_to := message.reply_to_message:
            id_ = reply_to.from_user.id if reply_to.from_user else reply_to.sender_chat.id
        if id_:
            if id_ in user_data and user_data[id_].get("SUDO"):
                update_user_ldata(id_, "SUDO", False)
                await database.update_user_data(id_)
                msg = "Demoted"
            else:
                msg = "Already Not Sudo! Sudo users added from config must be removed from config."
        else:
            msg = "Give ID or Reply To message of whom you want to remove from Sudo"
    except Exception as e:
        msg = f"Error: {e}"
    await send_message(message, msg)
