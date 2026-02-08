"""
Task Coordinator for distributed task execution

Implements:
- Task scheduling and execution
- Load distribution across cluster nodes
- Task prioritization and dependencies
- Progress tracking and callbacks
- Fault tolerance with retries
"""

import asyncio
import uuid
from datetime import datetime, UTC
from typing import Dict, List, Set, Optional, Any

# Import models
from .task_models import (
    TaskPriority,
    TaskState,
    TaskType,
    TaskDependency,
    TaskResult,
    Task,
    TaskAssignment,
    CoordinatorMetrics,
    TaskExecutor,
    TaskCoordinatorListener,
    DefaultTaskExecutor,
)

# Import specialized components
from .task_execution_monitor import TaskMonitor
from .task_assignment_manager import TaskAssignmentManager


class TaskCoordinator:
    """
    Coordinates distributed task execution across cluster nodes
    
    Singleton instance managing:
    - Task queuing and scheduling
    - Load distribution
    - Task dependencies
    - Progress tracking
    - Fault tolerance with retries
    """
    
    _instance: Optional['TaskCoordinator'] = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.enabled = False
        self.node_id = ""
        self.tasks: Dict[str, Task] = {}
        self.queue: List[str] = []  # task IDs
        self.peers: Set[str] = set()
        self.listeners: List[TaskCoordinatorListener] = []
        self.executors: Dict[TaskType, TaskExecutor] = {}
        self.max_concurrent_tasks = 10
        
        # Component delegation
        self.monitor = TaskMonitor()
        self.assignment_manager = TaskAssignmentManager()
        
        # Background tasks
        self._scheduler_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
    
    @classmethod
    def get_instance(cls) -> 'TaskCoordinator':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def start(self, node_id: str = "") -> bool:
        """Start task coordinator"""
        if self.enabled:
            return True
        
        try:
            self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
            self.enabled = True
            
            # Configure components
            self.monitor.set_enabled(True)
            self.monitor.set_task_reference(self.tasks)
            self.assignment_manager.set_node_info(self.node_id, self.peers)
            self.assignment_manager.set_task_reference(self.tasks)
            
            # Start background tasks
            self._scheduler_task = asyncio.create_task(self._scheduling_loop())
            self._monitor_task = asyncio.create_task(self.monitor.monitor_loop())
            
            return True
        except Exception:
            self.enabled = False
            return False
    
    async def stop(self) -> bool:
        """Stop task coordinator"""
        if not self.enabled:
            return True
        
        try:
            self.enabled = False
            self.monitor.set_enabled(False)
            
            if self._scheduler_task:
                self._scheduler_task.cancel()
            if self._monitor_task:
                self._monitor_task.cancel()
            
            await asyncio.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # TASK MANAGEMENT
    # ========================================================================
    
    async def submit_task(self, task: Task) -> bool:
        """Submit a task for execution"""
        if not self.enabled:
            return False
        
        try:
            self.tasks[task.task_id] = task
            task.state = TaskState.QUEUED
            self.queue.append(task.task_id)
            self.monitor.metrics.total_tasks += 1
            self.monitor.metrics.tasks_in_queue = len(self.queue)
            
            # Notify listeners
            for listener in self.listeners:
                await listener.on_task_queued(task)
            
            return True
        except Exception:
            return False
    
    async def submit_batch(self, tasks: List[Task]) -> bool:
        """Submit multiple tasks"""
        try:
            for task in tasks:
                await self.submit_task(task)
            return True
        except Exception:
            return False
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel pending or running task"""
        if task_id not in self.tasks:
            return False
        
        try:
            task = self.tasks[task_id]
            if task.state in [TaskState.PENDING, TaskState.QUEUED, TaskState.ASSIGNED]:
                task.state = TaskState.CANCELLED
                if task_id in self.queue:
                    self.queue.remove(task_id)
                return True
            return False
        except Exception:
            return False
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        return self.tasks.get(task_id)
    
    async def get_tasks_by_state(self, state: TaskState) -> List[Task]:
        """Get all tasks in given state"""
        return [t for t in self.tasks.values() if t.state == state]
    
    # ========================================================================
    # SCHEDULING LOOP
    # ========================================================================
    
    async def _scheduling_loop(self) -> None:
        """Background loop for scheduling tasks"""
        while self.enabled:
            try:
                # Get queued tasks, sorted by priority
                queued = [self.tasks[tid] for tid in self.queue if tid in self.tasks]
                priority_order = {
                    "critical": 0, "high": 1, "normal": 2, "low": 3, "deferred": 4
                }
                queued.sort(key=lambda t: priority_order.get(t.priority.value, 5))
                
                # Assign to nodes
                for task in queued[:self.max_concurrent_tasks]:
                    # Check dependencies
                    if await self.assignment_manager.check_dependencies(task):
                        assigned_node = await self.assignment_manager.select_target_node(task)
                        if assigned_node:
                            await self.assignment_manager.assign_task(task, assigned_node)
                            self.queue.remove(task.task_id)
                
                # Update metrics
                self.monitor.metrics.tasks_in_queue = len(self.queue)
                
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(1)
    
    # ========================================================================
    # TASK COMPLETION AND FAILURE
    # ========================================================================
    
    async def complete_task(self, task_id: str, result: TaskResult) -> bool:
        """Mark task as completed"""
        return await self.monitor.complete_task(task_id, result)
    
    async def fail_task(self, task_id: str, error: str) -> bool:
        """Mark task as failed with retries"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        result = await self.monitor.fail_task(task_id, error)
        
        # Re-queue if retrying
        if task.state == TaskState.RETRYING and task_id not in self.queue:
            self.queue.append(task_id)
        
        return result
    
    # ========================================================================
    # MANAGEMENT
    # ========================================================================
    
    async def add_executor(self, task_type: TaskType, executor: TaskExecutor) -> bool:
        """Register task executor"""
        try:
            self.executors[task_type] = executor
            return True
        except Exception:
            return False
    
    async def register_peer(self, peer_id: str) -> bool:
        """Register peer node"""
        try:
            self.peers.add(peer_id)
            self.assignment_manager.register_peer(peer_id)
            return True
        except Exception:
            return False
    
    async def add_listener(self, listener: TaskCoordinatorListener) -> bool:
        """Register task coordinator listener"""
        try:
            self.listeners.append(listener)
            self.monitor.add_listener(listener)
            return True
        except Exception:
            return False
    
    async def get_metrics(self) -> CoordinatorMetrics:
        """Get coordinator metrics"""
        return self.monitor.metrics
    
    async def get_queue_size(self) -> int:
        """Get size of task queue"""
        return len(self.queue)
    
    async def is_enabled(self) -> bool:
        """Check if coordinator is enabled"""
        return self.enabled
