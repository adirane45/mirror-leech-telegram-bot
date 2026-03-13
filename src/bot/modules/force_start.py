from .. import queue_dict_lock, queued_dl, queued_up, task_dict, task_dict_lock, user_data
from ..core.config_manager import Config
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import get_task_by_gid
from ..helper.ext_utils.task_manager import start_dl_from_queued, start_up_from_queued
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.message_utils import send_message


async def _parse_force_start_request(message):
    """Extract task and status from force start command."""
    msg = message.text.split()
    status = msg[1] if len(msg) > 1 and msg[1] in ["fd", "fu"] else ""

    gid = _extract_force_start_gid(msg, status)
    if gid:
        return await _resolve_force_start_task(gid, status)

    if reply_to_id := message.reply_to_message_id:
        async with task_dict_lock:
            task = task_dict.get(reply_to_id)
        if task is None:
            return None, None, "This is not an active task!"
        return task, status, None

    if len(msg) in {1, 2}:
        return None, None, _force_start_help_message()

    return None, None, None


def _extract_force_start_gid(msg, status):
    if status and len(msg) > 2:
        return msg[2]
    if not status and len(msg) > 1:
        return msg[1]
    return ""


async def _resolve_force_start_task(gid, status):
    task = await get_task_by_gid(gid)
    if task is None:
        return None, None, f"GID: <code>{gid}</code> Not Found."
    return task, status, None


def _force_start_help_message():
    return f"""Reply to an active Command message which was used to start the download/upload.
<code>/{BotCommands.ForceStartCommand[0]}</code> fd (to remove it from download queue) or fu (to remove it from upload queue) or nothing to start remove it from both download and upload queue.
Also send <code>/{BotCommands.ForceStartCommand[0]} GID</code> fu|fd or obly gid to force start by removing the task rom queue!
Examples:
<code>/{BotCommands.ForceStartCommand[1]}</code> GID fu (force upload)
<code>/{BotCommands.ForceStartCommand[1]}</code> GID (force download and upload)
By reply to task cmd:
<code>/{BotCommands.ForceStartCommand[1]}</code> (force download and upload)
<code>/{BotCommands.ForceStartCommand[1]}</code> fd (force download)
"""


def _check_task_permission(task, user_id):
    """Check if user has permission to force start this task."""
    return (
        Config.OWNER_ID == user_id
        or task.listener.user_id == user_id
        or (user_id in user_data and user_data[user_id].get("SUDO"))
    )


async def _force_upload_handler(listener):
    """Handle force upload request."""
    listener.force_upload = True
    if listener.mid in queued_up:
        await start_up_from_queued(listener.mid)
        return "Task have been force started to upload!"
    return "Force upload enabled for this task!"


async def _force_download_handler(listener):
    """Handle force download request."""
    listener.force_download = True
    if listener.mid in queued_dl:
        await start_dl_from_queued(listener.mid)
        return "Task have been force started to download only!"
    return "This task not in download queue!"


async def _force_both_handler(listener):
    """Handle force download and upload request."""
    listener.force_download = True
    listener.force_upload = True
    if listener.mid in queued_up:
        await start_up_from_queued(listener.mid)
        return "Task have been force started to upload!"
    if listener.mid in queued_dl:
        await start_dl_from_queued(listener.mid)
        return "Task have been force started to download and upload will start once download finish!"
    return "This task not in queue!"


@new_task
async def remove_from_queue(_, message):
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    
    task, status, error_msg = await _parse_force_start_request(message)
    if error_msg:
        await send_message(message, error_msg)
        return
    
    if not _check_task_permission(task, user_id):
        await send_message(message, "This task is not for you!")
        return
    
    listener = task.listener
    async with queue_dict_lock:
        if status == "fu":
            msg = await _force_upload_handler(listener)
        elif status == "fd":
            msg = await _force_download_handler(listener)
        else:
            msg = await _force_both_handler(listener)
    
    await send_message(message, msg)

