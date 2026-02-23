"""
Enhanced Dashboard Handler Module
Provides handlers for accessing enhanced stats and feedback through bot commands
"""

from time import time
from asyncio import iscoroutinefunction
from psutil import cpu_percent, virtual_memory, disk_usage

from .. import bot_start_time, task_dict, task_dict_lock, DOWNLOAD_DIR
from ..helper.ext_utils.status_utils import get_readable_file_size, get_readable_time
from ..helper.telegram_helper.message_utils import send_message
from ..helper.telegram_helper.button_build import ButtonMaker
from ..helper.ext_utils.bot_utils import new_task
from ..core.enhanced_stats import (
    ProgressBar,
    HealthIndicator,
    SystemStats,
    StatsFormatter,
    TaskStats,
)
from ..core.enhanced_status_integration import EnhancedStatusBuilder, EnhancedDashboard


@new_task
async def enhanced_stats_handler(_, message):
    """Handle /estats command - Show enhanced statistics"""
    text = StatsFormatter.format_system_dashboard(bot_start_time, DOWNLOAD_DIR)
    await send_message(message, text)


@new_task
async def enhanced_dashboard_handler(_, message):
    """Handle /edash command - Show enhanced dashboard"""
    async with task_dict_lock:
        tasks = list(task_dict.values())

    text = EnhancedDashboard.create_detailed_view(tasks, bot_start_time, DOWNLOAD_DIR)
    await send_message(message, text)


@new_task
async def enhanced_quick_status_handler(_, message):
    """Handle /equick command - Show quick status"""
    async with task_dict_lock:
        task_count = len(task_dict)

    cpu = cpu_percent(interval=1)
    ram = virtual_memory().percent
    disk_free = get_readable_file_size(disk_usage(DOWNLOAD_DIR).free)

    text = EnhancedDashboard.create_quick_view(task_count, cpu, ram, disk_free)
    await send_message(message, text)


@new_task
async def enhanced_analytics_handler(_, message):
    """Handle /eanalytics command - Show task analytics"""
    async with task_dict_lock:
        tasks = list(task_dict.values())

    if not tasks:
        text = "No active tasks to analyze"
    else:
        text = EnhancedDashboard.create_analytics_view(tasks)

    await send_message(message, text)


@new_task
async def resource_monitor_handler(_, message):
    """Handle /rmon command - Show detailed resource monitoring"""
    cpu_stats = SystemStats.get_cpu_stats()
    mem_stats = SystemStats.get_memory_stats()
    disk_stats = SystemStats.get_disk_stats(DOWNLOAD_DIR)
    net_stats = SystemStats.get_network_stats()

    text = "<b>🖥️ RESOURCE MONITOR</b>\n"
    text += "=" * 40 + "\n\n"

    # CPU Details
    text += "<b>CPU Usage:</b>\n"
    text += f"{ProgressBar.blocks_bar(cpu_stats['overall'], 20)} Overall\n"
    text += f"Cores: {cpu_stats['cores_physical']} (Physical) / {cpu_stats['cores_total']} (Total)\n\n"

    # Memory Details
    text += "<b>Memory Usage:</b>\n"
    text += f"{ProgressBar.blocks_bar(mem_stats['percent'], 20)}\n"
    text += f"Total: {get_readable_file_size(mem_stats['total'])}\n"
    text += f"Used: {get_readable_file_size(mem_stats['used'])}\n"
    text += f"Available: {get_readable_file_size(mem_stats['available'])}\n\n"

    # Disk Details
    text += "<b>Disk Usage:</b>\n"
    text += f"{ProgressBar.blocks_bar(disk_stats['percent'], 20)}\n"
    text += f"Total: {get_readable_file_size(disk_stats['total'])}\n"
    text += f"Used: {get_readable_file_size(disk_stats['used'])}\n"
    text += f"Free: {get_readable_file_size(disk_stats['free'])}\n\n"

    # Network Details
    text += "<b>Network I/O:</b>\n"
    text += f"Sent: {get_readable_file_size(net_stats['bytes_sent'])}\n"
    text += f"Received: {get_readable_file_size(net_stats['bytes_recv'])}\n"

    await send_message(message, text)


@new_task
async def system_health_handler(_, message):
    """Handle /health command - Show system health report"""
    cpu = cpu_percent(interval=1)
    mem = virtual_memory().percent
    disk = disk_usage(DOWNLOAD_DIR).percent

    text = "<b>🏥 SYSTEM HEALTH REPORT</b>\n"
    text += "=" * 40 + "\n\n"

    # CPU Health
    cpu_health = HealthIndicator.get_health_indicator(int(cpu))
    text += f"CPU: {cpu_health} {ProgressBar.filled_bar(cpu, length=12)}\n"

    # Memory Health
    mem_health = HealthIndicator.get_health_indicator(int(mem))
    text += f"RAM: {mem_health} {ProgressBar.filled_bar(mem, length=12)}\n"

    # Disk Health
    disk_health = HealthIndicator.get_health_indicator(int(disk))
    text += f"DISK: {disk_health} {ProgressBar.filled_bar(disk, length=12)}\n\n"

    # Overall Status
    overall_health = int((cpu + mem + disk) / 3)
    overall_indicator = HealthIndicator.get_health_indicator(overall_health)

    text += f"Overall Health: {overall_indicator} "

    if overall_health >= 80:
        text += "Excellent"
    elif overall_health >= 50:
        text += "Good"
    elif overall_health >= 20:
        text += "Fair - Monitor closely"
    else:
        text += "Critical - Action required"

    await send_message(message, text)


@new_task
async def progress_summary_handler(_, message):
    """Handle /psummary command - Show progress summary of all tasks"""
    async with task_dict_lock:
        tasks = list(task_dict.values())

    if not tasks:
        text = "No active tasks"
        await send_message(message, text)
        return

    text = "<b>📊 PROGRESS SUMMARY</b>\n"
    text += "=" * 40 + "\n\n"

    # Summary statistics
    text += f"Total Tasks: {len(tasks)}\n"

    if len(tasks) > 0:
        total_size = TaskStats.calculate_total_size(tasks)
        total_speed = TaskStats.calculate_total_speed(tasks)
        total_eta = TaskStats.estimate_total_eta(tasks)

        text += f"Combined Size: {total_size}\n"
        text += f"Combined Speed: {total_speed}\n"
        text += f"Est. Total ETA: {total_eta}\n\n"

    # Task breakdown
    text += "<b>Task breakdown:</b>\n"
    for i, task in enumerate(tasks[:5], 1):  # Show top 5
        try:
            if iscoroutinefunction(task.status):
                tstatus = await task.status()
            else:
                tstatus = task.status()

            progress = task.progress() if hasattr(task, "progress") else 0
            text += f"{i}. {task.name()[:30]}\n"
            text += f"   {ProgressBar.filled_bar(progress, length=12)}\n"
        except Exception:
            pass

    if len(tasks) > 5:
        text += f"\n... and {len(tasks) - 5} more tasks"

    await send_message(message, text)


@new_task
async def comparison_stats_handler(_, message):
    """Handle /cstats command - Compare system resources before/after"""
    # This would compare current stats with baseline
    # For now, just show current snapshot

    text = "<b>📈 COMPARISON STATS</b>\n"
    text += "=" * 40 + "\n\n"

    cpu = cpu_percent(interval=1)
    mem = virtual_memory().percent
    disk = disk_usage(DOWNLOAD_DIR).percent

    text += "<b>Current Snapshot:</b>\n"
    text += f"CPU: {ProgressBar.filled_bar(cpu, length=15)}\n"
    text += f"RAM: {ProgressBar.filled_bar(mem, length=15)}\n"
    text += f"DISK: {ProgressBar.filled_bar(disk, length=15)}\n\n"

    # Provide recommendations
    text += "<b>💡 Recommendations:</b>\n"

    if cpu > 80:
        text += "• CPU usage is high - consider pausing some tasks\n"
    if mem > 80:
        text += "• Memory usage is high - consider clearing cache or restarting\n"
    if disk > 90:
        text += "• Disk space is critically low - archive or delete completed tasks\n"

    if cpu <= 80 and mem <= 80 and disk <= 90:
        text += "• System is running normally ✅"

    await send_message(message, text)


# Note: Handlers are now registered in bot/core/handlers.py in the add_handlers() function
