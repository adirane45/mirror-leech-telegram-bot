"""
Advanced Queue Priority System
VIP users, emergency downloads, weighted scoring, dynamic queues
"""

import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime, timedelta
from logging import getLogger
from bisect import insort

LOGGER = getLogger(__name__)


class UserTier(Enum):
    """User tier levels"""
    STANDARD = "standard"      # Default, weight=1
    PREMIUM = "premium"        # VIP, weight=3
    ADMIN = "admin"            # Admin, weight=5


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1         # Background jobs
    NORMAL = 5      # Default downloads
    HIGH = 10       # Important downloads
    CRITICAL = 20   # Emergency jobs


class QueueName(Enum):
    """Named queues"""
    DEFAULT = "default"
    VIP = "vip"
    EMERGENCY = "emergency"
    BATCH = "batch"


@dataclass
class QueuedTask:
    """Task in the queue"""
    task_id: str
    user_id: int
    operation: str              # "download", "upload", "mirror"
    priority: TaskPriority
    user_tier: UserTier
    queued_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Metadata
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Callbacks
    execute_callback: Optional[Callable] = None
    progress_callback: Optional[Callable] = None
    
    def calculate_score(self) -> float:
        """
        Calculate task score for priority queue
        Higher score = Higher priority = Execute sooner
        
        Formula: base_priority * user_weight + time_bonus + size_bonus
        """
        # Base priority weight
        base_score = self.priority.value
        
        # User tier weight (multiplier)
        tier_weights = {
            UserTier.STANDARD: 1.0,
            UserTier.PREMIUM: 3.0,
            UserTier.ADMIN: 5.0,
        }
        tier_weight = tier_weights.get(self.user_tier, 1.0)
        
        # Time-based boost (age in queue)
        age_seconds = (datetime.utcnow() - self.queued_at).total_seconds()
        time_bonus = age_seconds / 60.0  # +1 point per minute waiting
        
        # Size-based adjustment (smaller files boost)
        size_bonus = 0
        if self.file_size and self.file_size < 100_000_000:  # < 100MB
            # Smaller files get slight boost
            size_bonus = 2.0
        
        total_score = (base_score * tier_weight) + time_bonus + size_bonus
        return total_score
    
    def duration_in_queue(self) -> timedelta:
        """Get time spent in queue"""
        end_time = self.started_at or datetime.utcnow()
        return end_time - self.queued_at
    
    def total_duration(self) -> Optional[timedelta]:
        """Get total execution time"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def is_expired(self, max_queue_time_hours: int = 24) -> bool:
        """Check if task expired in queue"""
        return self.duration_in_queue() > timedelta(hours=max_queue_time_hours)


@dataclass
class QueueStats:
    """Statistics for a queue"""
    queue_name: str
    total_tasks: int
    queued_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_wait_time: float  # seconds
    average_execution_time: float  # seconds


class PriorityQueue:
    """Priority queue with weighted scoring"""
    
    def __init__(self, name: str, max_concurrent: int = 3):
        self.name = name
        self.max_concurrent = max_concurrent
        
        self._pending: List[QueuedTask] = []  # Sorted by score
        self._running: Dict[str, QueuedTask] = {}
        self._completed: List[QueuedTask] = []
        self._failed: Dict[str, QueuedTask] = {}
        
        self._lock = asyncio.Lock()
        self._dispatcher_running = False
    
    async def add(self, task: QueuedTask) -> str:
        """Add task to queue"""
        async with self._lock:
            insort(self._pending, task, key=lambda t: -t.calculate_score())
            LOGGER.debug(
                f"📌 Task '{task.task_id}' added to {self.name} queue "
                f"(priority={task.priority.name}, user_tier={task.user_tier.name})"
            )
        return task.task_id
    
    async def get_next(self) -> Optional[QueuedTask]:
        """Get next task to execute"""
        async with self._lock:
            if self._pending and len(self._running) < self.max_concurrent:
                task = self._pending.pop(0)
                self._running[task.task_id] = task
                task.started_at = datetime.utcnow()
                
                LOGGER.info(
                    f"▶️  Task '{task.task_id}' started from {self.name} queue "
                    f"(queued for {task.duration_in_queue().total_seconds():.1f}s)"
                )
                return task
            return None
    
    async def complete(self, task_id: str):
        """Mark task as completed"""
        async with self._lock:
            if task_id in self._running:
                task = self._running.pop(task_id)
                task.completed_at = datetime.utcnow()
                self._completed.append(task)
                
                LOGGER.info(
                    f"✅ Task '{task_id}' completed ({task.total_duration().total_seconds():.1f}s)"
                )
    
    async def fail(self, task_id: str, reason: str = "Unknown"):
        """Mark task as failed"""
        async with self._lock:
            if task_id in self._running:
                task = self._running.pop(task_id)
                task.completed_at = datetime.utcnow()
                self._failed[task_id] = task
                
                LOGGER.error(f"❌ Task '{task_id}' failed: {reason}")
    
    async def get_stats(self) -> QueueStats:
        """Get queue statistics"""
        async with self._lock:
            total = len(self._pending) + len(self._running) + len(self._completed) + len(self._failed)
            
            wait_times = [t.duration_in_queue().total_seconds() for t in self._completed if t.started_at]
            avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0
            
            exec_times = [t.total_duration().total_seconds() for t in self._completed if t.total_duration()]
            avg_exec = sum(exec_times) / len(exec_times) if exec_times else 0
            
            return QueueStats(
                queue_name=self.name,
                total_tasks=total,
                queued_tasks=len(self._pending),
                running_tasks=len(self._running),
                completed_tasks=len(self._completed),
                failed_tasks=len(self._failed),
                average_wait_time=avg_wait,
                average_execution_time=avg_exec,
            )
    
    async def list_pending(self, user_id: Optional[int] = None) -> List[QueuedTask]:
        """List pending tasks"""
        async with self._lock:
            tasks = self._pending[:]
            if user_id:
                tasks = [t for t in tasks if t.user_id == user_id]
            return tasks
    
    async def list_running(self) -> List[QueuedTask]:
        """List running tasks"""
        async with self._lock:
            return list(self._running.values())
    
    async def remove(self, task_id: str) -> bool:
        """Remove task from queue"""
        async with self._lock:
            # Try pending
            for i, task in enumerate(self._pending):
                if task.task_id == task_id:
                    self._pending.pop(i)
                    LOGGER.info(f"🗑️  Task '{task_id}' removed from pending")
                    return True
            
            # Try running
            if task_id in self._running:
                del self._running[task_id]
                LOGGER.warning(f"⚠️  Task '{task_id}' removed from running")
                return True
        
        return False
    
    async def requeue(self, task_id: str, new_priority: TaskPriority = None) -> bool:
        """Move task back to queue with optional new priority"""
        async with self._lock:
            if task_id in self._failed:
                task = self._failed.pop(task_id)
                if new_priority:
                    task.priority = new_priority
                task.queued_at = datetime.utcnow()
                task.started_at = None
                task.completed_at = None
                insort(self._pending, task, key=lambda t: -t.calculate_score())
                LOGGER.info(f"🔄 Task '{task_id}' requeued")
                return True
        
        return False


class DynamicQueueManager:
    """Manages multiple named queues with load balancing"""
    
    def __init__(self):
        self.queues: Dict[str, PriorityQueue] = {}
        self._dispatcher_tasks: Dict[str, asyncio.Task] = {}
        self._executors: Dict[str, Callable] = {}
        self._stats_history: List[Dict[str, QueueStats]] = []
    
    def create_queue(self, name: str, max_concurrent: int = 3):
        """Create a new named queue"""
        self.queues[name] = PriorityQueue(name, max_concurrent)
        LOGGER.info(f"📋 Queue '{name}' created (max_concurrent={max_concurrent})")
    
    async def add_task(
        self,
        task_id: str,
        user_id: int,
        operation: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        user_tier: UserTier = UserTier.STANDARD,
        queue_name: str = "default",
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        execute_callback: Optional[Callable] = None,
    ) -> bool:
        """Add task to queue"""
        if queue_name not in self.queues:
            LOGGER.warning(f"⚠️  Queue '{queue_name}' doesn't exist, using default")
            queue_name = "default"
        
        task = QueuedTask(
            task_id=task_id,
            user_id=user_id,
            operation=operation,
            priority=priority,
            user_tier=user_tier,
            file_name=file_name,
            file_size=file_size,
            execute_callback=execute_callback,
        )
        
        await self.queues[queue_name].add(task)
        return True
    
    async def set_executor(self, queue_name: str, executor: Callable):
        """Set executor for queue"""
        self._executors[queue_name] = executor
        LOGGER.debug(f"Executor set for queue '{queue_name}'")
    
    async def start_dispatcher(self, queue_name: str):
        """Start dispatcher for a queue"""
        if queue_name in self._dispatcher_tasks:
            LOGGER.warning(f"⚠️  Dispatcher already running for '{queue_name}'")
            return
        
        if queue_name not in self._executors:
            LOGGER.warning(f"⚠️  No executor set for queue '{queue_name}'")
            return
        
        queue = self.queues[queue_name]
        executor = self._executors[queue_name]
        
        async def dispatch_loop():
            LOGGER.info(f"🚀 Dispatcher started for queue '{queue_name}'")
            while True:
                try:
                    # Get next task
                    task = await queue.get_next()
                    
                    if task:
                        try:
                            # Execute task
                            if asyncio.iscoroutinefunction(executor):
                                await executor(task)
                            else:
                                executor(task)
                            
                            await queue.complete(task.task_id)
                        except Exception as e:
                            await queue.fail(task.task_id, str(e))
                    else:
                        await asyncio.sleep(0.5)  # Poll interval
                
                except Exception as e:
                    LOGGER.error(f"Dispatcher error: {e}", exc_info=True)
                    await asyncio.sleep(1)
        
        task = asyncio.create_task(dispatch_loop())
        self._dispatcher_tasks[queue_name] = task
    
    async def get_all_stats(self) -> Dict[str, QueueStats]:
        """Get statistics for all queues"""
        stats = {}
        for name, queue in self.queues.items():
            stats[name] = await queue.get_stats()
        return stats
    
    async def get_user_position(self, user_id: int, queue_name: str = "default") -> Optional[int]:
        """Get user's position in queue"""
        if queue_name not in self.queues:
            return None
        
        tasks = await self.queues[queue_name].list_pending(user_id)
        return len(tasks)
    
    async def cancel_task(self, task_id: str, queue_name: str = "default") -> bool:
        """Cancel a task"""
        if queue_name not in self.queues:
            return False
        
        return await self.queues[queue_name].remove(task_id)
    
    async def boost_task(self, task_id: str, queue_name: str = "default") -> bool:
        """Boost task priority"""
        if queue_name not in self.queues:
            return False
        
        tasks = await self.queues[queue_name].list_pending()
        for task in tasks:
            if task.task_id == task_id:
                # Move to HIGH priority
                task.priority = TaskPriority.HIGH
                LOGGER.info(f"⬆️  Task '{task_id}' priority boosted")
                return True
        
        return False
    
    async def log_stats(self):
        """Log queue statistics"""
        stats = await self.get_all_stats()
        
        for name, s in stats.items():
            LOGGER.info(
                f"📊 {name} queue: "
                f"pending={s.queued_tasks}, running={s.running_tasks}, "
                f"completed={s.completed_tasks}, failed={s.failed_tasks}, "
                f"avg_wait={s.average_wait_time:.1f}s, avg_exec={s.average_execution_time:.1f}s"
            )
        
        self._stats_history.append(stats)


# Global instance
queue_manager = DynamicQueueManager()

# Create default queues
async def initialize_queue_system():
    """Initialize queue system"""
    queue_manager.create_queue(QueueName.DEFAULT.value, max_concurrent=3)
    queue_manager.create_queue(QueueName.VIP.value, max_concurrent=2)
    queue_manager.create_queue(QueueName.EMERGENCY.value, max_concurrent=1)
    queue_manager.create_queue(QueueName.BATCH.value, max_concurrent=5)
    LOGGER.info("✅ Queue system initialized")
