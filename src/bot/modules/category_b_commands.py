"""
Admin Commands for Category B Features
Provides Telegram commands to monitor and manage advanced features
"""

from logging import getLogger

from pyrogram import Client, filters
from pyrogram.types import Message

from ..core.category_b_integration import category_b
from ..helper.telegram_helper.filters import CustomFilters
from ..helper.telegram_helper.message_utils import send_message

LOGGER = getLogger(__name__)


async def queue_status(client: Client, message: Message):
    """Show queue status and statistics"""
    try:
        stats = await category_b.get_queue_stats()

        if not stats:
            await send_message(message, "⚠️ No queue statistics available.")
            return

        # Build status message
        status_lines = ["📊 **Queue Status Report**\n"]

        for queue_name, queue_stats in stats.items():
            status_lines.append(
                f"\n**{queue_name.upper()} Queue:**\n"
                f"├ Queued: {queue_stats.queued_tasks}\n"
                f"├ Running: {queue_stats.running_tasks}\n"
                f"├ Completed: {queue_stats.completed_tasks}\n"
                f"├ Failed: {queue_stats.failed_tasks}\n"
                f"├ Avg Wait: {queue_stats.average_wait_time:.1f}s\n"
                f"└ Avg Exec: {queue_stats.average_execution_time:.1f}s"
            )

        await send_message(message, "\n".join(status_lines))

    except Exception as e:
        LOGGER.error(f"Error in queue_status: {e}", exc_info=True)
        await send_message(message, f"❌ Error: {e}")


async def dlq_status(client: Client, message: Message):
    """Show Dead-Letter Queue status"""
    try:
        count = await category_b.get_dlq_count()
        tasks = await category_b.list_dlq_tasks()

        if count == 0:
            await send_message(message, "✅ DLQ is empty - no failed tasks.")
            return

        # Build DLQ report
        lines = [f"📮 **Dead-Letter Queue Status**\n", f"Total Failed Tasks: {count}\n"]

        for task in tasks[:10]:  # Show first 10
            icon = "🔄" if task["recoverable"] else "❌"
            lines.append(
                f"\n{icon} **{task['task_id']}**\n"
                f"├ Operation: {task['operation']}\n"
                f"├ Error Type: {task['error_type']}\n"
                f"├ Failures: {task['failure_count']}\n"
                f"└ Message: {task['error_message'][:50]}..."
            )

        if count > 10:
            lines.append(f"\n... and {count - 10} more tasks")

        await send_message(message, "\n".join(lines))

    except Exception as e:
        LOGGER.error(f"Error in dlq_status: {e}", exc_info=True)
        await send_message(message, f"❌ Error: {e}")


async def circuit_status(client: Client, message: Message):
    """Show circuit breaker status"""
    try:
        breakers = {
            "Telegram API": category_b.telegram_breaker,
            "Google Drive API": category_b.gdrive_breaker,
            "Aria2 Client": category_b.aria2_breaker,
        }

        lines = ["🔌 **Circuit Breaker Status**\n"]

        for name, breaker in breakers.items():
            state_icons = {
                "closed": "🟢",
                "open": "🔴",
                "half_open": "🟡",
            }

            icon = state_icons.get(breaker.state.value, "❓")
            metrics = breaker.metrics

            lines.append(
                f"\n{icon} **{name}**\n"
                f"├ State: {breaker.state.value.upper()}\n"
                f"├ Success Rate: {metrics.success_rate() * 100:.1f}%\n"
                f"├ Total Calls: {metrics.total_calls}\n"
                f"├ Successful: {metrics.successful_calls}\n"
                f"├ Failed: {metrics.failed_calls}\n"
                f"└ Rejected: {metrics.rejected_calls}"
            )

        await send_message(message, "\n".join(lines))

    except Exception as e:
        LOGGER.error(f"Error in circuit_status: {e}", exc_info=True)
        await send_message(message, f"❌ Error: {e}")


async def boost_task(client: Client, message: Message):
    """Boost task priority in queue"""
    try:
        args = message.text.split(maxsplit=2)
        if len(args) < 2:
            await send_message(
                message,
                "Usage: `/boost <task_id> [queue_name]`\n"
                "Example: `/boost download_file123 default`"
            )
            return

        task_id = args[1]
        queue_name = args[2] if len(args) > 2 else "default"

        success = await category_b.queue_manager.boost_task(task_id, queue_name)

        if success:
            await send_message(message, f"⬆️ Task '{task_id}' priority boosted!")
        else:
            await send_message(message, f"❌ Task '{task_id}' not found in queue.")

    except Exception as e:
        LOGGER.error(f"Error in boost_task: {e}", exc_info=True)
        await send_message(message, f"❌ Error: {e}")


async def cancel_task(client: Client, message: Message):
    """Cancel task from queue"""
    try:
        args = message.text.split(maxsplit=2)
        if len(args) < 2:
            await send_message(
                message,
                "Usage: `/cancel <task_id> [queue_name]`\n"
                "Example: `/cancel download_file123 default`"
            )
            return

        task_id = args[1]
        queue_name = args[2] if len(args) > 2 else "default"

        success = await category_b.queue_manager.cancel_task(task_id, queue_name)

        if success:
            await send_message(message, f"🗑️ Task '{task_id}' cancelled.")
        else:
            await send_message(message, f"❌ Task '{task_id}' not found.")

    except Exception as e:
        LOGGER.error(f"Error in cancel_task: {e}", exc_info=True)
        await send_message(message, f"❌ Error: {e}")


async def my_queue_position(client: Client, message: Message):
    """Check user's position in queue"""
    try:
        user_id = message.from_user.id
        position = await category_b.queue_manager.get_user_position(user_id, "default")

        if position is None or position == 0:
            await send_message(message, "✅ You have no tasks in the queue.")
        else:
            await send_message(
                message,
                f"📍 Your Position: You have **{position}** task(s) waiting in the queue."
            )

    except Exception as e:
        LOGGER.error(f"Error in my_queue_position: {e}", exc_info=True)
        await send_message(message, f"❌ Error: {e}")


async def system_health(client: Client, message: Message):
    """Show system health status"""
    try:
        from ..core.health_monitor import health_monitor

        report = await health_monitor.get_report()

        if not report:
            await send_message(message, "⚠️ No health report available.")
            return

        status_icons = {
            "healthy": "✅",
            "degraded": "⚠️",
            "critical": "❌",
            "unknown": "❓",
        }

        icon = status_icons.get(report.overall_status.value, "❓")

        lines = [
            f"🏥 **System Health Report**\n",
            f"\n{icon} Overall Status: **{report.overall_status.value.upper()}**",
            f"⏱️ Uptime: {health_monitor.get_uptime_hours():.1f} hours\n",
        ]

        # Component status
        if report.components:
            lines.append("\n**Component Status:**")
            for component_type, metric in report.components.items():
                comp_icon = status_icons.get(metric.status.value, "❓")
                lines.append(
                    f"{comp_icon} {component_type.value}: {metric.status.value}"
                )

        await send_message(message, "\n".join(lines))

    except Exception as e:
        LOGGER.error(f"Error in system_health: {e}", exc_info=True)
        await send_message(message, f"❌ Error: {e}")


async def category_b_help(client: Client, message: Message):
    """Show Category B features help"""
    help_text = """
🔧 **Category B Advanced Features**

**Queue Management:**
`/qstatus` - View queue statistics
`/myqueue` - Check your queue position
`/boost <task_id>` - Boost task priority (Admin)
`/cancel <task_id>` - Cancel task from queue (Admin)

**Error Recovery:**
`/dlq` - View Dead-Letter Queue status (Admin)

**System Monitoring:**
`/circuits` - View circuit breaker status (Admin)
`/health` - View system health status (Admin)

**Features:**
✅ Smart Retry with DLQ
✅ Parallel Chunk Downloads (3-5x speed)
✅ Priority Queue System
✅ Circuit Breaker Protection
✅ Auto-Recovery System
"""

    await send_message(message, help_text)


def register_category_b_handlers(app: Client):
    """Register Category B command handlers"""

    # Admin-only commands
    app.add_handler(
        filters.command("qstatus") & CustomFilters.sudo,
        queue_status,
    )

    app.add_handler(
        filters.command("dlq") & CustomFilters.sudo,
        dlq_status,
    )

    app.add_handler(
        filters.command("circuits") & CustomFilters.sudo,
        circuit_status,
    )

    app.add_handler(
        filters.command("boost") & CustomFilters.sudo,
        boost_task,
    )

    app.add_handler(
        filters.command("cancel") & CustomFilters.sudo,
        cancel_task,
    )

    app.add_handler(
        filters.command("health") & CustomFilters.sudo,
        system_health,
    )

    # User commands
    app.add_handler(
        filters.command("myqueue"),
        my_queue_position,
    )

    app.add_handler(
        filters.command(["categoryb", "catb", "advancedhelp"]),
        category_b_help,
    )

    LOGGER.info("✅ Category B command handlers registered")
