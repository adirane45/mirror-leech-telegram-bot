"""
Command Failure Alert System Integration

Sets up Telegram notifications for command failures.
Integrates with CommandHealthMonitor to send alerts to OWNER_ID or alert chat.
"""

import asyncio
from typing import Any, Optional

from .. import LOGGER
from .command_health_monitor import CommandExecution, CommandHealthMonitor, CommandMetrics


class CommandAlertSystem:
    """Manages command failure alerts and notifications"""

    def __init__(self) -> None:
        self.monitor = CommandHealthMonitor.get_instance()
        self.owner_id: Optional[int] = None
        self.alert_chat_id: Optional[int] = None
        self.tag_owners_on_critical = True
        self.enabled = False

    def configure(self, owner_id: int, alert_chat_id: Optional[int] = None, enabled: bool = True) -> None:
        """
        Configure alert system.

        Args:
            owner_id: Telegram user ID to receive alerts
            alert_chat_id: Optional group/channel chat ID for alerts (defaults to owner_id)
            enabled: Whether to send alerts
        """
        self.owner_id = owner_id
        self.alert_chat_id = alert_chat_id or owner_id
        self.enabled = enabled
        LOGGER.info(f"✅ Command Alert System configured | Owner: {owner_id} | Enabled: {enabled}")

    async def register_alerts_for_command(self, command: str, tg_client: Any = None) -> None:
        """Register alert callbacks for a specific command"""
        if not self.enabled or not tg_client:
            return

        async def send_alert(cmd: str, metrics: CommandMetrics, execution: CommandExecution) -> None:
            """Alert callback that sends Telegram message"""
            try:
                message = self._format_alert_message(cmd, metrics, execution)
                await tg_client.send_message(self.alert_chat_id, message)
            except Exception as e:
                LOGGER.error(f"Failed to send command failure alert: {e}")

        self.monitor.register_alert_callback(command, send_alert)

    async def register_alerts_for_all_commands(self, commands: list[str], tg_client: Any = None) -> None:
        """Register alert callbacks for multiple commands"""
        tasks = [
            self.register_alerts_for_command(cmd, tg_client)
            for cmd in commands
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    def _format_alert_message(command: str, metrics: CommandMetrics, execution: CommandExecution) -> str:
        """Format alert message for Telegram"""
        timestamp = execution.timestamp.strftime("%H:%M:%S")

        message = (
            f"🚨 <b>Command Failure Alert</b>\n\n"
            f"<b>Command:</b> <code>/{command}</code>\n"
            f"<b>User ID:</b> <code>{execution.user_id}</code>\n"
            f"<b>Status:</b> <code>{execution.status.value.upper()}</code>\n"
            f"<b>Timestamp:</b> {timestamp}\n"
            f"<b>Duration:</b> {execution.duration_ms:.0f}ms\n\n"
            f"<b>Metrics Summary:</b>\n"
            f"├─ Total executions: <code>{metrics.total_executions}</code>\n"
            f"├─ Success rate: <code>{metrics.success_rate:.1f}%</code>\n"
            f"├─ Consecutive failures: <code>{metrics.consecutive_failures}</code>\n"
            f"└─ Last error: <code>{metrics.last_error or 'N/A'}</code>"
        )

        if execution.error:
            message += f"\n\n<b>Error Details:</b>\n<code>{execution.error[:200]}</code>"

        return message

    def get_health_report(self) -> str:
        """Get command health report for Telegram"""
        summary = self.monitor.get_health_summary()

        message = (
            f"📊 <b>Command Health Report</b>\n\n"
            f"<b>Status:</b> {summary.get('status', 'unknown').upper()}\n"
            f"<b>Commands Monitored:</b> {summary.get('total_commands', 0)}\n"
            f"├─ Healthy: {summary.get('healthy', 0)}\n"
            f"├─ Degraded: {summary.get('degraded', 0)}\n"
            f"└─ Failing: {summary.get('failing', 0)}"
        )

        # Add detailed metrics for failing commands
        failing_commands = [
            m for m in self.monitor.get_all_metrics().values()
            if m.success_rate < 80
        ]

        if failing_commands:
            message += "\n\n<b>Failing Commands:</b>\n"
            for metrics in failing_commands[:5]:  # Show top 5
                message += (
                    f"├─ <code>/{metrics.command}</code>: "
                    f"{metrics.success_rate:.1f}% "
                    f"({metrics.failed} failures)\n"
                )

        return message


# Global instance
command_alert_system = CommandAlertSystem()
