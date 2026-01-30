# Task Scheduling Commands
# Schedule downloads to start at specific times
# Perfect for off-peak bandwidth usage
# Modified by: justadi

from datetime import datetime, timedelta
from secrets import token_hex

from ..core.task_scheduler import TaskScheduler
from ..helper.ext_utils.bot_utils import new_task
from ..helper.telegram_helper.message_utils import send_message


def _parse_time(time_str: str) -> datetime:
    """Parse time as HH:MM or YYYY-MM-DD HH:MM"""
    time_str = time_str.strip()
    if "-" in time_str:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M")

    now = datetime.now()
    dt = datetime.strptime(time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    if dt <= now:
        dt = dt + timedelta(days=1)
    return dt


@new_task
async def schedule_task(_, message):
    """
    Schedule a mirror/leech task for later execution
    
    Usage:
        /schedule HH:MM mirror <link> [options]
        /schedule YYYY-MM-DD HH:MM leech <link> [options]
    
    Examples:
        /schedule 02:30 mirror https://example.com/file.zip
        /schedule 2026-02-01 18:00 leech magnet:?xt=...
    
    Modified by: justadi
    """
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await send_message(
            message,
            "<b>🗓️ Schedule Task</b>\n\n"
            "Usage:\n"
            "<code>/schedule HH:MM mirror <link> [options]</code>\n"
            "<code>/schedule YYYY-MM-DD HH:MM leech <link> [options]</code>\n",
        )
        return

    try:
        start_time = _parse_time(parts[1])
    except Exception:
        await send_message(message, "<b>❌ Invalid time format.</b>")
        return

    command_text = parts[2].strip()
    cmd_word = command_text.split(maxsplit=1)[0].lstrip("/").lower()
    if cmd_word not in {"mirror", "leech"}:
        await send_message(message, "<b>❌ Command must start with mirror or leech.</b>")
        return

    is_leech = cmd_word == "leech"
    task_id = token_hex(4)
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    chat_id = message.chat.id

    ok = await TaskScheduler.schedule_download(
        task_id=task_id,
        user_id=user_id,
        chat_id=chat_id,
        command_text=command_text,
        start_time=start_time,
        is_leech=is_leech,
    )

    if ok:
        await send_message(
            message,
            "<b>✅ Task Scheduled</b>\n"
            f"<b>ID:</b> <code>{task_id}</code>\n"
            f"<b>When:</b> <code>{start_time}</code>",
        )
    else:
        await send_message(message, "<b>❌ Failed to schedule task.</b>")


@new_task
async def list_schedules(_, message):
    """
    List all scheduled tasks for current user
    
    Shows task ID, scheduled time, and status for each task
    
    Modified by: justadi
    """
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    tasks = await TaskScheduler.get_scheduled_tasks(user_id)
    if not tasks:
        await send_message(message, "<b>🗓️ No scheduled tasks.</b>")
        return

    text = "<b>🗓️ Scheduled Tasks</b>\n\n"
    for task in tasks[:20]:
        text += (
            f"<b>ID:</b> <code>{task.get('_id', 'N/A')}</code>\n"
            f"<b>When:</b> <code>{task.get('scheduled_for')}</code>\n"
            f"<b>Status:</b> <code>{task.get('status')}</code>\n\n"
        )
    await send_message(message, text)


@new_task
async def cancel_schedule(_, message):
    """
    Cancel a scheduled task
    
    Usage: /unschedule <task_id>
    
    Modified by: justadi
    """
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await send_message(message, "Usage: <code>/unschedule &lt;task_id&gt;</code>")
        return

    task_id = parts[1].strip()
    ok = await TaskScheduler.cancel_scheduled_task(task_id)
    if ok:
        await send_message(message, f"<b>✅ Cancelled:</b> <code>{task_id}</code>")
    else:
        await send_message(message, f"<b>❌ Failed to cancel:</b> <code>{task_id}</code>")