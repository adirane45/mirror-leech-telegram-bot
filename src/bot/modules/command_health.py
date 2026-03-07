"""
Command Health Monitoring Telegram Commands

Provides /health and /cmdstats commands for monitoring command execution health.
"""

from pyrogram import Client
from pyrogram.filters import command
from pyrogram.types import Message

from .. import LOGGER
from ..helper.telegram_helper.bot_commands import BotCommands
from ..helper.telegram_helper.filters import CustomFilters
from ..core.command_health_monitor import command_health_monitor
from ..core.command_alert_system import command_alert_system


async def health_report_handler(client: Client, message: Message):
    """
    Show command health report.
    
    Usage: /health
    """
    try:
        if not command_health_monitor._enabled:
            await message.reply_text(
                "⚠️ <b>Command Health Monitoring is disabled</b>\n\n"
                "Enable it in bot configuration to track command execution health.",
                parse_mode="html"
            )
            return
        
        # Get health report from alert system
        report = command_alert_system.get_health_report()
        
        # Add timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report += f"\n\n<i>Generated: {timestamp}</i>"
        
        await message.reply_text(report, parse_mode="html")
        
    except Exception as e:
        LOGGER.error(f"Error in health_report_handler: {e}")
        await message.reply_text(
            f"❌ Error generating health report:\n<code>{str(e)}</code>",
            parse_mode="html"
        )


async def command_stats_handler(client: Client, message: Message):
    """
    Show detailed command statistics.
    
    Usage: /cmdstats [command_name]
    """
    try:
        if not command_health_monitor._enabled:
            await message.reply_text(
                "⚠️ Command monitoring is disabled.",
                parse_mode="html"
            )
            return
        
        # Parse command name if provided
        parts = message.text.split()
        target_cmd = parts[1] if len(parts) > 1 else None
        
        if target_cmd:
            # Show specific command stats
            metrics = command_health_monitor.get_metrics(target_cmd)
            
            if not metrics:
                await message.reply_text(
                    f"❌ No data found for command: <code>/{target_cmd}</code>",
                    parse_mode="html"
                )
                return
            
            # Format detailed stats
            status_icon = "🟢" if metrics.success_rate >= 95 else "🟡" if metrics.success_rate >= 80 else "🔴"
            
            report = (
                f"{status_icon} <b>Command Statistics: /{target_cmd}</b>\n\n"
                f"<b>Execution Summary:</b>\n"
                f"├─ Total executions: <code>{metrics.total_executions}</code>\n"
                f"├─ Successful: <code>{metrics.successful}</code>\n"
                f"├─ Failed: <code>{metrics.failed}</code>\n"
                f"├─ Timeouts: <code>{metrics.timeout}</code>\n"
                f"├─ Errors: <code>{metrics.error}</code>\n"
                f"└─ Success rate: <code>{metrics.success_rate:.1f}%</code>\n\n"
                f"<b>Performance:</b>\n"
                f"└─ Average duration: <code>{metrics.avg_duration_ms:.1f}ms</code>\n\n"
            )
            
            if metrics.last_failure:
                from datetime import datetime
                time_str = metrics.last_failure.strftime("%H:%M:%S")
                report += (
                    f"<b>Last Failure:</b>\n"
                    f"├─ Time: <code>{time_str}</code>\n"
                    f"├─ Consecutive failures: <code>{metrics.consecutive_failures}</code>\n"
                    f"└─ Error: <code>{metrics.last_error or 'N/A'}</code>\n"
                )
            
        else:
            # Show all commands summary
            all_metrics = command_health_monitor.get_all_metrics()
            
            if not all_metrics:
                await message.reply_text(
                    "📊 No command execution data available yet.",
                    parse_mode="html"
                )
                return
            
            report = "<b>📊 Command Execution Statistics</b>\n\n"
            
            # Sort by total executions
            sorted_metrics = sorted(
                all_metrics.items(),
                key=lambda x: x[1].total_executions,
                reverse=True
            )
            
            for cmd, metrics in sorted_metrics[:15]:  # Top 15
                status_icon = "🟢" if metrics.success_rate >= 95 else "🟡" if metrics.success_rate >= 80 else "🔴"
                report += (
                    f"{status_icon} <code>/{cmd:<12}</code> "
                    f"{metrics.success_rate:>5.1f}% "
                    f"({metrics.successful}/{metrics.total_executions})\n"
                )
            
            if len(all_metrics) > 15:
                report += f"\n<i>... and {len(all_metrics) - 15} more commands</i>\n"
            
            report += "\n<i>Use /cmdstats &lt;command&gt; for detailed stats</i>"
        
        await message.reply_text(report, parse_mode="html")
        
    except Exception as e:
        LOGGER.error(f"Error in command_stats_handler: {e}")
        await message.reply_text(
            f"❌ Error: <code>{str(e)}</code>",
            parse_mode="html"
        )


async def reset_command_stats_handler(client: Client, message: Message):
    """
    Reset command statistics (admin only).
    
    Usage: /resetstats [command_name]
    """
    try:
        parts = message.text.split()
        target_cmd = parts[1] if len(parts) > 1 else None
        
        if target_cmd:
            command_health_monitor.reset_metrics(target_cmd)
            await message.reply_text(
                f"✅ Statistics reset for: <code>/{target_cmd}</code>",
                parse_mode="html"
            )
        else:
            command_health_monitor.reset_metrics()
            await message.reply_text(
                "✅ All command statistics have been reset.",
                parse_mode="html"
            )
        
    except Exception as e:
        LOGGER.error(f"Error in reset_command_stats_handler: {e}")
        await message.reply_text(
            f"❌ Error: <code>{str(e)}</code>",
            parse_mode="html"
        )
