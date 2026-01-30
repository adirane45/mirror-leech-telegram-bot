from asyncio import gather
from time import time
from psutil import cpu_percent, virtual_memory, disk_usage

from .. import task_dict, task_dict_lock, download_history, DOWNLOAD_DIR, bot_start_time
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import (
    MirrorStatus,
    get_readable_file_size,
    get_readable_time,
)
from ..helper.ext_utils.history_utils import format_history
from ..helper.telegram_helper.interactive_keyboards import InteractiveKeyboards
from ..helper.telegram_helper.message_utils import send_message


async def _collect_status_counts():
    from inspect import iscoroutinefunction
    
    tasks = list(task_dict.values())
    counts = {
        "download": 0,
        "upload": 0,
        "paused": 0,
        "queued": 0,
        "other": 0,
    }
    if not tasks:
        return counts

    # Separate async and sync status methods
    coro_tasks = [tk for tk in tasks if iscoroutinefunction(tk.status)]
    sync_tasks = [tk for tk in tasks if not iscoroutinefunction(tk.status)]
    
    # Get async statuses
    coro_statuses = await gather(*[tk.status() for tk in coro_tasks]) if coro_tasks else []
    
    # Process all statuses
    all_statuses = list(coro_statuses) + [tk.status() for tk in sync_tasks]
    
    for st in all_statuses:
        if st == MirrorStatus.STATUS_DOWNLOAD:
            counts["download"] += 1
        elif st == MirrorStatus.STATUS_UPLOAD:
            counts["upload"] += 1
        elif st == MirrorStatus.STATUS_PAUSED:
            counts["paused"] += 1
        elif st in [MirrorStatus.STATUS_QUEUEDL, MirrorStatus.STATUS_QUEUEUP]:
            counts["queued"] += 1
        else:
            counts["other"] += 1
    return counts


@new_task
async def dashboard(_, message):
    """Dashboard/Summary view"""
    async with task_dict_lock:
        active_count = len(task_dict)

    counts = await _collect_status_counts()
    mem = virtual_memory()
    disk = disk_usage(DOWNLOAD_DIR)

    header = "<b>📊 Dashboard / Summary</b>\n"
    header += f"<b>Active Tasks:</b> {active_count}\n"
    header += (
        f"<b>Status:</b> ▶️ {counts['download']} | ⬆️ {counts['upload']} | "
        f"⏸️ {counts['paused']} | ⏳ {counts['queued']} | ⚙️ {counts['other']}\n\n"
    )

    system = (
        f"<b>System:</b>\n"
        f"• CPU: {cpu_percent()}%\n"
        f"• RAM: {mem.percent}%\n"
        f"• Disk Free: {get_readable_file_size(disk.free)}\n"
        f"• Uptime: {get_readable_time(time() - bot_start_time)}\n\n"
    )

    history_text = "<b>Recent Activity:</b>\n"
    if download_history:
        history_text += format_history(list(download_history), limit=5)
    else:
        history_text += "No recent activity."

    text = header + system + history_text
    await send_message(message, text, InteractiveKeyboards.quick_actions())
