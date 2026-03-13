"""
Dead-Letter Queue & Smart Retry Engine
Manages failed tasks with intelligent retry strategies
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from logging import getLogger
from typing import Any, Awaitable, Callable, Dict, List, Optional

LOGGER = getLogger(__name__)


class FailureType(Enum):
    """Classification of failure types"""
    TRANSIENT = "transient"              # Network timeout, temporary error
    RATE_LIMITED = "rate_limited"        # 429 - too many requests
    AUTH_FAILED = "auth_failed"          # 401/403 - auth issue
    QUOTA_EXCEEDED = "quota_exceeded"    # Quota/limit reached
    RESOURCE_UNAVAILABLE = "unavailable" # Service unavailable
    CONTENT_BLOCKED = "content_blocked"  # DMCA/IP block - permanent
    INSUFFICIENT_SPACE = "insufficient_space"  # Disk/storage full
    CORRUPTED_SOURCE = "corrupted"       # File checksum mismatch
    UNKNOWN = "unknown"                  # Unknown error


@dataclass
class FailureContext:
    """Context for a failed task"""
    task_id: str
    operation: str  # "download", "upload", etc.
    error_type: FailureType
    error_message: str
    failure_count: int = 1
    first_failure_at: datetime = field(default_factory=lambda: datetime.now())
    last_failure_at: datetime = field(default_factory=lambda: datetime.now())
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Checkpoint data for resume
    checkpoint_data: Optional[Dict[str, Any]] = None

    def is_recoverable(self) -> bool:
        """Check if task can be retried"""
        return self.error_type not in [
            FailureType.CONTENT_BLOCKED,
            FailureType.CORRUPTED_SOURCE,
        ]


class RetryStrategy:
    """Intelligent retry strategy based on error type"""

    @staticmethod
    def get_retry_delay(error_type: FailureType, attempt: int) -> int:
        """
        Get retry delay in seconds

        Args:
            error_type: Type of failure
            attempt: Retry attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        strategies = {
            FailureType.TRANSIENT: {
                1: 5,      # 5 seconds
                2: 10,     # 10 seconds
                3: 20,     # 20 seconds
                4: 30,     # 30 seconds
            },
            FailureType.RATE_LIMITED: {
                1: 60,      # 1 minute
                2: 300,     # 5 minutes
                3: 900,     # 15 minutes
                4: 3600,    # 1 hour
            },
            FailureType.AUTH_FAILED: {
                1: 10,      # 10 seconds
                2: 30,      # 30 seconds
                3: 60,      # 1 minute
            },
            FailureType.QUOTA_EXCEEDED: {
                1: 3600,    # 1 hour
                2: 86400,   # 1 day
            },
            FailureType.RESOURCE_UNAVAILABLE: {
                1: 30,
                2: 60,
                3: 300,
            },
        }

        strategy = strategies.get(error_type, {})
        delay = strategy.get(attempt, strategy.get(max(strategy.keys())) if strategy else 300)
        
        # Ensure delay is not None (fallback to 300)
        if delay is None:
            delay = 300

        # Add jitter (±10%)
        jitter = int(delay * 0.1)
        import random
        return delay + random.randint(-jitter, jitter)

    @staticmethod
    def max_retries(error_type: FailureType) -> int:
        """Get max retries for error type"""
        max_attempts = {
            FailureType.TRANSIENT: 4,
            FailureType.RATE_LIMITED: 4,
            FailureType.AUTH_FAILED: 3,
            FailureType.QUOTA_EXCEEDED: 2,
            FailureType.RESOURCE_UNAVAILABLE: 3,
            FailureType.CONTENT_BLOCKED: 0,
            FailureType.INSUFFICIENT_SPACE: 0,
            FailureType.CORRUPTED_SOURCE: 0,
            FailureType.UNKNOWN: 3,
        }
        return max_attempts.get(error_type, 3)


class DeadLetterQueue:
    """Queue for failed tasks awaiting retry"""

    def __init__(self) -> None:
        self._queue: Dict[str, FailureContext] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        self._watchers: List[Callable[[FailureContext], Awaitable[None]]] = []

    async def add(self, failure: FailureContext) -> None:
        """Add failed task to DLQ"""
        async with self._lock:
            self._queue[failure.task_id] = failure
            LOGGER.warning(
                f"📮 Task '{failure.task_id}' added to DLQ: "
                f"{failure.error_type.value} - {failure.error_message[:50]}"
            )

            # Notify watchers
            for watcher in self._watchers:
                # Use ensure_future to handle Awaitable type properly
                asyncio.ensure_future(watcher(failure))

    async def get(self, task_id: str) -> Optional[FailureContext]:
        """Get task from DLQ"""
        async with self._lock:
            return self._queue.get(task_id)

    async def remove(self, task_id: str) -> None:
        """Remove task from DLQ"""
        async with self._lock:
            if task_id in self._queue:
                del self._queue[task_id]

    async def get_ready_for_retry(self) -> List[FailureContext]:
        """Get tasks ready for retry based on delay"""
        async with self._lock:
            ready: List[FailureContext] = []
            now = datetime.now()

            for task_id, failure in list(self._queue.items()):
                if not failure.is_recoverable():
                    continue

                retry_delay = RetryStrategy.get_retry_delay(
                    failure.error_type,
                    failure.failure_count
                )

                if (now - failure.last_failure_at).total_seconds() >= retry_delay:
                    ready.append(failure)

            return ready

    async def count(self) -> int:
        """Get total tasks in DLQ"""
        async with self._lock:
            return len(self._queue)

    async def list_all(self) -> List[FailureContext]:
        """List all tasks in DLQ"""
        async with self._lock:
            return list(self._queue.values())

    def add_watcher(self, callback: Callable[[FailureContext], Awaitable[None]]) -> None:
        """Add callback for DLQ changes"""
        self._watchers.append(callback)


class CheckpointManager:
    """Manages task checkpoints for resume capability"""

    def __init__(self) -> None:
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    def save_checkpoint(self, task_id: str, data: Dict[str, Any]) -> None:
        """Save task checkpoint"""
        self._checkpoints[task_id] = {
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        LOGGER.debug(f"💾 Checkpoint saved for task '{task_id}'")

    def get_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task checkpoint"""
        if task_id in self._checkpoints:
            return self._checkpoints[task_id].get("data")
        return None

    def delete_checkpoint(self, task_id: str) -> None:
        """Delete task checkpoint"""
        if task_id in self._checkpoints:
            del self._checkpoints[task_id]

    def clear_old_checkpoints(self, max_age_hours: int = 24) -> None:
        """Clean up old checkpoints"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        expired: List[str] = []

        for task_id, checkpoint in self._checkpoints.items():
            timestamp = datetime.fromisoformat(checkpoint["timestamp"])
            if timestamp < cutoff:
                expired.append(task_id)

        for task_id in expired:
            del self._checkpoints[task_id]
            LOGGER.debug(f"🗑️  Deleted old checkpoint for '{task_id}'")


class FailureAnalyzer:
    """Analyzes errors and determines recovery strategy"""

    @staticmethod
    def classify_error(error: Exception, error_message: Optional[str] = None) -> FailureType:
        """Classify error and return FailureType"""
        msg = str(error).lower() + (error_message or "").lower()

        # Pattern matching for common errors
        patterns = {
            FailureType.RATE_LIMITED: ["429", "too many requests", "rate limit"],
            FailureType.AUTH_FAILED: ["401", "403", "unauthorized", "forbidden", "invalid token"],
            FailureType.QUOTA_EXCEEDED: ["quota", "limit exceeded", "storage full"],
            FailureType.TRANSIENT: ["timeout", "connection", "reset", "temporarily unavailable"],
            FailureType.RESOURCE_UNAVAILABLE: ["503", "service unavailable", "temporarily unavailable"],
            FailureType.CONTENT_BLOCKED: ["dmca", "copyright", "blocked", "removed"],
            FailureType.INSUFFICIENT_SPACE: ["no space", "disk full", "enospc"],
            FailureType.CORRUPTED_SOURCE: ["checksum", "corrupt", "crc"],
        }

        for failure_type, keywords in patterns.items():
            for keyword in keywords:
                if keyword in msg:
                    return failure_type

        return FailureType.UNKNOWN

    @staticmethod
    def suggest_fix(failure: FailureContext) -> Optional[str]:
        """Suggest fix for failure"""
        suggestions = {
            FailureType.RATE_LIMITED: "Exponential backoff retry enabled",
            FailureType.AUTH_FAILED: "Rotate credentials and retry",
            FailureType.QUOTA_EXCEEDED: "Wait 24 hours for quota reset",
            FailureType.INSUFFICIENT_SPACE: "Free up disk space manually",
            FailureType.CORRUPTED_SOURCE: "Download from different source",
            FailureType.TRANSIENT: "Automatic retry with backoff",
            FailureType.RESOURCE_UNAVAILABLE: "Service recovery in progress",
        }
        return suggestions.get(failure.error_type)


class SmartRetryEngine:
    """Coordinates DLQ and retry logic"""

    def __init__(self) -> None:
        self.dlq = DeadLetterQueue()
        self.checkpoints = CheckpointManager()
        self._retry_tasks: Dict[str, "asyncio.Task[None]"] = {}

    async def handle_failure(
        self,
        task_id: str,
        operation: str,
        error: Exception,
        metadata: Optional[Dict[str, Any]] = None,
        checkpoint: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle task failure"""
        error_type = FailureAnalyzer.classify_error(error)

        failure = FailureContext(
            task_id=task_id,
            operation=operation,
            error_type=error_type,
            error_message=str(error)[:200],
            metadata=metadata or {},
            checkpoint_data=checkpoint,
        )

        suggestion = FailureAnalyzer.suggest_fix(failure)
        LOGGER.error(
            f"❌ Task '{task_id}' failed ({operation}): {error_type.value}\n"
            f"   Message: {str(error)[:100]}\n"
            f"   Suggestion: {suggestion}"
        )

        # Save checkpoint for resume
        if checkpoint:
            self.checkpoints.save_checkpoint(task_id, checkpoint)

        # Add to DLQ
        await self.dlq.add(failure)

    async def record_retry(self, task_id: str) -> None:
        """Record that task is being retried"""
        failure = await self.dlq.get(task_id)
        if failure:
            failure.failure_count += 1
            failure.last_failure_at = datetime.now()

            max_retries = RetryStrategy.max_retries(failure.error_type)
            LOGGER.info(
                f"🔄 Retrying task '{task_id}' "
                f"({failure.failure_count}/{max_retries + 1})"
            )

    async def processor_loop(self, retry_callback: Callable[[str, FailureContext, Optional[Dict[str, Any]]], Awaitable[None]]) -> None:
        """Main loop to process DLQ items"""
        LOGGER.info("🚀 Smart Retry Engine started")

        while True:
            try:
                # Get tasks ready for retry
                ready = await self.dlq.get_ready_for_retry()

                for failure in ready:
                    if not failure.is_recoverable():
                        await self.dlq.remove(failure.task_id)
                        LOGGER.warning(
                            f"🗑️  Discarded unrecoverable task '{failure.task_id}' "
                            f"({failure.error_type.value})"
                        )
                        continue

                    max_retries = RetryStrategy.max_retries(failure.error_type)
                    if failure.failure_count > max_retries:
                        await self.dlq.remove(failure.task_id)
                        LOGGER.error(
                            f"❌ Task '{failure.task_id}' exhausted retries "
                            f"({failure.failure_count}/{max_retries + 1})"
                        )
                        continue

                    # Retry
                    await self.record_retry(failure.task_id)
                    checkpoint = self.checkpoints.get_checkpoint(failure.task_id)

                    try:
                        await retry_callback(failure.task_id, failure, checkpoint)
                        await self.dlq.remove(failure.task_id)
                        self.checkpoints.delete_checkpoint(failure.task_id)
                        LOGGER.info(f"✅ Task '{failure.task_id}' recovered successfully")
                    except Exception as e:
                        LOGGER.warning(f"Retry failed: {e}")

                # Cleanup old checkpoints
                self.checkpoints.clear_old_checkpoints(max_age_hours=24)

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                LOGGER.error(f"Error in retry processor: {e}", exc_info=True)
                await asyncio.sleep(10)


# Global instances
dlq = DeadLetterQueue()
smart_retry = SmartRetryEngine()
