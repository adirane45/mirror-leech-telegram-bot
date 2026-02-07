"""
Quick Integration Examples for Enhanced Stats & Feedback
Copy & paste ready code snippets
"""

# ============================================================================
# EXAMPLE 1: Simple Enhanced Status Display
# ============================================================================

from bot.core.enhanced_stats import ProgressBar, HealthIndicator
from bot.helper.telegram_helper.message_utils import send_message

async def show_simple_status(_, message):
    """Display a simple enhanced status bar"""
    cpu_percent = 75.5
    mem_percent = 62.3
    
    text = "<b>📊 System Status</b>\n"
    text += f"CPU: {ProgressBar.filled_bar(cpu_percent, length=12)}\n"
    text += f"RAM: {ProgressBar.filled_bar(mem_percent, length=12)}\n"
    
    await send_message(message, text)


# ============================================================================
# EXAMPLE 2: Health-Aware Status Display
# ============================================================================

async def show_health_status(_, message):
    """Display status with health indicators"""
    cpu = 45.0
    mem = 72.0
    disk = 85.0
    
    cpu_health = HealthIndicator.get_health_indicator(int(cpu))
    mem_health = HealthIndicator.get_health_indicator(int(mem))
    disk_health = HealthIndicator.get_health_indicator(int(disk))
    
    text = "<b>🏥 System Health</b>\n"
    text += f"{cpu_health} CPU:  {cpu:.1f}%\n"
    text += f"{mem_health} RAM:  {mem:.1f}%\n"
    text += f"{disk_health} DISK: {disk:.1f}%\n"
    
    await send_message(message, text)


# ============================================================================
# EXAMPLE 3: Complete System Dashboard
# ============================================================================

from bot.core.enhanced_stats import StatsFormatter
from bot import bot_start_time, DOWNLOAD_DIR

async def show_dashboard(_, message):
    """Display complete system dashboard"""
    dashboard = StatsFormatter.format_system_dashboard(bot_start_time, DOWNLOAD_DIR)
    await send_message(message, dashboard)


# ============================================================================
# EXAMPLE 4: Task Progress Tracking
# ============================================================================

from bot.core.enhanced_feedback import ProgressTracker
from bot.helper.ext_utils.status_utils import get_readable_file_size, get_readable_time

async def track_file_download(file_path, file_size):
    """Example of tracking file download progress"""
    tracker = ProgressTracker(
        task_id=file_path,
        task_name=f"Downloading {file_path}",
        total=file_size
    )
    
    # Simulate download
    downloaded = 0
    chunk_size = 1024 * 1024  # 1 MB chunks
    
    while downloaded < file_size:
        # Simulate downloading
        downloaded += chunk_size
        tracker.update(min(downloaded, file_size))
        
        # Get formatted output
        progress_text = tracker.format_progress_bar()
        percentage = tracker.get_progress_percentage()
        
        print(f"{progress_text} - {percentage:.1f}%")
    
    # Final info
    return tracker.format_details()


# ============================================================================
# EXAMPLE 5: Enhanced Task Status Message
# ============================================================================

from bot.core.enhanced_status_integration import EnhancedStatusBuilder

async def show_enhanced_task_status(_, message, task):
    """Display a single task with enhanced formatting"""
    task_msg = await EnhancedStatusBuilder.build_task_message(
        task=task,
        index=1,
        include_progress_bar=True,
        include_health=True,
        compact=False
    )
    
    await send_message(message, task_msg)


# ============================================================================
# EXAMPLE 6: Real-time Feedback for Long Operations
# ============================================================================

from bot.core.enhanced_feedback import RealtimeFeedback, FeedbackFormatter

async def long_operation_with_feedback(_, message):
    """Example of providing real-time feedback during operation"""
    feedback = RealtimeFeedback()
    operation_id = "operation_1"
    
    # Start feedback
    await feedback.start_feedback(
        operation_id,
        "Processing Files",
        "Starting operation..."
    )
    
    # Simulate work with updates
    for i in range(1, 6):
        await feedback.update_feedback(
            operation_id,
            f"Processing file {i}/5...",
            append=False
        )
        # Do some work...
        await asyncio.sleep(1)
    
    # End feedback
    result = await feedback.end_feedback(
        operation_id,
        "Operation completed successfully!"
    )
    
    # Send final message
    final_msg = FeedbackFormatter.format_task_completed(
        "File Processing",
        size="500 MB",
        time_taken=get_readable_time(result.get("duration", 0))
    )
    
    await send_message(message, final_msg)


# ============================================================================
# EXAMPLE 7: Combined Status with Progress
# ============================================================================

from psutil import cpu_percent, virtual_memory, disk_usage

async def show_full_status(_, message, tasks):
    """Display full status with task progress and system resources"""
    
    cpu = cpu_percent(interval=1)
    mem = virtual_memory().percent
    disk_free = get_readable_file_size(disk_usage("/").free)
    uptime = get_readable_time(time() - bot_start_time)
    
    # Count tasks by type
    task_counts = {
        "download": sum(1 for t in tasks if "Download" in str(t.status())),
        "upload": sum(1 for t in tasks if "Upload" in str(t.status())),
        "paused": sum(1 for t in tasks if "Paused" in str(t.status())),
        "queued": sum(1 for t in tasks if "Queue" in str(t.status())),
        "other": len(tasks) - sum(1 for t in tasks if any(x in str(t.status()) for x in ["Download", "Upload", "Paused", "Queue"]))
    }
    
    # Build complete message
    text = await EnhancedStatusBuilder.build_full_status_message(
        tasks=tasks,
        task_counts=task_counts,
        cpu_percent=cpu,
        mem_percent=mem,
        disk_free=disk_free,
        uptime=uptime,
        include_progress_bars=True
    )
    
    await send_message(message, text)


# ============================================================================
# EXAMPLE 8: Quick Analytics Summary
# ============================================================================

from bot.core.enhanced_stats import TaskStats

async def show_analytics(_, message, tasks):
    """Show quick analytics of all tasks"""
    
    if len(tasks) == 0:
        await send_message(message, "No active tasks")
        return
    
    total_size = TaskStats.calculate_total_size(tasks)
    total_speed = TaskStats.calculate_total_speed(tasks)
    estimated_eta = TaskStats.estimate_total_eta(tasks)
    
    text = "<b>📈 QUICK ANALYTICS</b>\n"
    text += f"Total Tasks: {len(tasks)}\n"
    text += f"Combined Size: {total_size}\n"
    text += f"Combined Speed: {total_speed}\n"
    text += f"Estimated ETA: {estimated_eta}\n"
    
    await send_message(message, text)


# ============================================================================
# EXAMPLE 9: Error Handler with Good Feedback
# ============================================================================

from bot.core.enhanced_status_integration import MessageEnhancer

async def handle_operation_error(_, message, error):
    """Handle errors with user-friendly feedback"""
    
    error_msg = MessageEnhancer.format_error_with_feedback(
        "Operation Failed",
        str(error),
        suggestion="Please check your internet connection and try again"
    )
    
    await send_message(message, error_msg)


# ============================================================================
# EXAMPLE 10: System Health Check with Recommendations
# ============================================================================

from bot.core.enhanced_stats import HealthIndicator, ProgressBar

async def check_health_with_recommendations(_, message):
    """Check system health and provide recommendations"""
    
    cpu = cpu_percent(interval=1)
    mem = virtual_memory().percent
    disk = disk_usage("/").percent
    
    text = "<b>🏥 HEALTH CHECK</b>\n\n"
    
    # Display status
    text += f"{ProgressBar.blocks_bar(cpu, 20)} CPU\n"
    text += f"{ProgressBar.blocks_bar(mem, 20)} RAM\n"
    text += f"{ProgressBar.blocks_bar(disk, 20)} DISK\n\n"
    
    # Add recommendations
    text += "<b>💡 Recommendations:</b>\n"
    
    has_issues = False
    
    if cpu > 85:
        text += "⚠️ CPU usage is high - consider pausing some tasks\n"
        has_issues = True
    
    if mem > 85:
        text += "⚠️ Memory usage is high - restart if issues persist\n"
        has_issues = True
    
    if disk > 90:
        text += "🚨 Disk space critical - archive completed tasks\n"
        has_issues = True
    
    if not has_issues:
        text += "✅ All systems running normally\n"
    
    await send_message(message, text)


# ============================================================================
# SETUP INSTRUCTIONS
# ============================================================================

"""
To use these modules in your bot:

1. Import the modules at the top of your command handler file:
   from bot.core.enhanced_stats import ProgressBar, HealthIndicator, StatsFormatter
   from bot.core.enhanced_feedback import ProgressTracker, FeedbackFormatter
   from bot.core.enhanced_status_integration import EnhancedStatusBuilder

2. Use the examples above in your command handlers

3. Register handlers in your __main__.py:
   from bot.modules.enhanced_dashboard import (
       enhanced_stats_handler,
       enhanced_dashboard_handler,
       enhanced_quick_status_handler
   )
   
   app.on_message(filters.command("estats"), enhanced_stats_handler)
   app.on_message(filters.command("edash"), enhanced_dashboard_handler)
   app.on_message(filters.command("equick"), enhanced_quick_status_handler)

4. Test with:
   /estats - Show fancy stats
   /edash - Show dashboard
   /equick - Quick status
"""

# ============================================================================
# COMMON USE CASES QUICK REFERENCE
# ============================================================================

"""
Use Case 1: Show simple progress bar
→ Use: ProgressBar.filled_bar(percentage)

Use Case 2: Show health-aware metrics
→ Use: HealthIndicator.get_health_indicator(value)

Use Case 3: Display system dashboard
→ Use: StatsFormatter.format_system_dashboard(bot_start_time)

Use Case 4: Track download progress
→ Use: ProgressTracker class

Use Case 5: Show task details
→ Use: EnhancedStatusBuilder.build_task_message()

Use Case 6: Real-time feedback
→ Use: RealtimeFeedback class

Use Case 7: Error messages
→ Use: FeedbackFormatter.format_task_failed()

Use Case 8: Success messages
→ Use: FeedbackFormatter.format_task_completed()

Use Case 9: Detailed stats report
→ Use: StatsFormatter.format_detailed_stats()

Use Case 10: Multiple task summary
→ Use: TaskStats.calculate_* methods
"""
