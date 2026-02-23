from asyncio import gather, iscoroutinefunction
from shlex import split as shlex_split
from time import time

from .. import task_dict, task_dict_lock
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import (
    MirrorStatus,
    get_progress_bar_string,
    get_readable_file_size,
    get_readable_time,
    speed_string_to_bytes,
)
from ..helper.telegram_helper.interactive_keyboards import InteractiveKeyboards
from ..helper.telegram_helper.message_utils import send_message, edit_message


def _parse_args(text):
    args = {"status": None, "sort": None, "hours": None, "query": ""}
    parts = shlex_split(text)
    for p in parts[1:]:
        if p.startswith("-s=") or p.startswith("--status="):
            args["status"] = p.split("=", 1)[1]
        elif p.startswith("-sort="):
            args["sort"] = p.split("=", 1)[1]
        elif p.startswith("-h="):
            try:
                args["hours"] = int(p.split("=", 1)[1])
            except Exception:
                args["hours"] = None
        else:
            args["query"] += f" {p}"
    args["query"] = args["query"].strip()
    return args


async def _task_status(task):
    if iscoroutinefunction(task.status):
        return await task.status()
    return task.status()


@new_task
async def task_search(_, message):
    """Search and filter active tasks"""
    args = _parse_args(message.text)
    query = args["query"].lower()
    status_filter = args["status"]
    sort_by = args["sort"]
    hours = args["hours"]

    async with task_dict_lock:
        tasks = list(task_dict.values())

    results = []
    for task in tasks:
        status = await _task_status(task)
        if status_filter and status_filter.lower() not in status.lower():
            continue
        if hours and (time() - task.listener.created_at) > hours * 3600:
            continue
        name = task.name().lower()
        gid = task.gid().lower()
        if query and query not in name and query not in gid:
            continue
        results.append((task, status))

    if sort_by == "speed":
        results.sort(key=lambda x: speed_string_to_bytes(x[0].speed()), reverse=True)
    elif sort_by == "size":
        results.sort(key=lambda x: speed_string_to_bytes(x[0].size()), reverse=True)
    elif sort_by == "time":
        results.sort(key=lambda x: x[0].listener.created_at, reverse=True)

    if not results:
        await send_message(message, "❌ No tasks matched your search.")
        return

    text = "<b>🔍 Task Search Results</b>\n\n"
    for idx, (task, status) in enumerate(results[:20], start=1):
        progress = task.progress() if task.listener.progress else "-"
        text += (
            f"{idx}. <b>{status}</b> | <code>{task.name()[:40]}</code>\n"
            f"   Progress: {progress} | GID: <code>{task.gid()}</code>\n"
        )
    text += "\nTip: Use -s=Download -sort=speed -h=24"
    await send_message(message, text)


@new_task
async def task_details(_, message):
    """Detailed task information"""
    msg = message.text.split()
    if len(msg) < 2 and not message.reply_to_message_id:
        await send_message(message, "Usage: /tdetails [gid] or reply to a task message")
        return

    gid = msg[1] if len(msg) > 1 else None
    if not gid and message.reply_to_message_id:
        async with task_dict_lock:
            task = task_dict.get(message.reply_to_message_id)
            if task:
                gid = task.gid()

    if not gid:
        await send_message(message, "❌ GID not found!")
        return

    task = None
    async with task_dict_lock:
        for tk in task_dict.values():
            if tk.gid() == gid:
                task = tk
                break

    if not task:
        await send_message(message, "❌ Task not found!")
        return

    status = await _task_status(task)
    progress = task.progress() if task.listener.progress else "-"
    speed = task.speed()
    eta = task.eta()

    text = "<b>🔎 Task Details</b>\n\n"
    text += f"<b>Name:</b> <code>{task.name()}</code>\n"
    text += f"<b>Status:</b> {status}\n"
    text += f"<b>Progress:</b> {get_progress_bar_string(progress)} {progress}\n"
    text += f"<b>Speed:</b> {speed}\n"
    text += f"<b>ETA:</b> {eta}\n"
    text += f"<b>Size:</b> {task.size()}\n"
    text += f"<b>User:</b> <code>{task.listener.user_id}</code>\n"
    text += f"<b>GID:</b> <code>{gid}</code>\n"

    await send_message(message, text, InteractiveKeyboards.task_menu(gid))
