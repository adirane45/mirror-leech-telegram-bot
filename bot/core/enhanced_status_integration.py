"""
Enhanced Status Integration Module
Integrates enhanced stats and feedback into existing bot handlers
"""

from typing import Optional, List, Dict
from asyncio import iscoroutinefunction
from html import escape
from time import time

from ..helper.ext_utils.status_utils import (
    get_readable_file_size,
    get_readable_time,
    STATUS_EMOJI,
)
from .enhanced_stats import ProgressBar, HealthIndicator, StatsFormatter, SystemStats
from .enhanced_feedback import FeedbackFormatter, ProgressTracker


class EnhancedStatusBuilder:
    """Build enhanced status messages with better formatting"""

    @staticmethod
    async def build_task_message(
        task,
        index: int = 1,
        include_progress_bar: bool = True,
        include_health: bool = True,
        compact: bool = False,
    ) -> str:
        """Build enhanced status message for a single task"""
        try:
            # Get task status
            if iscoroutinefunction(task.status):
                tstatus = await task.status()
            else:
                tstatus = task.status()

            # Get status emoji
            status_emoji = STATUS_EMOJI.get(tstatus, "⚙️")

            # Build message
            msg = f"<b>{index}. {status_emoji} {tstatus}:</b> "
            msg += f"<code>{escape(task.name())}</code>\n"

            if compact:
                # Compact view - just essential info
                if hasattr(task, "speed") and callable(task.speed):
                    speed = task.speed()
                    msg += f"Speed: {speed}"
                return msg

            # Detailed view
            if hasattr(task.listener, "subname") and task.listener.subname:
                msg += f"<i>{task.listener.subname}</i>\n"

            # Progress section
            if (
                tstatus not in ["Seed", "QueueUp"]
                and hasattr(task.listener, "progress")
                and task.listener.progress
            ):
                progress = task.progress()
                
                if include_progress_bar:
                    msg += f"Progress: {ProgressBar.filled_bar(progress, length=12)}\n"
                
                # File processing info
                if hasattr(task.listener, "subname") and task.listener.subname:
                    subsize = f"/{get_readable_file_size(task.listener.subsize)}"
                    ac = len(task.listener.files_to_proceed)
                    count = f"{task.listener.proceed_count}/{ac or '?'}"
                    msg += f"Count: {count}\n"
                else:
                    subsize = ""

                # Size and speed
                if hasattr(task, "processed_bytes"):
                    msg += f"Size: {task.processed_bytes()}{subsize} of {task.size()}\n"

                if hasattr(task, "speed"):
                    speed = task.speed()
                    if include_health:
                        health = HealthIndicator.get_health_indicator(
                            int(task.listener.speed_limit / 100 * 10) if hasattr(task.listener, "speed_limit") else 50
                        )
                        msg += f"Speed: {health} {speed}\n"
                    else:
                        msg += f"Speed: {speed}\n"

                if hasattr(task, "eta"):
                    msg += f"ETA: ⏳ {task.eta()}\n"

                # Torrent specific info
                if hasattr(task.listener, "is_torrent") and task.listener.is_torrent:
                    try:
                        if hasattr(task, "seeders_num"):
                            msg += f"Seeders: {task.seeders_num()} | Leechers: {task.leechers_num()}\n"
                    except Exception:
                        pass

            elif tstatus == "Seed" and hasattr(task, "size"):
                msg += f"Size: {task.size()}\n"
                if hasattr(task, "seed_speed"):
                    msg += f"Speed: {task.seed_speed()}\n"
                if hasattr(task, "uploaded_bytes"):
                    msg += f"Uploaded: {task.uploaded_bytes()}\n"
                if hasattr(task, "ratio"):
                    msg += f"Ratio: {task.ratio()} | "
                if hasattr(task, "seeding_time"):
                    msg += f"Time: {task.seeding_time()}\n"

            else:
                if hasattr(task, "size"):
                    msg += f"Size: {task.size()}\n"

            # Cancel command
            if hasattr(task, "gid"):
                from ..helper.telegram_helper.bot_commands import BotCommands
                msg += f"<code>/{BotCommands.CancelTaskCommand[1]} {task.gid()}</code>"

            return msg

        except Exception as e:
            return f"Error building task message: {str(e)}"

    @staticmethod
    def build_status_header(
        download_count: int,
        upload_count: int,
        paused_count: int,
        queued_count: int,
        other_count: int,
    ) -> str:
        """Build enhanced status header with counts and visual indicators"""
        text = "<b>📌 STATUS OVERVIEW</b>\n"
        text += "=" * 40 + "\n"
        text += f"▶️ Downloads: {download_count} | "
        text += f"⬆️ Uploads: {upload_count} | "
        text += f"⏸️ Paused: {paused_count} | "
        text += f"⏳ Queued: {queued_count} | "
        text += f"⚙️ Other: {other_count}\n\n"
        return text

    @staticmethod
    def build_resource_footer(
        cpu_percent: float,
        mem_percent: float,
        disk_free: str,
        uptime: str,
        include_health: bool = True,
    ) -> str:
        """Build enhanced resource footer"""
        text = "\n" + "=" * 40 + "\n"
        text += "<b>📊 SYSTEM RESOURCES</b>\n"
        
        if include_health:
            cpu_health = HealthIndicator.get_health_indicator(int(cpu_percent))
            mem_health = HealthIndicator.get_health_indicator(int(mem_percent))
            
            text += f"{cpu_health} CPU: {cpu_percent:.1f}% | "
            text += f"{mem_health} RAM: {mem_percent:.1f}% | "
        else:
            text += f"CPU: {cpu_percent:.1f}% | RAM: {mem_percent:.1f}% | "
        
        text += f"💿 Free: {disk_free}\n"
        text += f"⏱️ Uptime: {uptime}"
        
        return text

    @staticmethod
    def build_full_status_message(
        tasks: List,
        task_counts: Dict[str, int],
        cpu_percent: float,
        mem_percent: float,
        disk_free: str,
        uptime: str,
        include_progress_bars: bool = True,
        compact: bool = False,
    ) -> str:
        """Build a complete enhanced status message"""
        text = EnhancedStatusBuilder.build_status_header(
            task_counts.get("download", 0),
            task_counts.get("upload", 0),
            task_counts.get("paused", 0),
            task_counts.get("queued", 0),
            task_counts.get("other", 0),
        )

        if not tasks:
            text += "<i>No active tasks</i>\n"
        else:
            for index, task in enumerate(tasks, 1):
                task_msg = EnhancedStatusBuilder.build_task_message(
                    task,
                    index,
                    include_progress_bar=include_progress_bars,
                    compact=compact,
                )
                text += task_msg + "\n\n"

        text += EnhancedStatusBuilder.build_resource_footer(
            cpu_percent,
            mem_percent,
            disk_free,
            uptime,
            include_health=not compact,
        )

        return text


class EnhancedDashboard:
    """Create enhanced dashboard with various views"""

    @staticmethod
    def create_quick_view(
        active_tasks: int,
        cpu_percent: float,
        ram_percent: float,
        disk_free: str,
    ) -> str:
        """Create quick dashboard view"""
        text = "<b>⚡ QUICK STATUS</b>\n"
        text += f"Tasks Running: <code>{active_tasks}</code>\n"
        text += f"CPU: <code>{cpu_percent:.1f}%</code>\n"
        text += f"RAM: <code>{ram_percent:.1f}%</code>\n"
        text += f"Disk Free: <code>{disk_free}</code>"
        return text

    @staticmethod
    def create_detailed_view(
        tasks: List,
        bot_start_time: float,
        download_dir: str = "/",
    ) -> str:
        """Create detailed dashboard view"""
        # System stats
        cpu_stats = SystemStats.get_cpu_stats()
        mem_stats = SystemStats.get_memory_stats()
        disk_stats = SystemStats.get_disk_stats(download_dir)
        net_stats = SystemStats.get_network_stats()

        text = "<b>📊 DETAILED DASHBOARD</b>\n\n"

        # System information
        text += "<b>System:</b>\n"
        text += f"Uptime: {get_readable_time(time() - bot_start_time)}\n"
        text += f"CPU: {ProgressBar.blocks_bar(cpu_stats['overall'], 15)}\n"
        text += f"RAM: {ProgressBar.blocks_bar(mem_stats['percent'], 15)}\n"
        text += f"Disk: {ProgressBar.blocks_bar(disk_stats['percent'], 15)}\n\n"

        # Task information
        text += f"<b>Tasks:</b> {len(tasks)}\n"
        text += f"Free Space: {get_readable_file_size(disk_stats['free'])}\n"
        text += f"Network: ⬆️ {get_readable_file_size(net_stats['bytes_sent'])} | "
        text += f"⬇️ {get_readable_file_size(net_stats['bytes_recv'])}\n"

        return text

    @staticmethod
    def create_analytics_view(tasks: List) -> str:
        """Create analytics dashboard view"""
        from .enhanced_stats import TaskStats

        if not tasks:
            return "<i>No tasks to analyze</i>"

        total_size = TaskStats.calculate_total_size(tasks)
        total_speed = TaskStats.calculate_total_speed(tasks)
        total_eta = TaskStats.estimate_total_eta(tasks)

        text = "<b>📈 ANALYTICS</b>\n\n"
        text += f"Total Size: {total_size}\n"
        text += f"Combined Speed: {total_speed}\n"
        text += f"Est. Total ETA: {total_eta}\n"
        text += f"Active Tasks: {len(tasks)}"

        return text


class MessageEnhancer:
    """Enhance existing messages with better formatting"""

    @staticmethod
    def add_buttons_to_message(
        message_text: str,
        task_count: int,
        include_refresh: bool = True,
        include_view_modes: bool = True,
    ) -> str:
        """Add button hints to message text"""
        hints = []
        if include_refresh:
            hints.append("♻️ Refresh")
        if include_view_modes:
            hints.append("👁️ View")
        if task_count > 5:
            hints.append("📖 Pages")

        if hints:
            message_text += "\n\n<i>Available: " + " | ".join(hints) + "</i>"

        return message_text

    @staticmethod
    def enhance_task_display(
        task_message: str,
        warning_threshold: float = 85.0,
        critical_threshold: float = 95.0,
    ) -> str:
        """Enhance task message with warnings if needed"""
        # This can be extended to add warnings based on resource usage
        return task_message

    @staticmethod
    def format_error_with_feedback(
        error_title: str,
        error_message: str,
        suggestion: str = "",
    ) -> str:
        """Format error messages with helpful feedback"""
        text = f"{FeedbackFormatter.format_task_failed(error_title)}\n"
        text += f"Details: {error_message}"
        if suggestion:
            text += f"\n\n💡 <i>Suggestion: {suggestion}</i>"
        return text

    @staticmethod
    def format_success_with_feedback(
        action: str,
        result: str = "",
        duration: str = "",
    ) -> str:
        """Format success messages with positive feedback"""
        text = f"{FeedbackFormatter.format_task_completed(action)}\n"
        if result:
            text += f"Result: {result}"
        if duration:
            text += f"\n⏱️ Completed in: {duration}"
        return text
