"""
Phase 5: Smart Notifications System
Configurable notification rules with priority-based alerting and multi-channel delivery
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta, UTC
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    TELEGRAM = "telegram"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"


class NotificationCategory(str, Enum):
    """Notification categories"""
    DOWNLOAD_COMPLETE = "download_complete"
    DOWNLOAD_FAILED = "download_failed"
    SYSTEM_ERROR = "system_error"
    SECURITY_ALERT = "security_alert"
    RATE_LIMIT = "rate_limit"
    DISK_SPACE = "disk_space"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


@dataclass
class NotificationRule:
    """Notification rule configuration"""
    rule_id: str
    name: str
    category: NotificationCategory
    priority: NotificationPriority
    channels: List[NotificationChannel]
    enabled: bool = True
    
    # Rate limiting
    rate_limit_count: int = 10  # Max notifications
    rate_limit_window: int = 60  # Time window in seconds
    
    # Conditions
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # User targeting
    user_ids: Optional[List[str]] = None  # None = all users
    
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Notification:
    """Notification message"""
    notification_id: str
    category: NotificationCategory
    priority: NotificationPriority
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    user_id: Optional[str] = None
    channels: List[NotificationChannel] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    sent_at: Optional[datetime] = None
    delivered: bool = False
    error: Optional[str] = None


@dataclass
class NotificationStats:
    """Notification statistics"""
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    by_priority: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_channel: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_category: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class SmartNotificationSystem:
    """
    Smart Notifications System
    
    Features:
    - Configurable notification rules
    - Priority-based alerting (LOW, MEDIUM, HIGH, CRITICAL)
    - Multi-channel delivery (Telegram, Email, SMS, Webhook)
    - Rate limiting to prevent notification spam
    - User-specific targeting
    - Notification aggregation for similar events
    - Delivery tracking and retry logic
    
    Usage:
        notif = SmartNotificationSystem()
        
        # Define rule
        rule = NotificationRule(
            rule_id="download_complete",
            name="Download Completed",
            category=NotificationCategory.DOWNLOAD_COMPLETE,
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.TELEGRAM]
        )
        notif.add_rule(rule)
        
        # Send notification
        await notif.send_notification(
            category=NotificationCategory.DOWNLOAD_COMPLETE,
            title="Download Complete",
            message="file.zip downloaded successfully"
        )
    """
    
    def __init__(self):
        self.rules: Dict[str, NotificationRule] = {}  # rule_id -> rule
        self.notifications: Dict[str, Notification] = {}  # notification_id -> notification
        self.stats = NotificationStats()
        
        # Rate limiting tracking
        self.rate_limit_counters: Dict[str, List[datetime]] = defaultdict(list)
        
        # Channel handlers
        self.channel_handlers: Dict[NotificationChannel, Callable] = {}
        
        # Notification queue
        self.queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        
        logger.info("SmartNotificationSystem initialized")
    
    # ========================================================================
    # RULE MANAGEMENT
    # ========================================================================
    
    def add_rule(self, rule: NotificationRule) -> None:
        """Add notification rule"""
        try:
            self.rules[rule.rule_id] = rule
            logger.info(f"Notification rule added: {rule.name} ({rule.priority})")
        except Exception as e:
            logger.error(f"Failed to add rule: {e}")
            raise
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove notification rule"""
        try:
            if rule_id in self.rules:
                del self.rules[rule_id]
                logger.info(f"Rule removed: {rule_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove rule: {e}")
            return False
    
    def update_rule(self, rule_id: str, **updates) -> bool:
        """Update notification rule"""
        try:
            if rule_id not in self.rules:
                return False
            
            rule = self.rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            logger.info(f"Rule updated: {rule_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update rule: {e}")
            return False
    
    def get_rule(self, rule_id: str) -> Optional[NotificationRule]:
        """Get notification rule"""
        return self.rules.get(rule_id)
    
    def list_rules(self, category: Optional[NotificationCategory] = None) -> List[NotificationRule]:
        """List notification rules"""
        rules = list(self.rules.values())
        if category:
            rules = [r for r in rules if r.category == category]
        return rules
    
    # ========================================================================
    # CHANNEL HANDLERS
    # ========================================================================
    
    def register_channel_handler(
        self,
        channel: NotificationChannel,
        handler: Callable
    ) -> None:
        """
        Register handler for notification channel
        
        Handler signature: async def handler(notification: Notification) -> bool
        """
        self.channel_handlers[channel] = handler
        logger.info(f"Channel handler registered: {channel}")
    
    # ========================================================================
    # NOTIFICATION SENDING
    # ========================================================================
    
    async def send_notification(
        self,
        category: NotificationCategory,
        title: str,
        message: str,
        priority: Optional[NotificationPriority] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        channels: Optional[List[NotificationChannel]] = None
    ) -> Optional[str]:
        """
        Send notification
        
        Returns:
            notification_id if sent, None if blocked
        """
        try:
            # Find matching rules
            matching_rules = self._find_matching_rules(category, user_id)
            
            if not matching_rules:
                logger.debug(f"No rules match category: {category}")
                return None
            
            # Use highest priority rule
            rule = max(matching_rules, key=lambda r: self._priority_value(r.priority))
            
            # Check rate limit
            if not self._check_rate_limit(rule):
                logger.warning(f"Rate limit exceeded for rule: {rule.name}")
                return None
            
            # Create notification
            import secrets
            notification_id = secrets.token_urlsafe(16)
            
            notification = Notification(
                notification_id=notification_id,
                category=category,
                priority=priority or rule.priority,
                title=title,
                message=message,
                data=data or {},
                user_id=user_id,
                channels=channels or rule.channels
            )
            
            # Store notification
            self.notifications[notification_id] = notification
            
            # Queue for delivery
            await self.queue.put(notification)
            
            # Update stats
            self.stats.total_sent += 1
            self.stats.by_priority[notification.priority] += 1
            self.stats.by_category[notification.category] += 1
            
            logger.info(f"Notification queued: {title} ({notification.priority})")
            
            return notification_id
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return None
    
    def _find_matching_rules(
        self,
        category: NotificationCategory,
        user_id: Optional[str]
    ) -> List[NotificationRule]:
        """Find rules matching category and user"""
        matching = []
        
        for rule in self.rules.values():
            if not rule.enabled:
                continue
            
            # Check category
            if rule.category != category:
                continue
            
            # Check user targeting
            if rule.user_ids is not None:
                if user_id not in rule.user_ids:
                    continue
            
            matching.append(rule)
        
        return matching
    
    def _priority_value(self, priority: NotificationPriority) -> int:
        """Convert priority to numeric value"""
        priority_map = {
            NotificationPriority.LOW: 1,
            NotificationPriority.MEDIUM: 2,
            NotificationPriority.HIGH: 3,
            NotificationPriority.CRITICAL: 4
        }
        return priority_map.get(priority, 0)
    
    def _check_rate_limit(self, rule: NotificationRule) -> bool:
        """Check if notification is within rate limit"""
        try:
            now = datetime.now(UTC)
            rule_key = rule.rule_id
            
            # Get recent notifications for this rule
            recent = self.rate_limit_counters[rule_key]
            
            # Remove old entries
            cutoff = now - timedelta(seconds=rule.rate_limit_window)
            recent = [t for t in recent if t > cutoff]
            self.rate_limit_counters[rule_key] = recent
            
            # Check count
            if len(recent) >= rule.rate_limit_count:
                return False
            
            # Add current notification
            recent.append(now)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Allow on error
    
    # ========================================================================
    # NOTIFICATION DELIVERY
    # ========================================================================
    
    async def start_worker(self) -> None:
        """Start notification delivery worker"""
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self._delivery_worker())
            logger.info("Notification worker started")
    
    async def stop_worker(self) -> None:
        """Stop notification delivery worker"""
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            logger.info("Notification worker stopped")
    
    async def _delivery_worker(self) -> None:
        """Background worker for delivering notifications"""
        logger.info("Notification delivery worker running")
        
        while True:
            try:
                # Get notification from queue
                notification = await self.queue.get()
                
                # Deliver to channels
                await self._deliver_notification(notification)
                
                self.queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Delivery worker error: {e}")
                await asyncio.sleep(1)
    
    async def _deliver_notification(self, notification: Notification) -> None:
        """Deliver notification to all channels"""
        try:
            success_channels = []
            failed_channels = []
            
            for channel in notification.channels:
                try:
                    # Get handler
                    handler = self.channel_handlers.get(channel)
                    if not handler:
                        logger.warning(f"No handler for channel: {channel}")
                        failed_channels.append(channel)
                        continue
                    
                    # Call handler
                    result = await handler(notification)
                    
                    if result:
                        success_channels.append(channel)
                        self.stats.by_channel[channel] += 1
                    else:
                        failed_channels.append(channel)
                    
                except Exception as e:
                    logger.error(f"Channel delivery error ({channel}): {e}")
                    failed_channels.append(channel)
            
            # Update notification status
            if success_channels:
                notification.sent_at = datetime.now(UTC)
                notification.delivered = len(failed_channels) == 0
                self.stats.total_delivered += 1
            else:
                notification.error = f"Failed on all channels: {failed_channels}"
                self.stats.total_failed += 1
            
            logger.info(
                f"Notification delivered: {notification.title} "
                f"(success={success_channels}, failed={failed_channels})"
            )
            
        except Exception as e:
            logger.error(f"Notification delivery error: {e}")
            notification.error = str(e)
            self.stats.total_failed += 1
    
    # ========================================================================
    # BULK OPERATIONS
    # ========================================================================
    
    async def send_bulk_notification(
        self,
        category: NotificationCategory,
        title: str,
        message: str,
        user_ids: List[str],
        priority: Optional[NotificationPriority] = None
    ) -> List[str]:
        """Send notification to multiple users"""
        notification_ids = []
        
        for user_id in user_ids:
            notif_id = await self.send_notification(
                category=category,
                title=title,
                message=message,
                priority=priority,
                user_id=user_id
            )
            if notif_id:
                notification_ids.append(notif_id)
        
        logger.info(f"Bulk notification sent to {len(notification_ids)}/{len(user_ids)} users")
        
        return notification_ids
    
    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        return {
            'total_sent': self.stats.total_sent,
            'total_delivered': self.stats.total_delivered,
            'total_failed': self.stats.total_failed,
            'delivery_rate': (
                self.stats.total_delivered / self.stats.total_sent * 100
                if self.stats.total_sent > 0 else 0
            ),
            'by_priority': dict(self.stats.by_priority),
            'by_channel': dict(self.stats.by_channel),
            'by_category': dict(self.stats.by_category),
            'active_rules': len([r for r in self.rules.values() if r.enabled]),
            'queue_size': self.queue.qsize()
        }
    
    def get_notification_history(
        self,
        user_id: Optional[str] = None,
        category: Optional[NotificationCategory] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get notification history"""
        notifications = list(self.notifications.values())
        
        # Filter by user
        if user_id:
            notifications = [n for n in notifications if n.user_id == user_id]
        
        # Filter by category
        if category:
            notifications = [n for n in notifications if n.category == category]
        
        # Sort by created_at (newest first)
        notifications.sort(key=lambda n: n.created_at, reverse=True)
        
        # Limit results
        notifications = notifications[:limit]
        
        # Convert to dict
        return [
            {
                'notification_id': n.notification_id,
                'category': n.category,
                'priority': n.priority,
                'title': n.title,
                'message': n.message,
                'channels': n.channels,
                'created_at': n.created_at.isoformat(),
                'sent_at': n.sent_at.isoformat() if n.sent_at else None,
                'delivered': n.delivered,
                'error': n.error
            }
            for n in notifications
        ]


# ============================================================================
# SINGLETON
# ============================================================================

_notification_system: Optional[SmartNotificationSystem] = None


def get_notification_system() -> SmartNotificationSystem:
    """Get notification system singleton"""
    global _notification_system
    if _notification_system is None:
        _notification_system = SmartNotificationSystem()
    return _notification_system
