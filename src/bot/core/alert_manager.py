"""
Alert System - Error Detection and Notifications
Tracks errors and sends alerts to users/admins
Safe Innovation Path - Phase 2

Enhanced by: justadi
Date: February 5, 2026
"""

import asyncio
from datetime import UTC, datetime, timedelta
from logging import getLogger
from typing import Any, Callable, Dict, List, Optional, Union

from .alert_manager_models import Alert, AlertSeverity, AlertType
from .config_manager import Config

LOGGER = getLogger(__name__)


class AlertManager:
    """
    Manages alerts and error tracking
    Can trigger notifications via multiple channels
    """

    _instance: Optional["AlertManager"] = None
    _enabled: bool = False
    _alerts: List[Alert] = []
    _subscribers: Dict[str, List[Callable[[Alert], None]]] = {}
    _alert_handlers: List[Callable[[Alert], None]] = []

    def __new__(cls) -> "AlertManager":
        if cls._instance is None:
            cls._instance = super(AlertManager, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            self._alerts = []
            self._subscribers = {}
            self._alert_handlers = []
            self._initialized = True

    def enable(self) -> None:
        """Enable alert system"""
        self._enabled = getattr(Config, "ENABLE_ALERT_SYSTEM", False)

        if self._enabled:
            LOGGER.info("✅ Alert system enabled")
        else:
            LOGGER.debug("Alert system disabled")

    @property
    def is_enabled(self) -> bool:
        """Check if alert system is enabled"""
        return self._enabled

    def register_handler(self, handler: Callable[[Alert], None]) -> None:
        """
        Register a handler function to be called when alerts are triggered

        Args:
            handler: Async function that receives an Alert object
        """
        if handler not in self._alert_handlers:
            self._alert_handlers.append(handler)
            LOGGER.debug(f"Alert handler registered: {handler.__name__}")

    def unregister_handler(self, handler: Callable[[Alert], None]) -> None:
        """Unregister an alert handler"""
        if handler in self._alert_handlers:
            self._alert_handlers.remove(handler)

    async def trigger_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        task_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Optional[Alert]:
        """
        Trigger an alert

        Args:
            alert_type: Type of alert
            severity: Severity level
            title: Alert title
            message: Alert message
            task_id: Associated task ID (if any)
            details: Additional details

        Returns:
            Created Alert object
        """
        if not self._enabled:
            return None

        alert = Alert(alert_type, severity, title, message, task_id, details)
        self._alerts.append(alert)

        LOGGER.warning(f"Alert triggered: {alert.title} ({severity.value})")

        # Call all registered handlers
        for handler in self._alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                LOGGER.error(f"Error in alert handler: {e}")

        # Notify subscribers
        await self._notify_subscribers(alert)

        return alert

    async def _notify_subscribers(self, alert: Alert) -> None:
        """Notify all subscribers about the alert"""
        alert_type_str = alert.alert_type.value

        if alert_type_str in self._subscribers:
            for callback in self._subscribers[alert_type_str]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    LOGGER.error(f"Error notifying subscriber: {e}")

    def subscribe(self, alert_type: AlertType, callback: Callable[[Alert], None]) -> None:
        """
        Subscribe to alerts of a specific type

        Args:
            alert_type: Type of alert to subscribe to
            callback: Function to call when alert is triggered
        """
        key = alert_type.value
        if key not in self._subscribers:
            self._subscribers[key] = []

        if callback not in self._subscribers[key]:
            self._subscribers[key].append(callback)
            LOGGER.debug(f"Subscribed to {key} alerts")

    def unsubscribe(self, alert_type: AlertType, callback: Callable[[Alert], None]) -> None:
        """Unsubscribe from alerts"""
        key = alert_type.value
        if key in self._subscribers and callback in self._subscribers[key]:
            self._subscribers[key].remove(callback)

    def get_alerts(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
    ) -> List[Dict[str, Union[str, int, float]]]:
        """
        Get recent alerts

        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity (None = all)
            alert_type: Filter by alert type (None = all)

        Returns:
            List of alert dictionaries
        """
        if not self._enabled:
            return []

        alerts = self._alerts[-limit:]

        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        # Filter by type if specified
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]

        return [a.to_dict() for a in reversed(alerts)]

    def _count_alerts_by_severity(self) -> Dict[str, int]:
        return {
            "critical": len([a for a in self._alerts if a.severity == AlertSeverity.CRITICAL]),
            "high": len([a for a in self._alerts if a.severity == AlertSeverity.HIGH]),
            "medium": len([a for a in self._alerts if a.severity == AlertSeverity.MEDIUM]),
            "low": len([a for a in self._alerts if a.severity == AlertSeverity.LOW]),
        }

    def _count_alerts_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for alert in self._alerts:
            alert_type = alert.alert_type.value
            counts[alert_type] = counts.get(alert_type, 0) + 1
        return counts

    def get_alert_summary(self) -> Dict[str, Union[bool, int, Dict[str, int]]]:
        """Get summary of alerts"""
        if not self._enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "total_alerts": len(self._alerts),
            "by_severity": self._count_alerts_by_severity(),
            "by_type": self._count_alerts_by_type(),
        }

    def clear_old_alerts(self, hours: int = 24) -> int:
        """
        Clear alerts older than specified hours

        Args:
            hours: Hours to keep alerts for

        Returns:
            Number of alerts cleared
        """
        if not self._enabled:
            return 0

        cutoff_time = datetime.now(UTC) - timedelta(hours=hours)
        original_count = len(self._alerts)

        self._alerts = [
            a for a in self._alerts
            if a.timestamp > cutoff_time
        ]

        cleared = original_count - len(self._alerts)
        if cleared > 0:
            LOGGER.info(f"Cleared {cleared} old alerts")

        return cleared


# Singleton instance
alert_manager = AlertManager()
