# Task Categorization Commands
# Organize tasks into custom categories
# Better task management and organization
# Modified by: justadi

from ..core.task_categorizer import TaskCategorizer
from ..helper.ext_utils.bot_utils import new_task
from ..helper.telegram_helper.message_utils import send_message
from .. import task_dict, task_dict_lock


@new_task
async def manage_categories(_, message):
    """Create/list/delete categories"""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 2:
        await send_message(
            message,
            "<b>📂 Categories</b>\n\n"
            "Usage:\n"
            "<code>/category list</code>\n"
            "<code>/category add &lt;name&gt;</code>\n"
            "<code>/category del &lt;name&gt;</code>\n"
            "<code>/category stats</code>",
        )
        return

    action = parts[1].lower()

    if action == "list":
        cats = await TaskCategorizer.get_all_categories()
        if not cats:
            await send_message(message, "<b>No categories found.</b>")
            return
        text = "<b>📂 Categories</b>\n\n"
        for name, cat in cats.items():
            text += f"• <code>{name}</code> ({cat.get('task_count', 0)})\n"
        await send_message(message, text)
        return

    if action == "stats":
        stats = await TaskCategorizer.get_category_stats()
        text = "<b>📊 Category Stats</b>\n\n"
        text += f"Total: {stats.get('total_tasks', 0)} tasks\n"
        for name, data in stats.get("categories", {}).items():
            text += f"• {name}: {data.get('count', 0)}\n"
        await send_message(message, text)
        return

    if len(parts) < 3:
        await send_message(message, "<b>❌ Missing category name.</b>")
        return

    name = parts[2].strip()
    if action == "add":
        ok = await TaskCategorizer.create_category(name)
        msg = "<b>✅ Category created.</b>" if ok else "<b>❌ Failed to create.</b>"
        await send_message(message, msg)
    elif action == "del":
        ok = await TaskCategorizer.delete_category(name)
        msg = "<b>✅ Category deleted.</b>" if ok else "<b>❌ Failed to delete.</b>"
        await send_message(message, msg)
    else:
        await send_message(message, "<b>❌ Invalid action.</b>")


@new_task
async def categorize_task(_, message):
    """Assign a task to a category"""
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await send_message(
            message,
            "Usage: <code>/categorize &lt;gid&gt; &lt;category&gt;</code>",
        )
        return

    gid = parts[1].strip()
    category = parts[2].strip()

    target = None
    async with task_dict_lock:
        for task in task_dict.values():
            try:
                if task.gid() == gid:
                    target = task
                    break
            except Exception:
                continue

    if not target:
        await send_message(message, "<b>❌ Task not found.</b>")
        return

    ok = await TaskCategorizer.categorize_task(gid, category)
    msg = "<b>✅ Task categorized.</b>" if ok else "<b>❌ Failed to categorize.</b>"
    await send_message(message, msg)