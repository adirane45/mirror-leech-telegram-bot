# Search and Filter - Modified by: justadi
from html import escape
from re import search as re_search, IGNORECASE

from .. import task_dict, task_dict_lock, download_history
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import MirrorStatus, get_readable_file_size
from ..helper.telegram_helper.interactive_keyboards import InteractiveKeyboards
from ..helper.telegram_helper.message_utils import send_message


@new_task
async def search_tasks(_, message):
    """Search tasks by name or GID"""
    msg = message.text.split(maxsplit=1)
    
    if len(msg) < 2:
        await send_message(
            message,
            "🔍 <b>Search Tasks</b>\n\n"
            "Usage: /search [query]\n"
            "Search by name or GID\n\n"
            "<i>Modified by: justadi</i>"
        )
        return
    
    query = msg[1].lower()
    
    async with task_dict_lock:
        tasks = list(task_dict.values())
    
    results = []
    for task in tasks:
        name = task.name().lower()
        gid = task.gid().lower()
        
        if query in name or query in gid:
            results.append(task)
    
    if not results:
        await send_message(message, f"❌ No tasks found matching: <code>{escape(query)}</code>")
        return
    
    text = f"<b>🔍 Search Results</b>\n"
    text += f"<b>Query:</b> <code>{escape(query)}</code>\n"
    text += f"<b>Found:</b> {len(results)} tasks\n\n"
    
    for idx, task in enumerate(results[:10], 1):
        name = task.name()[:40]
        gid = task.gid()[:8]
        status = task.status() if not callable(task.status) else "Processing"
        text += f"{idx}. <code>{name}</code>\n"
        text += f"   Status: {status} | GID: <code>{gid}</code>\n\n"
    
    if len(results) > 10:
        text += f"... and {len(results) - 10} more\n"
    
    text += "<i>Modified by: justadi</i>"
    
    await send_message(message, text, InteractiveKeyboards.search_filter())


@new_task
async def filter_tasks(_, message):
    """Filter tasks by status"""
    msg = message.text.split()
    
    if len(msg) < 2:
        await send_message(
            message,
            "🔍 <b>Filter Tasks</b>\n\n"
            "Usage: /filter [status]\n"
            "Status: download, upload, paused, queued, all\n\n"
            "<i>Modified by: justadi</i>"
        )
        return
    
    filter_status = msg[1].lower()
    
    async with task_dict_lock:
        tasks = list(task_dict.values())
    
    filtered = []
    for task in tasks:
        status = task.status() if not callable(task.status) else await task.status()
        status_lower = status.lower()
        
        if filter_status == "all":
            filtered.append((task, status))
        elif filter_status == "download" and MirrorStatus.STATUS_DOWNLOAD in status:
            filtered.append((task, status))
        elif filter_status == "upload" and MirrorStatus.STATUS_UPLOAD in status:
            filtered.append((task, status))
        elif filter_status == "paused" and MirrorStatus.STATUS_PAUSED in status:
            filtered.append((task, status))
        elif filter_status in ["queued", "queue"] and ("Queue" in status):
            filtered.append((task, status))
    
    if not filtered:
        await send_message(message, f"❌ No tasks found with status: <b>{filter_status}</b>")
        return
    
    text = f"<b>🔍 Filtered Tasks</b>\n"
    text += f"<b>Filter:</b> {filter_status.title()}\n"
    text += f"<b>Found:</b> {len(filtered)} tasks\n\n"
    
    for idx, (task, status) in enumerate(filtered[:10], 1):
        name = task.name()[:40]
        gid = task.gid()[:8]
        text += f"{idx}. <code>{name}</code>\n"
        text += f"   Status: {status} | GID: <code>{gid}</code>\n\n"
    
    if len(filtered) > 10:
        text += f"... and {len(filtered) - 10} more\n"
    
    text += "<i>Modified by: justadi</i>"
    
    await send_message(message, text, InteractiveKeyboards.status_filter())
