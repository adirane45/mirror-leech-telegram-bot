"""
Alert Manager Models
Data structures for alert management and tracking
"""

from enum import Enum
from typing import Dict, Optional
from datetime import datetime, UTC


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
