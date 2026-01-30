from asyncio import sleep
from time import time

from .. import task_dict, task_dict_lock, LOGGER
from ..core.config_manager import Config
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.status_utils import get_task_by_gid, get_all_tasks, MirrorStatus
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.telegram_helper.interactive_keyboards import InteractiveKeyboards
from ..helper.telegram_helper.filters import CustomFilters
from ..helper.telegram_helper.message_utils import (
    send_message,
    edit_message,
    delete_message,
)

# Queue manager state - stores task metadata
queue_info = {}  # gid -> {"priority": int, "timeout": int, "paused": bool, "created_at": time}


@new_task
async def show_queue(_, message):
    """Display all active tasks with options to manage them - Modified by: justadi"""
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    
    async with task_dict_lock:
        tasks = list(task_dict.values())
    
    if not tasks:
        await send_message(message, "❌ <b>No Active Tasks!</b>\n\n<i>Modified by: justadi</i>")
        return
    
    # Build task list with buttons
    msg_text = "<b>📋 Task Queue Manager</b>\n"
    msg_text += "<i>Enhanced UI by: justadi</i>\n\n"
    msg_text += f"<b>Total Tasks: {len(tasks)}</b>\n\n"
    
    for idx, task in enumerate(tasks, 1):
        status = task.status()
        gid = task.gid()
        name = task.name()[:35]  # Truncate long names
        
        paused = queue_info.get(gid, {}).get("paused", False)
        priority = queue_info.get(gid, {}).get("priority", 0)
        
        status_emoji = "⏸️" if paused else "▶️"
        priority_str = f" [P{priority}]" if priority != 0 else ""
        
        msg_text += f"{idx}. {status_emoji} <code>{name}</code>{priority_str}\n"
        msg_text += f"   <b>Status:</b> {status} | <code>{gid[:8]}</code>\n\n"
    
    msg_text += "<b>⚡ Quick Actions Available:</b>\n"
    msg_text += "• Use buttons below to manage tasks\n"
    msg_text += "• Tap any task for options\n"
    
    queue_msg = await send_message(message, msg_text, InteractiveKeyboards.queue_management())


@new_task
async def pause_queue(_, message):
    """Pause a specific task or all tasks - Modified by: justadi"""
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    msg = message.text.split()
    
    if len(msg) < 2:
        await send_message(
            message, 
            "⏸️ <b>Pause Task</b>\n\nUsage: /pqueue [gid]\n\n<i>Modified by: justadi</i>"
        )
        return
    
    gid = msg[1] if len(msg) > 1 else None
    
    if not gid:
        reply_to_id = message.reply_to_message_id
        if reply_to_id:
            async with task_dict_lock:
                task = task_dict.get(reply_to_id)
                if task:
                    gid = task.gid()
    
    if not gid:
        await send_message(message, "❌ <b>GID not found!</b>")
        return
    
    task = await get_task_by_gid(gid)
    if task is None:
        await send_message(message, f"❌ <b>Task not found!</b>\n<code>{gid}</code>")
        return
    
    # Check authorization
    if (
        Config.OWNER_ID != user_id
        and task.listener.user_id != user_id
    ):
        await send_message(message, "❌ <b>Unauthorized!</b> This task is not for you!")
        return
    
    try:
        obj = task.task()
        # Pause the download if it has pause method
        if hasattr(obj, 'pause'):
            await obj.pause()
            queue_info[gid] = queue_info.get(gid, {})
            queue_info[gid]["paused"] = True
            resp = await send_message(
                message, 
                f"✅ <b>Task Paused!</b>\n<code>{gid[:12]}</code>\n\n<i>Modified by: justadi</i>",
                InteractiveKeyboards.task_menu(gid)
            )
        else:
            await send_message(message, f"⚠️ <b>Not Supported!</b>\nThis task type doesn't support pause!")
    except Exception as e:
        LOGGER.error(f"Error pausing task {gid}: {e}")
        await send_message(message, f"❌ <b>Error:</b> {str(e)}")


@new_task
async def resume_queue(_, message):
    """Resume a paused task - Modified by: justadi"""
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    msg = message.text.split()
    
    if len(msg) < 2:
        await send_message(
            message, 
            "▶️ <b>Resume Task</b>\n\nUsage: /rqueue [gid]\n\n<i>Modified by: justadi</i>"
        )
        return
    
    gid = msg[1] if len(msg) > 1 else None
    
    if not gid:
        reply_to_id = message.reply_to_message_id
        if reply_to_id:
            async with task_dict_lock:
                task = task_dict.get(reply_to_id)
                if task:
                    gid = task.gid()
    
    if not gid:
        await send_message(message, "❌ <b>GID not found!</b>")
        return
    
    task = await get_task_by_gid(gid)
    if task is None:
        await send_message(message, f"❌ <b>Task not found!</b>\n<code>{gid}</code>")
        return
    
    # Check authorization
    if (
        Config.OWNER_ID != user_id
        and task.listener.user_id != user_id
    ):
        await send_message(message, "❌ <b>Unauthorized!</b> This task is not for you!")
        return
    
    try:
        obj = task.task()
        # Resume the download if it has resume method
        if hasattr(obj, 'resume'):
            await obj.resume()
            queue_info[gid] = queue_info.get(gid, {})
            queue_info[gid]["paused"] = False
            resp = await send_message(
                message, 
                f"✅ <b>Task Resumed!</b>\n<code>{gid[:12]}</code>\n\n<i>Modified by: justadi</i>",
                InteractiveKeyboards.task_menu(gid)
            )
        else:
            await send_message(message, f"⚠️ <b>Not Supported!</b>\nThis task type doesn't support resume!")
    except Exception as e:
        LOGGER.error(f"Error resuming task {gid}: {e}")
        await send_message(message, f"❌ <b>Error:</b> {str(e)}")


@new_task
async def set_priority(_, message):
    """Set task priority - Modified by: justadi"""
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    msg = message.text.split()
    
    if len(msg) < 3:
        await send_message(
            message,
            "⬆️ <b>Set Priority</b>\n\n"
            "Usage: /prqueue [gid] [priority]\n\n"
            "Priority Levels:\n"
            "• <code>1</code> = ⬆️ High\n"
            "• <code>0</code> = ➡️ Normal\n"
            "• <code>-1</code> = ⬇️ Low\n\n"
            "<i>Modified by: justadi</i>"
        )
        return
    
    gid = msg[1]
    try:
        priority = int(msg[2])
        if priority not in [-1, 0, 1]:
            await send_message(message, "❌ <b>Invalid Priority!</b>\nMust be -1, 0, or 1")
            return
    except (ValueError, IndexError):
        await send_message(message, "❌ <b>Error!</b> Invalid priority value")
        return
    
    task = await get_task_by_gid(gid)
    if task is None:
        await send_message(message, f"❌ <b>Task not found!</b>\n<code>{gid}</code>")
        return
    
    # Check authorization
    if (
        Config.OWNER_ID != user_id
        and task.listener.user_id != user_id
    ):
        await send_message(message, "❌ <b>Unauthorized!</b> This task is not for you!")
        return
    
    queue_info[gid] = queue_info.get(gid, {})
    queue_info[gid]["priority"] = priority
    
    priority_text = {-1: "⬇️ Low", 0: "➡️ Normal", 1: "⬆️ High"}[priority]
    resp = await send_message(
        message,
        f"✅ <b>Priority Updated!</b>\n"
        f"GID: <code>{gid[:12]}</code>\n"
        f"Priority: <b>{priority_text}</b>\n\n"
        f"<i>Modified by: justadi</i>",
        InteractiveKeyboards.task_menu(gid)
    )


@new_task
async def pause_all_queue(_, message):
    """Pause all active tasks - Modified by: justadi"""
    if message.from_user.id != Config.OWNER_ID:
        await send_message(message, "❌ <b>Owner Only!</b>\nThis command is only for the owner!")
        return
    
    async with task_dict_lock:
        tasks = list(task_dict.values())
    
    if not tasks:
        await send_message(message, "❌ <b>No Active Tasks!</b>")
        return
    
    paused_count = 0
    for task in tasks:
        try:
            obj = task.task()
            if hasattr(obj, 'pause'):
                await obj.pause()
                queue_info[task.gid()] = queue_info.get(task.gid(), {})
                queue_info[task.gid()]["paused"] = True
                paused_count += 1
        except:
            pass
    
    await send_message(
        message, 
        f"✅ <b>All Tasks Paused!</b>\n\n"
        f"<b>Paused:</b> {paused_count}/{len(tasks)}\n\n"
        f"<i>Modified by: justadi</i>",
        InteractiveKeyboards.quick_actions()
    )


@new_task
async def resume_all_queue(_, message):
    """Resume all paused tasks - Modified by: justadi"""
    if message.from_user.id != Config.OWNER_ID:
        await send_message(message, "❌ <b>Owner Only!</b>\nThis command is only for the owner!")
        return
    
    async with task_dict_lock:
        tasks = list(task_dict.values())
    
    if not tasks:
        await send_message(message, "❌ <b>No Active Tasks!</b>")
        return
    
    resumed_count = 0
    for task in tasks:
        try:
            obj = task.task()
            if hasattr(obj, 'resume'):
                await obj.resume()
                queue_info[task.gid()] = queue_info.get(task.gid(), {})
                queue_info[task.gid()]["paused"] = False
                resumed_count += 1
        except:
            pass
    
    await send_message(
        message, 
        f"✅ <b>All Tasks Resumed!</b>\n\n"
        f"<b>Resumed:</b> {resumed_count}/{len(tasks)}\n\n"
        f"<i>Modified by: justadi</i>",
        InteractiveKeyboards.quick_actions()
    )
