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
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Set, Optional, Any

# Import models from refactored task_models module
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
        self.results: Dict[str, TaskResult] = {}
        self.assignments: Dict[str, TaskAssignment] = {}
        self.peers: Set[str] = set()
        self.metrics = CoordinatorMetrics()
        self.listeners: List[TaskCoordinatorListener] = []
        self.executors: Dict[TaskType, TaskExecutor] = {}
        self.max_concurrent_tasks = 10
        self.load_balance_strategy = "least_loaded"  # or "round_robin", "random"
        self.task_timeout_seconds = 300
        
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
            
            # Start background tasks
            self._scheduler_task = asyncio.create_task(self._scheduling_loop())
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            
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
            self.metrics.total_tasks += 1
            self.metrics.tasks_in_queue = len(self.queue)
            
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
    # SCHEDULING AND EXECUTION
    # ========================================================================
    
    async def _scheduling_loop(self) -> None:
        """Background loop for scheduling tasks"""
        while self.enabled:
            try:
                # Get queued tasks
                queued = [self.tasks[tid] for tid in self.queue if tid in self.tasks]
                queued.sort(key=lambda t: (
                    {"critical": 0, "high": 1, "normal": 2, "low": 3, "deferred": 4}[t.priority.value]
                ))
                
                # Assign to nodes
                for task in queued[:self.max_concurrent_tasks]:
                    assigned_node = await self._select_target_node(task)
                    if assigned_node:
                        await self._assign_task(task, assigned_node)
                
                await asyncio.sleep(1)
            except Exception:
                await asyncio.sleep(1)
    
    async def _assign_task(self, task: Task, node_id: str) -> bool:
        """Assign task to node"""
        try:
            task.state = TaskState.ASSIGNED
            task.assigned_node = node_id
            self.queue.remove(task.task_id)
            
            assignment = TaskAssignment(
                task_id=task.task_id,
                node_id=node_id
            )
            self.assignments[assignment.assignment_id] = assignment
            
            return True
        except Exception:
            return False
    
    async def _select_target_node(self, task: Task) -> Optional[str]:
        """Select best node for task"""
        if not self.peers:
            return self.node_id
        
        try:
            if self.load_balance_strategy == "least_loaded":
                # Select node with lowest utilization
                best_node = self.node_id
                min_util = 0.5
                
                for peer in self.peers:
                    # In real implementation, query peer for utilization
                    util = 0.3
                    if util < min_util:
                        min_util = util
                        best_node = peer
                
                return best_node
            
            else:  # round_robin, random, etc.
                import random
                nodes = [self.node_id] + list(self.peers)
                return random.choice(nodes)
        except Exception:
            return self.node_id
    
    async def _monitor_loop(self) -> None:
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
                self.metrics.active_tasks = len(await self.get_tasks_by_state(TaskState.RUNNING))
                self.metrics.tasks_in_queue = len(self.queue)
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
                self.queue.append(task.task_id)
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
    
    # ========================================================================
    # TASK DEPENDENCIES
    # ========================================================================
    
    async def check_dependencies(self, task: Task) -> bool:
        """Check if all task dependencies are satisfied"""
        for dep in task.dependencies:
            if dep.task_id not in self.tasks:
                return False
            
            dep_task = self.tasks[dep.task_id]
            if dep.must_complete_before:
                if dep_task.state != TaskState.COMPLETED:
                    return False
        
        return True
    
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
            return True
        except Exception:
            return False
    
    async def add_listener(self, listener: TaskCoordinatorListener) -> bool:
        """Register task coordinator listener"""
        try:
            self.listeners.append(listener)
            return True
        except Exception:
            return False
    
    async def get_metrics(self) -> CoordinatorMetrics:
        """Get coordinator metrics"""
        return self.metrics
    
    async def get_queue_size(self) -> int:
        """Get size of task queue"""
        return len(self.queue)
    
    async def is_enabled(self) -> bool:
        """Check if coordinator is enabled"""
        return self.enabled
