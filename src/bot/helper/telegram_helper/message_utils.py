from asyncio import sleep
from re import match as re_match
from time import time

from pyrogram.errors import FloodWait

from ... import DOWNLOAD_DIR, LOGGER, intervals, status_dict, task_dict_lock
from ...core.config_manager import Config
from ...core.telegram_manager import TgClient
from ..ext_utils.bot_utils import SetInterval
from ..ext_utils.exceptions import TgLinkException
from ..ext_utils.status_utils import get_readable_message


async def send_message(message, text, buttons=None, block=True):
    try:
        return await message.reply(
            text=text,
            disable_notification=True,
            reply_markup=buttons,
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        if not block:
            return str(f)
        await sleep(f.value * 1.2)
        return await send_message(message, text, buttons)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def edit_message(message, text, buttons=None, block=True):
    try:
        return await message.edit(
            text=text,
            reply_markup=buttons,
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        if not block:
            return str(f)
        await sleep(f.value * 1.2)
        return await edit_message(message, text, buttons)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def send_file(message, file, caption=""):
    try:
        return await message.reply_document(
            document=file, caption=caption, disable_notification=True
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await send_file(message, file, caption)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def send_rss(text, chat_id, thread_id):
    try:
        app = TgClient.user or TgClient.bot
        return await app.send_message(
            chat_id=chat_id,
            text=text,
            message_thread_id=thread_id,
            disable_notification=True,
        )
    except FloodWait as f:
        LOGGER.warning(str(f))
        await sleep(f.value * 1.2)
        return await send_rss(text)
    except Exception as e:
        LOGGER.error(str(e))
        return str(e)


async def delete_message(message):
    try:
        await message.delete()
    except Exception as e:
        LOGGER.error(str(e))


async def auto_delete_message(cmd_message=None, bot_message=None):
    await sleep(60)
    if cmd_message is not None:
        await delete_message(cmd_message)
    if bot_message is not None:
        await delete_message(bot_message)


async def delete_status():
    async with task_dict_lock:
        for key, data in list(status_dict.items()):
            try:
                await delete_message(data["message"])
                del status_dict[key]
            except Exception as e:
                LOGGER.error(str(e))


def _parse_telegram_link(link):
    if link.startswith("https://t.me/"):
        private = False
        msg = re_match(
            r"https:\/\/t\.me\/(?:c\/)?([^\/]+)(?:\/[^\/]+)?\/([0-9-]+)", link
        )
    else:
        private = True
        msg = re_match(
            r"tg:\/\/openmessage\?user_id=([0-9]+)&message_id=([0-9-]+)", link
        )
        if not TgClient.user:
            raise TgLinkException("USER_SESSION_STRING required for this private link!")
    return private, msg[1], msg[2]

def _expand_message_range(link, msg_id, private):
    links = []
    if "-" not in msg_id:
        return links, int(msg_id)
    
    start_id, end_id = msg_id.split("-")
    msg_id = start_id = int(start_id)
    end_id = int(end_id)
    btw = end_id - start_id
    
    if private:
        link = link.split("&message_id=")[0]
        links.append(f"{link}&message_id={start_id}")
        for _ in range(btw):
            start_id += 1
            links.append(f"{link}&message_id={start_id}")
    else:
        link = link.rsplit("/", 1)[0]
        links.append(f"{link}/{start_id}")
        for _ in range(btw):
            start_id += 1
            links.append(f"{link}/{start_id}")
    return links, msg_id

def _resolve_chat_id(chat, private):
    if chat.isdigit():
        return int(chat) if private else int(f"-100{chat}")
    return chat

async def _try_fetch_with_bot(chat, msg_id):
    try:
        message = await TgClient.bot.get_messages(chat_id=chat, message_ids=msg_id)
        if message.empty:
            return None
        return message
    except Exception:
        return None

async def _fetch_with_user(chat, msg_id):
    if not TgClient.user:
        return None
    try:
        user_message = await TgClient.user.get_messages(
            chat_id=chat, message_ids=msg_id
        )
        if not user_message.empty:
            return user_message
    except Exception as e:
        raise TgLinkException(
            f"You don't have access to this chat!. ERROR: {e}"
        ) from e
    return None

async def get_tg_link_message(link):
    private, chat, msg_id = _parse_telegram_link(link)
    links, msg_id = _expand_message_range(link, msg_id, private)
    chat = _resolve_chat_id(chat, private)
    
    if not private:
        message = await _try_fetch_with_bot(chat, msg_id)
        if message:
            return (links, "bot") if links else (message, "bot")
        private = True
        if not TgClient.user:
            raise TgLinkException("Bot cannot access private chat and no user session")
    
    user_message = await _fetch_with_user(chat, msg_id)
    if user_message:
        return (links, "user") if links else (user_message, "user")
    raise TgLinkException("Private: Please report!")


async def temp_download(msg):
    path = f"{DOWNLOAD_DIR}temp"
    return await msg.download(file_name=f"{path}/")


def _cancel_status_interval(sid):
    if obj := intervals["status"].get(sid):
        obj.cancel()
        del intervals["status"][sid]


def _remove_status_entry(sid):
    if sid in status_dict:
        del status_dict[sid]
    _cancel_status_interval(sid)


def _should_skip_status_update(sid, force=False):
    return not force and time() - status_dict[sid]["time"] < 3


def _should_update_status_text(sid, text):
    return text != status_dict[sid]["message"].text


async def _handle_status_edit_failure(sid, message):
    if message.startswith("Telegram says: [40"):
        _remove_status_entry(sid)
        return
    LOGGER.error(
        f"Status with id: {sid} haven't been updated. Error: {message}"
    )


async def update_status_message(sid, force=False):
    if intervals["stopAll"]:
        return
    async with task_dict_lock:
        if not status_dict.get(sid):
            _cancel_status_interval(sid)
            return
        if _should_skip_status_update(sid, force):
            return
        status_dict[sid]["time"] = time()
        page_no = status_dict[sid]["page_no"]
        status = status_dict[sid]["status"]
        is_user = status_dict[sid]["is_user"]
        page_step = status_dict[sid]["page_step"]
        text, buttons = await get_readable_message(
            sid, is_user, page_no, status, page_step
        )
        if text is None:
            _remove_status_entry(sid)
            return
        if _should_update_status_text(sid, text):
            message = await edit_message(
                status_dict[sid]["message"], text, buttons, block=False
            )
            if isinstance(message, str):
                await _handle_status_edit_failure(sid, message)
                return
            status_dict[sid]["message"].text = text
            status_dict[sid]["time"] = time()


async def _send_existing_status_message(msg, sid, is_user):
    page_no = status_dict[sid]["page_no"]
    status = status_dict[sid]["status"]
    page_step = status_dict[sid]["page_step"]
    text, buttons = await get_readable_message(
        sid, is_user, page_no, status, page_step
    )
    if text is None:
        _remove_status_entry(sid)
        return False

    old_message = status_dict[sid]["message"]
    message = await send_message(msg, text, buttons, block=False)
    if isinstance(message, str):
        LOGGER.error(
            f"Status with id: {sid} haven't been sent. Error: {message}"
        )
        return False

    await delete_message(old_message)
    message.text = text
    status_dict[sid].update({"message": message, "time": time()})
    return True


async def _send_new_status_message(msg, sid, is_user):
    text, buttons = await get_readable_message(sid, is_user)
    if text is None:
        return False

    message = await send_message(msg, text, buttons, block=False)
    if isinstance(message, str):
        LOGGER.error(
            f"Status with id: {sid} haven't been sent. Error: {message}"
        )
        return False

    message.text = text
    status_dict[sid] = {
        "message": message,
        "time": time(),
        "page_no": 1,
        "page_step": 1,
        "status": "All",
        "is_user": is_user,
    }
    return True


def _ensure_status_interval(sid, is_user):
    if intervals["status"].get(sid) or is_user:
        return
    intervals["status"][sid] = SetInterval(
        Config.STATUS_UPDATE_INTERVAL, update_status_message, sid
    )


async def send_status_message(msg, user_id=0):
    if intervals["stopAll"]:
        return
    sid = user_id or msg.chat.id
    is_user = bool(user_id)
    async with task_dict_lock:
        if sid in status_dict:
            if not await _send_existing_status_message(msg, sid, is_user):
                return
        else:
            if not await _send_new_status_message(msg, sid, is_user):
                return
        _ensure_status_interval(sid, is_user)
