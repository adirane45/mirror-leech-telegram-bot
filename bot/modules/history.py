from time import time

from .. import download_history
from ..helper.ext_utils.bot_utils import new_task
from ..helper.ext_utils.history_utils import format_history
from ..helper.ext_utils.status_utils import get_readable_time
from ..helper.telegram_helper.message_utils import send_message


@new_task
async def download_history_view(_, message):
    """Show download history and stats"""
    total = len(download_history)
    success = len([h for h in download_history if h.get("status") == "success"])
    failed = total - success

    stats = (
        "<b>📜 Download History</b>\n"
        f"<b>Total:</b> {total} | <b>✅ Success:</b> {success} | <b>❌ Failed:</b> {failed}\n\n"
    )

    if total:
        stats += format_history(list(download_history), limit=10)
    else:
        stats += "No history yet."

    await send_message(message, stats)
