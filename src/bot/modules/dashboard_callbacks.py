# Dashboard Quick Actions Callback Handler
# Handle interactive button clicks from dashboard
# Modified by: justadi

from ..helper.ext_utils.bot_utils import new_task
from .queue_manager import show_queue
from .search_filter import search_tasks
from .settings_ui import settings_panel
from .speedtest import speedtest
from .stats import bot_stats
from .status import task_status


@new_task
async def dashboard_callback_handler(_, query):
    """Handle quick action button clicks from dashboard"""
    data = query.data
    message = query.message

    await query.answer()

    if data == "quick_queue":
        # Show queue management
        await show_queue(_, message)
    elif data == "quick_status":
        # Show task status
        await task_status(_, message)
    elif data == "quick_stats":
        # Show bot statistics
        await bot_stats(_, message)
    elif data == "quick_speed":
        # Run speedtest
        await speedtest(_, message)
    elif data == "quick_search":
        # Show search interface
        await search_tasks(_, message)
    elif data == "quick_settings":
        # Show settings panel
        await settings_panel(_, message)
