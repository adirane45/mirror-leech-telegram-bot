"""
Enhanced Feedback Models
Data structures for feedback, notifications, and progress tracking
"""

from enum import Enum
from typing import Dict, Optional
from time import time


class FeedbackLevel(Enum):
    """Feedback level/severity"""
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    PROGRESS = "⏳"
    CRITICAL = "🚨"


class NotificationType(Enum):
    """Types of notifications"""
    TASK_STARTED = "task_started"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_PAUSED = "task_paused"
    TASK_RESUMED = "task_resumed"
    SYSTEM_ALERT = "system_alert"
    RESOURCE_WARNING = "resource_warning"
    CUSTOM = "custom"


class Notification:
    """Represents a single notification"""

    def __init__(
        self,
        title: str,
        message: str,
        notif_type: NotificationType = NotificationType.CUSTOM,
        level: FeedbackLevel = FeedbackLevel.INFO,
        timestamp: Optional[float] = None,
        data: Optional[Dict] = None,
    ):
        self.title = title
        self.message = message
        self.notif_type = notif_type
        self.level = level
        self.timestamp = timestamp or time()
        self.data = data or {}
        self.read = False

    def format_text(self) -> str:
        """Format notification as readable text"""
        from datetime import datetime
        time_str = datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")
        return (
            f"{self.level.value} <b>{self.title}</b> [{time_str}]\n"
            f"{self.message}"
        )

    def to_dict(self) -> Dict:
        """Convert notification to dictionary"""
        return {
            "title": self.title,
            "message": self.message,
            "type": self.notif_type.value,
            "level": self.level.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "read": self.read,
        }
