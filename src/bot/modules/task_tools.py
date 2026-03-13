from asyncio import iscoroutinefunction
from shlex import split as shlex_split
from time import time

from .. import task_dict, task_dict_lock
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import get_progress_bar_string, speed_string_to_bytes
from ..helper.telegram_helper.interactive_keyboards import InteractiveKeyboards
from ..helper.telegram_helper.message_utils import send_message


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


def _task_matches_filters(task, query: str, status_filter: str, hours: int) -> bool:
    """Check if task matches all search filters.
    
    Args:
        task: The task object to check
        query: Search query string
        status_filter: Status filter (optional)
        hours: Age filter in hours (optional)
    
    Returns:
        True if task matches all filters, False otherwise
    """
    if status_filter and status_filter.lower() not in (task.status if isinstance(task.status, str) else "").lower():
        return False
    if hours and (time() - task.listener.created_at) > hours * 3600:
        return False
    if query:
        name = task.name().lower()
        gid = task.gid().lower()
        if query not in name and query not in gid:
            return False
    return True


def _sort_results(results: list, sort_by: str) -> list:
    """Sort search results by specified criteria.
    
    Args:
        results: List of (task, status) tuples
        sort_by: Sort key (speed, size, time, or None)
    
    Returns:
        Sorted results list
    """
    if not sort_by:
        return results
    
    if sort_by == "speed":
        return sorted(results, key=lambda x: speed_string_to_bytes(x[0].speed()), reverse=True)
    elif sort_by == "size":
        return sorted(results, key=lambda x: speed_string_to_bytes(x[0].size()), reverse=True)
    elif sort_by == "time":
        return sorted(results, key=lambda x: x[0].listener.created_at, reverse=True)
    return results


def _format_search_results(results: list) -> str:
    """Format search results for display.
    
    Args:
        results: List of (task, status) tuples
    
    Returns:
        Formatted message string
    """
    text = "<b>🔍 Task Search Results</b>\n\n"
    for idx, (task, status) in enumerate(results[:20], start=1):
        progress = task.progress() if task.listener.progress else "-"
        text += (
            f"{idx}. <b>{status}</b> | <code>{task.name()[:40]}</code>\n"
            f"   Progress: {progress} | GID: <code>{task.gid()}</code>\n"
        )
    text += "\nTip: Use -s=Download -sort=speed -h=24"
    return text


async def _get_gid_from_message(message) -> str:
    """Extract GID from message or reply.
    
    Args:
        message: Telegram message object
    
    Returns:
        GID string or None if not found
    """
    msg = message.text.split()
    if len(msg) > 1:
        return msg[1]
    
    if message.reply_to_message_id:
        async with task_dict_lock:
            task = task_dict.get(message.reply_to_message_id)
            if task:
                return task.gid()
    
    return None


async def _find_task_by_gid(gid: str):
    """Find task in task_dict by GID.
    
    Args:
        gid: Task GID to search for
    
    Returns:
        Task object or None if not found
    """
    async with task_dict_lock:
        for task in task_dict.values():
            if task.gid() == gid:
                return task
    return None


def _format_task_details(task, status: str, gid: str) -> str:
    """Format task details for display.
    
    Args:
        task: Task object
        status: Task status string
        gid: Task GID
    
    Returns:
        Formatted message string
    """
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
    
    return text


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

    # Filter tasks matching all criteria
    results = [
        (task, await _task_status(task))
        for task in tasks
        if _task_matches_filters(task, query, status_filter, hours)
    ]

    if not results:
        await send_message(message, "❌ No tasks matched your search.")
        return

    # Sort results and format output
    sorted_results = _sort_results(results, sort_by)
    text = _format_search_results(sorted_results)
    await send_message(message, text)


@new_task
async def task_details(_, message):
    """Detailed task information"""
    if not message.text.split()[1:] and not message.reply_to_message_id:
        await send_message(message, "Usage: /tdetails [gid] or reply to a task message")
        return

    # Extract GID from message or reply
    gid = await _get_gid_from_message(message)
    if not gid:
        await send_message(message, "❌ GID not found!")
        return

    # Find task by GID
    task = await _find_task_by_gid(gid)
    if not task:
        await send_message(message, "❌ Task not found!")
        return

    # Format and send task details
    status = await _task_status(task)
    text = _format_task_details(task, status, gid)
    await send_message(message, text, InteractiveKeyboards.task_menu(gid))
