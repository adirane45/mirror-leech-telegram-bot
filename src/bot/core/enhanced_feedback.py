"""
Enhanced Feedback Module
Provides real-time feedback, notifications, and progress tracking with visual indicators
"""

from typing import Optional, Dict, List, Callable, Any
from time import time
import asyncio

from .enhanced_feedback_models import FeedbackLevel, NotificationType, Notification


class NotificationCenter:
    """Centralized notification management"""

    def __init__(self, max_notifications: int = 100):
        self.notifications: List[Notification] = []
        self.max_notifications = max_notifications
        self.subscribers: Dict[str, List[Callable]] = {}
        self._lock = asyncio.Lock()

    async def send(self, notification: Notification) -> None:
        """Send a notification"""
        async with self._lock:
            self.notifications.append(notification)
            if len(self.notifications) > self.max_notifications:
                self.notifications.pop(0)

        # Notify subscribers
        await self._notify_subscribers(notification)

    async def _notify_subscribers(self, notification: Notification) -> None:
        """Notify all subscribers of a notification"""
        notif_type = notification.notif_type.value
        subscribers = self.subscribers.get(notif_type, [])
        subscribers += self.subscribers.get("*", [])  # Wildcard subscribers

        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(notification)
                else:
                    callback(notification)
            except Exception as e:
                print(f"Error in notification subscriber: {e}")

    def subscribe(self, notification_type: str, callback: Callable) -> None:
        """Subscribe to notifications of a specific type"""
        if notification_type not in self.subscribers:
            self.subscribers[notification_type] = []
        self.subscribers[notification_type].append(callback)

    async def get_notifications(self, count: int = 10) -> List[Notification]:
        """Get recent notifications"""
        async with self._lock:
            return self.notifications[-count:]

    async def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        async with self._lock:
            return sum(1 for n in self.notifications if not n.read)

    async def mark_as_read(self, index: int) -> None:
        """Mark a notification as read"""
        async with self._lock:
            if 0 <= index < len(self.notifications):
                self.notifications[index].read = True

    async def clear_notifications(self) -> None:
        """Clear all notifications"""
        async with self._lock:
            self.notifications.clear()


class ProgressTracker:
    """Track and display progress with visual feedback"""

    def __init__(self, task_id: str, task_name: str, total: float = 100):
        self.task_id = task_id
        self.task_name = task_name
        self.total = total
        self.current = 0
        self.start_time = time()
        self.last_update = self.start_time
        self.speed = 0.0
        self.eta_seconds = 0
        self.status = "pending"
        self.substatus = ""

    def update(self, current: float) -> None:
        """Update progress"""
        current_time = time()
        if current_time - self.last_update > 0:
            self.speed = (current - self.current) / (current_time - self.last_update)

        remaining = self.total - current
        if self.speed > 0:
            self.eta_seconds = remaining / self.speed
        else:
            self.eta_seconds = 0

        self.current = current
        self.last_update = current_time

    def get_progress_percentage(self) -> float:
        """Get progress as percentage"""
        if self.total > 0:
            return min(100, (self.current / self.total) * 100)
        return 0

    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time() - self.start_time

    def format_progress_bar(self, length: int = 20) -> str:
        """Format progress bar"""
        percentage = self.get_progress_percentage()
        filled = int(length * percentage / 100)
        bar = "▰" * filled + "▱" * (length - filled)
        return f"[{bar}] {percentage:.1f}%"

    def format_details(self) -> str:
        """Format detailed progress information"""
        from ..helper.ext_utils.status_utils import get_readable_time, get_readable_file_size

        percentage = self.get_progress_percentage()
        elapsed = get_readable_time(self.get_elapsed_time())
        eta = get_readable_time(self.eta_seconds)
        speed = get_readable_file_size(self.speed, "/s")

        text = f"<b>{self.task_name}</b>\n"
        text += f"Status: <code>{self.status}</code>"
        if self.substatus:
            text += f" | {self.substatus}"
        text += "\n"
        text += f"{self.format_progress_bar()}\n"
        text += f"Speed: {speed} | ETA: {eta}\n"
        text += f"Elapsed: {elapsed}"
        return text

    def format_compact(self) -> str:
        """Format compact progress display"""
        percentage = self.get_progress_percentage()
        from ..helper.ext_utils.status_utils import get_readable_time

        eta = get_readable_time(self.eta_seconds)
        return f"{self.task_name}: {percentage:.0f}% | ETA: {eta}"


class FeedbackFormatter:
    """Format feedback messages for users"""

    @staticmethod
    def format_task_started(task_name: str, source: str = "") -> str:
        """Format task started message"""
        text = f"{FeedbackLevel.PROGRESS.value} <b>Task Started</b>\n"
        text += f"Name: <code>{task_name}</code>"
        if source:
            text += f"\nSource: <code>{source}</code>"
        return text

    @staticmethod
    def format_task_progress(
        task_name: str,
        progress: float,
        speed: str = "",
        eta: str = "",
    ) -> str:
        """Format task progress message"""
        from bot.core.enhanced_stats import ProgressBar

        text = f"{FeedbackLevel.PROGRESS.value} <b>In Progress</b>\n"
        text += f"Task: <code>{task_name}</code>\n"
        text += ProgressBar.filled_bar(progress, length=15) + "\n"
        if speed:
            text += f"Speed: {speed}\n"
        if eta:
            text += f"ETA: {eta}"
        return text

    @staticmethod
    def format_task_completed(task_name: str, size: str = "", time_taken: str = "") -> str:
        """Format task completed message"""
        text = f"{FeedbackLevel.SUCCESS.value} <b>Task Completed</b>\n"
        text += f"Name: <code>{task_name}</code>"
        if size:
            text += f"\nSize: <code>{size}</code>"
        if time_taken:
            text += f"\nTime: <code>{time_taken}</code>"
        return text

    @staticmethod
    def format_task_failed(task_name: str, error: str = "") -> str:
        """Format task failed message"""
        text = f"{FeedbackLevel.ERROR.value} <b>Task Failed</b>\n"
        text += f"Name: <code>{task_name}</code>"
        if error:
            text += f"\nError: <code>{error}</code>"
        return text

    @staticmethod
    def format_resource_warning(
        resource_name: str,
        current: float,
        threshold: float,
    ) -> str:
        """Format resource warning message"""
        text = f"{FeedbackLevel.WARNING.value} <b>Resource Warning</b>\n"
        text += f"Resource: <code>{resource_name}</code>\n"
        text += f"Current: <code>{current:.1f}%</code>\n"
        text += f"Threshold: <code>{threshold:.1f}%</code>"
        return text

    @staticmethod
    def format_system_alert(alert_title: str, alert_message: str) -> str:
        """Format system alert message"""
        text = f"{FeedbackLevel.CRITICAL.value} <b>{alert_title}</b>\n"
        text += f"{alert_message}"
        return text

    @staticmethod
    def format_inline_feedback(
        status_emoji: str,
        title: str,
        details: str = "",
    ) -> str:
        """Format inline feedback message"""
        text = f"{status_emoji} <b>{title}</b>"
        if details:
            text += f"\n{details}"
        return text

    @staticmethod
    def format_action_summary(
        action: str,
        success_count: int = 0,
        failed_count: int = 0,
        duration: str = "",
    ) -> str:
        """Format action summary"""
        text = f"{FeedbackLevel.SUCCESS.value} <b>{action} Summary</b>\n"
        text += f"✅ Successful: {success_count}\n"
        if failed_count > 0:
            text += f"❌ Failed: {failed_count}\n"
        if duration:
            text += f"⏱️ Duration: {duration}"
        return text


class RealtimeFeedback:
    """Manage real-time feedback updates"""

    def __init__(self):
        self.active_feedbacks: Dict[str, Dict[str, Any]] = {}
        self.feedback_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    async def start_feedback(
        self,
        feedback_id: str,
        title: str,
        initial_message: str = "",
    ) -> None:
        """Start a new feedback session"""
        async with self._lock:
            self.active_feedbacks[feedback_id] = {
                "title": title,
                "message": initial_message,
                "start_time": time(),
                "updates": [],
            }

    async def update_feedback(
        self,
        feedback_id: str,
        message: str,
        append: bool = False,
    ) -> None:
        """Update active feedback"""
        async with self._lock:
            if feedback_id in self.active_feedbacks:
                if append:
                    self.active_feedbacks[feedback_id]["message"] += f"\n{message}"
                else:
                    self.active_feedbacks[feedback_id]["message"] = message
                self.active_feedbacks[feedback_id]["updates"].append(
                    {
                        "time": time(),
                        "message": message,
                    }
                )

    async def end_feedback(
        self,
        feedback_id: str,
        final_message: str = "",
    ) -> Dict[str, Any]:
        """End feedback session and return history"""
        async with self._lock:
            if feedback_id in self.active_feedbacks:
                feedback = self.active_feedbacks.pop(feedback_id)
                if final_message:
                    feedback["message"] = final_message
                feedback["end_time"] = time()
                feedback["duration"] = feedback["end_time"] - feedback["start_time"]
                self.feedback_history.append(feedback)
                return feedback
            return {}

    async def get_active_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Get active feedback by ID"""
        async with self._lock:
            return self.active_feedbacks.get(feedback_id)

    async def get_all_active(self) -> Dict[str, Dict[str, Any]]:
        """Get all active feedbacks"""
        async with self._lock:
            return self.active_feedbacks.copy()

    async def cancel_feedback(self, feedback_id: str) -> None:
        """Cancel a feedback session"""
        async with self._lock:
            if feedback_id in self.active_feedbacks:
                del self.active_feedbacks[feedback_id]
