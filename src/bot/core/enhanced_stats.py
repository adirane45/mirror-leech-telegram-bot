"""
Enhanced Stats Module
Provides comprehensive stats and analytics with beautiful formatting and visualizations
"""

from typing import Dict, Tuple, Optional
from time import time
from psutil import (
    disk_usage,
    cpu_percent,
    virtual_memory,
    cpu_count,
    boot_time,
    net_io_counters,
)
from datetime import datetime, timedelta

from ..helper.ext_utils.status_utils import get_readable_file_size, get_readable_time


class ProgressBar:
    """Create beautiful progress bars with various styles"""

    @staticmethod
    def filled_bar(percentage: float, length: int = 10, show_percent: bool = True) -> str:
        """
        Create a filled progress bar
        
        Args:
            percentage: Progress percentage (0-100)
            length: Length of the bar
            show_percent: Show percentage text
            
        Returns:
            Formatted progress bar string
        """
        if percentage < 0:
            percentage = 0
        elif percentage > 100:
            percentage = 100

        filled = int(length * percentage / 100)
        bar = "█" * filled + "░" * (length - filled)
        
        if show_percent:
            return f"{bar} {percentage:.1f}%"
        return bar

    @staticmethod
    def emoji_bar(percentage: float) -> str:
        """Create emoji-based progress bar"""
        emojis = ["🟫", "⬜"]
        filled = int(percentage / 10)
        return "".join(["🟦"] * filled + emojis[0:10-filled])

    @staticmethod
    def blocks_bar(percentage: float, length: int = 20) -> str:
        """Create block-based progress bar"""
        filled = int(length * percentage / 100)
        return f"[{'▰' * filled}{'▱' * (length - filled)}] {percentage:.0f}%"


class HealthIndicator:
    """Provide health status indicators with emojis and colors"""

    # Health status emojis
    STATUS_EXCELLENT = "🟢"  # > 80%
    STATUS_GOOD = "🟡"      # 50-80%
    STATUS_WARNING = "🟠"   # 20-50%
    STATUS_CRITICAL = "🔴"  # < 20%
    STATUS_OFFLINE = "⚫"   # 0%

    @staticmethod
    def get_health_indicator(percentage: int) -> str:
        """Get health indicator emoji based on percentage"""
        if percentage >= 80:
            return HealthIndicator.STATUS_EXCELLENT
        elif percentage >= 50:
            return HealthIndicator.STATUS_GOOD
        elif percentage >= 20:
            return HealthIndicator.STATUS_WARNING
        elif percentage > 0:
            return HealthIndicator.STATUS_CRITICAL
        return HealthIndicator.STATUS_OFFLINE

    @staticmethod
    def get_resource_status(name: str, value: float, max_value: Optional[float] = None) -> str:
        """
        Get formatted resource status with indicator
        
        Args:
            name: Resource name (CPU, RAM, DISK, etc.)
            value: Current value
            max_value: Maximum value (for percentage calculation)
            
        Returns:
            Formatted status string
        """
        if max_value is not None:
            percentage = (value / max_value * 100) if max_value > 0 else 0
        else:
            percentage = value

        indicator = HealthIndicator.get_health_indicator(int(percentage))
        return f"{indicator} {name}: {percentage:.1f}%"


class SystemStats:
    """Collect and format system statistics"""

    @staticmethod
    def get_cpu_stats() -> Dict:
        """Get comprehensive CPU statistics"""
        per_cpu = cpu_percent(interval=1, percpu=True)
        return {
            "overall": cpu_percent(interval=1),
            "per_cpu": per_cpu,
            "cores_total": cpu_count(),
            "cores_physical": cpu_count(logical=False),
        }

    @staticmethod
    def get_memory_stats() -> Dict:
        """Get comprehensive memory statistics"""
        memory = virtual_memory()
        return {
            "total": memory.total,
            "used": memory.used,
            "available": memory.available,
            "percent": memory.percent,
            "percent_readable": f"{memory.percent:.1f}%",
        }

    @staticmethod
    def get_disk_stats(path: str = "/") -> Dict:
        """Get comprehensive disk statistics"""
        disk = disk_usage(path)
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
            "percent_readable": f"{disk.percent:.1f}%",
        }

    @staticmethod
    def get_network_stats() -> Dict:
        """Get network I/O statistics"""
        net = net_io_counters()
        return {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        }

    @staticmethod
    def format_cpu_details() -> str:
        """Format detailed CPU information"""
        stats = SystemStats.get_cpu_stats()
        per_cpu_str = " | ".join(
            [f"CPU{i+1}: {round(p)}%" for i, p in enumerate(stats["per_cpu"])]
        )
        
        text = f"<b>CPU Usage:</b> {stats['overall']}%\n"
        text += f"<code>{per_cpu_str}</code>\n"
        text += f"Cores: {stats['cores_physical']} (Physical) / {stats['cores_total']} (Total)"
        return text

    @staticmethod
    def format_memory_details() -> str:
        """Format detailed memory information"""
        stats = SystemStats.get_memory_stats()
        
        text = f"<b>Memory Usage:</b>\n"
        text += f"Total: {get_readable_file_size(stats['total'])}\n"
        text += f"Used: {get_readable_file_size(stats['used'])} ({stats['percent_readable']})\n"
        text += f"Available: {get_readable_file_size(stats['available'])}"
        return text

    @staticmethod
    def format_disk_details(path: str = "/") -> str:
        """Format detailed disk information"""
        stats = SystemStats.get_disk_stats(path)
        
        text = f"<b>Disk Usage ({path}):</b>\n"
        text += f"Total: {get_readable_file_size(stats['total'])}\n"
        text += f"Used: {get_readable_file_size(stats['used'])} ({stats['percent_readable']})\n"
        text += f"Free: {get_readable_file_size(stats['free'])}"
        return text

    @staticmethod
    def format_network_stats() -> str:
        """Format network statistics"""
        stats = SystemStats.get_network_stats()
        
        text = f"<b>Network I/O:</b>\n"
        text += f"Sent: {get_readable_file_size(stats['bytes_sent'])}\n"
        text += f"Received: {get_readable_file_size(stats['bytes_recv'])}"
        return text


class TaskStats:
    """Calculate and format task statistics"""

    @staticmethod
    def calculate_total_speed(tasks: list) -> str:
        """Calculate total speed from all active tasks"""
        total_speed = 0
        for task in tasks:
            try:
                speed = task.speed()
                if isinstance(speed, str):
                    # Parse speed string like "10 MB/s"
                    parts = speed.split()
                    if len(parts) >= 1:
                        try:
                            value = float(parts[0])
                            unit = parts[1] if len(parts) > 1 else "B"
                            multipliers = {
                                "B": 1,
                                "KB": 1024,
                                "MB": 1024**2,
                                "GB": 1024**3,
                            }
                            total_speed += value * multipliers.get(unit, 1)
                        except ValueError:
                            pass
            except Exception:
                pass

        return get_readable_file_size(total_speed, "/s")

    @staticmethod
    def calculate_total_size(tasks: list) -> str:
        """Calculate total size of all active tasks"""
        total_size = 0
        for task in tasks:
            try:
                size_str = task.size()
                if isinstance(size_str, str):
                    # Parse size string
                    parts = size_str.split()
                    if len(parts) >= 1:
                        try:
                            value = float(parts[0])
                            unit = parts[1] if len(parts) > 1 else "B"
                            multipliers = {
                                "B": 1,
                                "KB": 1024,
                                "MB": 1024**2,
                                "GB": 1024**3,
                                "TB": 1024**4,
                            }
                            total_size += value * multipliers.get(unit, 1)
                        except ValueError:
                            pass
            except Exception:
                pass

        return get_readable_file_size(total_size)

    @staticmethod
    def estimate_total_eta(tasks: list) -> str:
        """Estimate total ETA from all active tasks"""
        max_eta_seconds = 0
        for task in tasks:
            try:
                eta_str = task.eta()
                if isinstance(eta_str, str):
                    # Parse ETA like "2h 30m"
                    eta_seconds = 0
                    parts = eta_str.split()
                    for i, part in enumerate(parts):
                        if part.endswith("d"):
                            eta_seconds += int(part[:-1]) * 86400
                        elif part.endswith("h"):
                            eta_seconds += int(part[:-1]) * 3600
                        elif part.endswith("m"):
                            eta_seconds += int(part[:-1]) * 60
                        elif part.endswith("s"):
                            eta_seconds += int(part[:-1])
                    max_eta_seconds = max(max_eta_seconds, eta_seconds)
            except Exception:
                pass

        return get_readable_time(max_eta_seconds)


class StatsFormatter:
    """Format statistics for display"""

    @staticmethod
    def format_system_dashboard(bot_start_time: float, download_dir: str = "/") -> str:
        """Create a beautiful system dashboard"""
        cpu_stats = SystemStats.get_cpu_stats()
        mem_stats = SystemStats.get_memory_stats()
        disk_stats = SystemStats.get_disk_stats(download_dir)
        uptime = get_readable_time(time() - bot_start_time)
        os_uptime = get_readable_time(time() - boot_time())

        # Create progress bars
        cpu_bar = ProgressBar.filled_bar(cpu_stats["overall"], length=10)
        mem_bar = ProgressBar.filled_bar(mem_stats["percent"], length=10)
        disk_bar = ProgressBar.filled_bar(disk_stats["percent"], length=10)

        # Get health indicators
        cpu_health = HealthIndicator.get_health_indicator(int(cpu_stats["overall"]))
        mem_health = HealthIndicator.get_health_indicator(int(mem_stats["percent"]))
        disk_health = HealthIndicator.get_health_indicator(int(disk_stats["percent"]))

        text = "<b>📊 SYSTEM DASHBOARD</b>\n"
        text += "=" * 40 + "\n\n"

        text += f"<b>⏱️  Uptime:</b>\n"
        text += f"  Bot: {uptime}\n"
        text += f"  System: {os_uptime}\n\n"

        text += f"<b>🖥️  CPU Usage:</b>\n"
        text += f"  {cpu_health} {cpu_bar}\n\n"

        text += f"<b>💾 Memory Usage:</b>\n"
        text += f"  {mem_health} {mem_bar}\n"
        text += f"  Used: {get_readable_file_size(mem_stats['used'])} / {get_readable_file_size(mem_stats['total'])}\n\n"

        text += f"<b>💿 Disk Usage:</b>\n"
        text += f"  {disk_health} {disk_bar}\n"
        text += f"  Free: {get_readable_file_size(disk_stats['free'])} / {get_readable_file_size(disk_stats['total'])}\n\n"

        text += f"<b>🌐 Network:</b>\n"
        net_stats = SystemStats.get_network_stats()
        text += f"  ⬆️  Sent: {get_readable_file_size(net_stats['bytes_sent'])}\n"
        text += f"  ⬇️  Recv: {get_readable_file_size(net_stats['bytes_recv'])}\n"

        return text

    @staticmethod
    def format_quick_stats(
        active_tasks: int,
        total_downloaded: str,
        total_uploaded: str,
        cpu_percent: float,
        mem_percent: float,
        free_disk: str,
    ) -> str:
        """Create quick stats summary card"""
        text = "<b>📈 QUICK STATS</b>\n"
        text += "=" * 30 + "\n"
        text += f"▶️  Active Tasks: <code>{active_tasks}</code>\n"
        text += f"📥 Downloaded: <code>{total_downloaded}</code>\n"
        text += f"📤 Uploaded: <code>{total_uploaded}</code>\n"
        text += f"🖥️  CPU: {HealthIndicator.get_health_indicator(int(cpu_percent))} <code>{cpu_percent:.1f}%</code>\n"
        text += f"💾 RAM: {HealthIndicator.get_health_indicator(int(mem_percent))} <code>{mem_percent:.1f}%</code>\n"
        text += f"💿 Free Disk: <code>{free_disk}</code>\n"
        return text

    @staticmethod
    def format_detailed_stats(
        tasks: list,
        cpu_percent: float,
        mem_percent: float,
        disk_percent: float,
        free_disk: str,
    ) -> str:
        """Create detailed statistics report"""
        total_size = TaskStats.calculate_total_size(tasks)
        total_speed = TaskStats.calculate_total_speed(tasks)
        total_eta = TaskStats.estimate_total_eta(tasks)

        text = "<b>📊 DETAILED STATISTICS</b>\n"
        text += "=" * 40 + "\n\n"

        text += "<b>Task Summary:</b>\n"
        text += f"  Total Tasks: {len(tasks)}\n"
        text += f"  Combined Size: {total_size}\n"
        text += f"  Combined Speed: {total_speed}\n"
        text += f"  Estimated ETA: {total_eta}\n\n"

        text += "<b>System Resources:</b>\n"
        text += f"  {ProgressBar.blocks_bar(cpu_percent, 15)} CPU\n"
        text += f"  {ProgressBar.blocks_bar(mem_percent, 15)} RAM\n"
        text += f"  {ProgressBar.blocks_bar(disk_percent, 15)} DISK\n"
        text += f"  Free Space: {free_disk}\n"

        return text
