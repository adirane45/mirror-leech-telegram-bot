"""
Dead-Letter Queue (DLQ) Handler and Smart Retry Engine

Implements:
- Failure classification (transient vs. permanent)
- Automatic retry with exponential backoff
- Error-specific recovery strategies
- Task checkpointing for resume capability
"""

import asyncio
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field

from .. import LOGGER
from .redis_manager import redis_client


class FailureType(str, Enum):
    """Classification of failure types"""
    TRANSIENT = "transient"                    # Temporary failure, can retry
    RATE_LIMITED = "rate_limited"              # Rate limit (429), use backoff
    AUTH_FAILED = "auth_failed"                # Authentication error (401)
    QUOTA_EXCEEDED = "quota_exceeded"          # Quota/limit exceeded
    CONTENT_BLOCKED = "content_blocked"        # DMCA/blocked (permanent)
    INSUFFICIENT_SPACE = "insufficient_space" # Disk/storage full
    CORRUPTED = "corrupted"                    # Data corruption (permanent)
    UNKNOWN = "unknown"                        # Unknown error


class RetryStrategy(str, Enum):
    """Retry strategies"""
    IMMEDIATE = "immediate"                    # Retry immediately
    LINEAR_BACKOFF = "linear_backoff"         # 1s, 2s, 3s, ...
    EXPONENTIAL_BACKOFF = "exponential_backoff" # 1s, 2s, 4s, 8s, ...
    NO_RETRY = "no_retry"                      # Don't retry


@dataclass
class FailedTask:
    """Represents a failed task in DLQ"""
    task_id: str
    task_type: str
    arguments: Dict[str, Any]
    error_message: str
    failure_type: FailureType
    attempt_count: int = 1
    max_attempts: int = 3
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    next_retry_time: Optional[datetime] = None
    last_error_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    checkpoint_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "arguments": self.arguments,
            "error_message": self.error_message,
            "failure_type": self.failure_type.value,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "retry_strategy": self.retry_strategy.value,
            "next_retry_time": self.next_retry_time.isoformat() if self.next_retry_time else None,
            "last_error_time": self.last_error_time.isoformat(),
            "checkpoint_data": self.checkpoint_data,
            "metadata": self.metadata,
        }


class FailureAnalyzer:
    """Analyze failures and classify them"""
    
    @staticmethod
    def classify_error(error: Exception, error_message: str = None) -> FailureType:
        """Classify error type"""
        msg = (error_message or str(error)).lower()
        
        # Rate limit errors
        if any(x in msg for x in ['429', 'rate limit', 'too many requests', 'quota']):
            return FailureType.RATE_LIMITED
        
        # Auth errors
        if any(x in msg for x in ['401', '403', 'unauthorized', 'forbidden', 'invalid token']):
            return FailureType.AUTH_FAILED
        
        # Quota errors
        if any(x in msg for x in ['quota exceeded', 'storage limit', 'limit exceeded']):
            return FailureType.QUOTA_EXCEEDED
        
        # Content blocked
        if any(x in msg for x in ['dmca', 'takedown', 'blocked', 'unavailable', '410']):
            return FailureType.CONTENT_BLOCKED
        
        # Disk space
        if any(x in msg for x in ['disk full', 'no space', 'enospc', 'insufficient space']):
            return FailureType.INSUFFICIENT_SPACE
        
        # Corruption
        if any(x in msg for x in ['corruption', 'checksum', 'corrupted', 'invalid crc']):
            return FailureType.CORRUPTED
        
        # Network/transient
        if any(x in msg for x in ['timeout', 'connection', 'network', 'temporary', 'transient']):
            return FailureType.TRANSIENT
        
        return FailureType.UNKNOWN
    
    @staticmethod
    def get_retry_strategy(failure_type: FailureType) -> RetryStrategy:
        """Get retry strategy for failure type"""
        strategy_map = {
            FailureType.TRANSIENT: RetryStrategy.EXPONENTIAL_BACKOFF,
            FailureType.RATE_LIMITED: RetryStrategy.EXPONENTIAL_BACKOFF,
            FailureType.AUTH_FAILED: RetryStrategy.NO_RETRY,  # Permanent
            FailureType.QUOTA_EXCEEDED: RetryStrategy.LINEAR_BACKOFF,  # Soft retry
            FailureType.CONTENT_BLOCKED: RetryStrategy.NO_RETRY,  # Permanent
            FailureType.INSUFFICIENT_SPACE: RetryStrategy.NO_RETRY,  # Manual intervention
            FailureType.CORRUPTED: RetryStrategy.NO_RETRY,  # Permanent
            FailureType.UNKNOWN: RetryStrategy.LINEAR_BACKOFF,  # Conservative
        }
        return strategy_map.get(failure_type, RetryStrategy.LINEAR_BACKOFF)


class DLQHandler:
    """Dead-Letter Queue handler and retry manager"""
    
    def __init__(self):
        self.enabled = True
        self.max_dlq_size = 10000
        self.dlq_storage: Dict[str, FailedTask] = {}  # In-memory backup
    
    async def add_to_dlq(
        self,
        task_id: str,
        task_type: str,
        error: Exception,
        arguments: Dict[str, Any],
        checkpoint_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[FailedTask]:
        """Add failed task to DLQ"""
        
        # Classify error
        failure_type = FailureAnalyzer.classify_error(error, str(error))
        retry_strategy = FailureAnalyzer.get_retry_strategy(failure_type)
        
        # Create failed task
        failed_task = FailedTask(
            task_id=task_id,
            task_type=task_type,
            arguments=arguments,
            error_message=str(error),
            failure_type=failure_type,
            retry_strategy=retry_strategy,
            checkpoint_data=checkpoint_data,
            metadata=metadata or {},
        )
        
        # Calculate next retry time
        if retry_strategy != RetryStrategy.NO_RETRY:
            failed_task.next_retry_time = self._calculate_retry_time(
                attempt_count=failed_task.attempt_count,
                retry_strategy=retry_strategy,
            )
        
        # Store in Redis
        key = f"dlq:{task_id}"
        if redis_client.is_enabled:
            await redis_client.set(key, failed_task.to_dict(), ttl=86400 * 7)  # 7 days
        
        # Store in memory backup
        self.dlq_storage[task_id] = failed_task
        
        # Keep size under control
        if len(self.dlq_storage) > self.max_dlq_size:
            # Remove oldest
            oldest_key = min(
                self.dlq_storage.keys(),
                key=lambda k: self.dlq_storage[k].last_error_time
            )
            del self.dlq_storage[oldest_key]
        
        LOGGER.warning(
            f"Task {task_id} added to DLQ: "
            f"type={failure_type.value}, strategy={retry_strategy.value}, "
            f"next_retry={failed_task.next_retry_time}"
        )
        
        return failed_task
    
    def _calculate_retry_time(
        self,
        attempt_count: int,
        retry_strategy: RetryStrategy,
    ) -> datetime:
        """Calculate next retry time"""
        now = datetime.now(timezone.utc)
        
        if retry_strategy == RetryStrategy.IMMEDIATE:
            delay = 0
        
        elif retry_strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = attempt_count * 60  # 1min, 2min, 3min, ...
        
        elif retry_strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = min(60 * (2 ** (attempt_count - 1)), 3600)  # Max 1 hour
        
        else:
            delay = 0
        
        return now + timedelta(seconds=delay)
    
    async def get_ready_for_retry(self) -> list:
        """Get tasks ready for retry"""
        now = datetime.now(timezone.utc)
        ready = []
        
        for task_id, task in list(self.dlq_storage.items()):
            if task.attempt_count >= task.max_attempts:
                continue  # Max attempts reached
            
            if task.retry_strategy == RetryStrategy.NO_RETRY:
                continue  # Don't retry
            
            if task.next_retry_time and task.next_retry_time <= now:
                ready.append(task)
        
        return ready
    
    async def retry_task(
        self,
        task_id: str,
        execute_func: Callable,
    ) -> bool:
        """Retry a failed task"""
        if task_id not in self.dlq_storage:
            LOGGER.warning(f"Task {task_id} not in DLQ")
            return False
        
        task = self.dlq_storage[task_id]
        task.attempt_count += 1
        
        LOGGER.info(f"Retrying task {task_id} (attempt {task.attempt_count}/{task.max_attempts})")
        
        try:
            # Call execute function with checkpoint data
            if asyncio.iscoroutinefunction(execute_func):
                result = await execute_func(task.arguments, task.checkpoint_data)
            else:
                result = execute_func(task.arguments, task.checkpoint_data)
            
            # Success! Remove from DLQ
            await self.remove_from_dlq(task_id)
            LOGGER.info(f"Task {task_id} successfully retried")
            return True
        
        except Exception as e:
            # Failure
            task.last_error_time = datetime.now(timezone.utc)
            task.error_message = str(e)
            
            # Update failure type
            task.failure_type = FailureAnalyzer.classify_error(e)
            
            if task.attempt_count >= task.max_attempts:
                # Max attempts reached
                await self.remove_from_dlq(task_id)
                LOGGER.error(
                    f"Task {task_id} max retry attempts reached ({task.max_attempts}). "
                    f"Final error: {e}"
                )
                return False
            
            # Calculate next retry time
            task.next_retry_time = self._calculate_retry_time(
                attempt_count=task.attempt_count,
                retry_strategy=task.retry_strategy,
            )
            
            LOGGER.warning(
                f"Task {task_id} retry failed. Next retry at {task.next_retry_time}. "
                f"Error: {e}"
            )
            return False
    
    async def remove_from_dlq(self, task_id: str) -> None:
        """Remove task from DLQ"""
        if task_id in self.dlq_storage:
            del self.dlq_storage[task_id]
        
        if redis_client.is_enabled:
            key = f"dlq:{task_id}"
            await redis_client.delete(key)
    
    async def get_dlq_status(self) -> Dict[str, Any]:
        """Get DLQ status"""
        ready_count = len(await self.get_ready_for_retry())
        
        failure_types = {}
        for task in self.dlq_storage.values():
            ft = task.failure_type.value
            failure_types[ft] = failure_types.get(ft, 0) + 1
        
        return {
            "total_tasks": len(self.dlq_storage),
            "ready_for_retry": ready_count,
            "failure_types": failure_types,
            "max_size": self.max_dlq_size,
        }


# Global instance
dlq_handler = DLQHandler()
