# Task Details View - Modified by: justadi
from html import escape
from inspect import iscoroutinefunction

from .. import task_dict, task_dict_lock
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import get_task_by_gid, get_readable_file_size, get_readable_time
from ..helper.telegram_helper.interactive_keyboards import InteractiveKeyboards
from ..helper.telegram_helper.message_utils import send_message


@new_task
async def task_details(_, message):
    """Show detailed information about a specific task"""
    msg = message.text.split()
    
    if len(msg) < 2:
        await send_message(
            message,
            "🔎 <b>Task Details</b>\n\n"
            "Usage: /taskdetails [gid]\n"
            "Or reply to a task message\n\n"
            "<i>Modified by: justadi</i>"
        )
        return
    
    gid = msg[1]
    task = await get_task_by_gid(gid)
    
    if not task:
        await send_message(message, f"❌ Task with GID <code>{gid}</code> not found!")
        return
    
    # Gather task information
    name = escape(task.name())
    status = await task.status() if iscoroutinefunction(task.status) else task.status()
    size = task.size()
    
    details = f"<b>🔎 Task Details</b>\n\n"
    details += f"<b>Name:</b>\n<code>{name}</code>\n\n"
    details += f"<b>GID:</b> <code>{gid}</code>\n"
    details += f"<b>Status:</b> {status}\n"
    details += f"<b>Size:</b> {size}\n"
    
    if hasattr(task, "processed_bytes"):
        details += f"<b>Processed:</b> {task.processed_bytes()}\n"
    
    if hasattr(task, "speed"):
        details += f"<b>Speed:</b> {task.speed()}\n"
    
    if hasattr(task, "eta"):
        details += f"<b>ETA:</b> {task.eta()}\n"
    
    if hasattr(task, "progress"):
        details += f"<b>Progress:</b> {task.progress()}\n"
    
    if hasattr(task.listener, "user_id"):
        details += f"<b>User ID:</b> <code>{task.listener.user_id}</code>\n"
    
    if hasattr(task.listener, "link"):
        link = task.listener.link
        if link and len(link) < 100:
            details += f"<b>Source:</b> <code>{escape(link)}</code>\n"
    
    if hasattr(task.listener, "created_at"):
        from time import time
        age = int(time() - task.listener.created_at)
        details += f"<b>Started:</b> {get_readable_time(age)} ago\n"
    
    details += "\n<i>Modified by: justadi</i>"
    
    await send_message(message, details, InteractiveKeyboards.task_menu(gid))
