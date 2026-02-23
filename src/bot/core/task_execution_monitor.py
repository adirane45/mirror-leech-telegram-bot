"""
Task Monitor for execution monitoring and failure handling

Implements:
- Task execution monitoring
- Timeout and failure detection
- Task completion tracking
- Retry logic and error handling
"""

import asyncio
from datetime import datetime, UTC
from typing import Dict, Callable, Optional

from .task_models import (
    TaskState,
    Task,
    TaskResult,
    CoordinatorMetrics,
    TaskCoordinatorListener,
)


class TaskMonitor:
    """
    Monitors task execution and handles failures
    
    Responsible for:
    - Task state monitoring
    - Timeout detection
    - Failure handling with retries
    - Task completion tracking
    - Metrics collection
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.results: Dict[str, TaskResult] = {}
        self.listeners = []
        self.metrics = CoordinatorMetrics()
        self.enabled = False
        self.task_timeout_seconds = 300
    
    async def monitor_loop(self) -> None:
        """Background loop for monitoring tasks"""
        while self.enabled:
            try:
                # Check for timeouts
                now = datetime.now(UTC)
                for task in self.tasks.values():
                    if task.state == TaskState.RUNNING:
                        age = (now - task.created_at).total_seconds()
                        if age > task.timeout_seconds:
                            task.state = TaskState.FAILED
                            await self._handle_task_failure(task, "Timeout")
                
                # Update metrics
                running_count = sum(
                    1 for t in self.tasks.values()
                    if t.state == TaskState.RUNNING
                )
                self.metrics.active_tasks = running_count
                self.metrics.last_updated = datetime.now(UTC)
                
                await asyncio.sleep(5)
            except Exception:
                await asyncio.sleep(5)
    
    async def _handle_task_failure(self, task: Task, error: str) -> bool:
        """Handle task failure with retries"""
        try:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.state = TaskState.RETRYING
                # Task will be re-queued by coordinator
                return True
            else:
                task.state = TaskState.FAILED
                
                # Notify listeners
                for listener in self.listeners:
                    await listener.on_task_failed(task, error)
                
                self.metrics.failed_tasks += 1
                return False
        except Exception:
            return False
    
    async def complete_task(self, task_id: str, result: TaskResult) -> bool:
        """Mark task as completed"""
        if task_id not in self.tasks:
            return False
        
        try:
            task = self.tasks[task_id]
            task.state = TaskState.COMPLETED
            task.result = result
            self.results[task_id] = result
            self.metrics.completed_tasks += 1
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_task_completed(task, result)
            
            return True
        except Exception:
            return False
    
    async def fail_task(self, task_id: str, error: str) -> bool:
        """Mark task as failed"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        return await self._handle_task_failure(task, error)
    
    def set_enabled(self, enabled: bool) -> None:
        """Set monitor enabled state"""
        self.enabled = enabled
    
    def set_task_reference(self, tasks: Dict[str, Task]) -> None:
        """Set reference to tasks dict"""
        self.tasks = tasks
    
    def add_listener(self, listener: TaskCoordinatorListener) -> None:
        """Add monitor listener"""
        if listener not in self.listeners:
            self.listeners.append(listener)
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result for completed task"""
        return self.results.get(task_id)
