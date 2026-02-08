"""
Alert System - Error Detection and Notifications
Tracks errors and sends alerts to users/admins
Safe Innovation Path - Phase 2

Enhanced by: justadi
Date: February 5, 2026
"""

import asyncio
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Callable
from enum import Enum
from logging import getLogger

from .config_manager import Config

LOGGER = getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert types"""
    DOWNLOAD_FAILED = "download_failed"
    UPLOAD_FAILED = "upload_failed"
    DISK_FULL = "disk_full"
    MEMORY_HIGH = "memory_high"
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    PERMISSION_DENIED = "permission_denied"
    NETWORK_ERROR = "network_error"
    CUSTOM = "custom"


class Alert:
    """Represents a single alert"""

    def __init__(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        task_id: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        self.alert_type = alert_type
        self.severity = severity
        self.title = title
        self.message = message
        self.task_id = task_id
        self.details = details or {}
        self.timestamp = datetime.now(UTC)
        self.id = f"{self.timestamp.timestamp()}_{self.alert_type.value}"

    def to_dict(self):
        """Convert alert to dictionary"""
        return {
            "id": self.id,
            "type": self.alert_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat(),
            "details": self.details,
        }


class AlertManager:
    """
    Manages alerts and error tracking
    Can trigger notifications via multiple channels
    """

    _instance = None
    _enabled = False
    _alerts: List[Alert] = []
    _subscribers: Dict[str, List[Callable]] = {}
    _alert_handlers: List[Callable] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AlertManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._alerts = []
            self._subscribers = {}
            self._alert_handlers = []
            self._initialized = True

    def enable(self):
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

    def register_handler(self, handler: Callable):
        """
        Register a handler function to be called when alerts are triggered

        Args:
            handler: Async function that receives an Alert object
        """
        if handler not in self._alert_handlers:
            self._alert_handlers.append(handler)
            LOGGER.debug(f"Alert handler registered: {handler.__name__}")

    def unregister_handler(self, handler: Callable):
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
        details: Optional[Dict] = None,
    ) -> Alert:
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

    async def _notify_subscribers(self, alert: Alert):
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

    def subscribe(self, alert_type: AlertType, callback: Callable):
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

    def unsubscribe(self, alert_type: AlertType, callback: Callable):
        """Unsubscribe from alerts"""
        key = alert_type.value
        if key in self._subscribers and callback in self._subscribers[key]:
            self._subscribers[key].remove(callback)

    def get_alerts(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
    ) -> List[Dict]:
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

    def get_alert_summary(self) -> Dict:
        """Get summary of alerts"""
        if not self._enabled:
            return {"enabled": False}

        summary = {
            "enabled": True,
            "total_alerts": len(self._alerts),
            "by_severity": {
                "critical": len([a for a in self._alerts if a.severity == AlertSeverity.CRITICAL]),
                "high": len([a for a in self._alerts if a.severity == AlertSeverity.HIGH]),
                "medium": len([a for a in self._alerts if a.severity == AlertSeverity.MEDIUM]),
                "low": len([a for a in self._alerts if a.severity == AlertSeverity.LOW]),
            },
            "by_type": {},
        }

        # Count by type
        for alert in self._alerts:
            alert_type = alert.alert_type.value
            if alert_type not in summary["by_type"]:
                summary["by_type"][alert_type] = 0
            summary["by_type"][alert_type] += 1

        return summary

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
