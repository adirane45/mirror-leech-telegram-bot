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
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Set, Optional, Any, Callable
from abc import ABC, abstractmethod


class TaskPriority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    DEFERRED = "deferred"


class TaskState(str, Enum):
    """State of a task"""
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskType(str, Enum):
    """Types of tasks"""
    COMPUTE = "compute"
    IO = "io"
    NETWORK = "network"
    STORAGE = "storage"
    REPLICATION = "replication"
    BACKUP = "backup"


@dataclass
class TaskDependency:
    """Task dependency information"""
    task_id: str
    must_complete_before: bool = True


@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'task_id': self.task_id,
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class Task:
    """Task definition"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    task_type: TaskType = TaskType.COMPUTE
    priority: TaskPriority = TaskPriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    state: TaskState = TaskState.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    assigned_node: Optional[str] = None
    dependencies: List[TaskDependency] = field(default_factory=list)
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: int = 300
    result: Optional[TaskResult] = None
    progress: int = 0  # 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'task_type': self.task_type.value,
            'priority': self.priority.value,
            'state': self.state.value,
            'assigned_node': self.assigned_node,
            'progress': self.progress,
            'retry_count': self.retry_count
        }


@dataclass
class TaskAssignment:
    """Assignment of task to node"""
    assignment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    node_id: str = ""
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None


@dataclass
class CoordinatorMetrics:
    """Metrics for task coordination"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_execution_time_ms: float = 0.0
    tasks_in_queue: int = 0
    active_tasks: int = 0
    node_utilization: Dict[str, float] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'avg_execution_time_ms': round(self.avg_execution_time_ms, 2),
            'tasks_in_queue': self.tasks_in_queue,
            'active_tasks': self.active_tasks,
            'node_utilization': self.node_utilization,
            'last_updated': self.last_updated.isoformat()
        }


class TaskExecutor(ABC):
    """Abstract executor for tasks"""
    
    @abstractmethod
    async def execute(self, task: Task) -> TaskResult:
        """Execute a task"""
        pass
    
    @abstractmethod
    async def supports(self, task_type: TaskType) -> bool:
        """Check if executor supports task type"""
        pass
    
    @abstractmethod
    async def get_utilization(self) -> float:
        """Get current utilization (0.0-1.0)"""
        pass


class TaskCoordinatorListener(ABC):
    """Abstract listener for task events"""
    
    @abstractmethod
    async def on_task_queued(self, task: Task) -> None:
        """Called when task is queued"""
        pass
    
    @abstractmethod
    async def on_task_started(self, task: Task, node_id: str) -> None:
        """Called when task starts"""
        pass
    
    @abstractmethod
    async def on_task_completed(self, task: Task, result: TaskResult) -> None:
        """Called when task completes"""
        pass
    
    @abstractmethod
    async def on_task_failed(self, task: Task, error: str) -> None:
        """Called when task fails"""
        pass


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
                now = datetime.utcnow()
                for task in self.tasks.values():
                    if task.state == TaskState.RUNNING:
                        age = (now - task.created_at).total_seconds()
                        if age > task.timeout_seconds:
                            task.state = TaskState.FAILED
                            await self._handle_task_failure(task, "Timeout")
                
                # Update metrics
                self.metrics.active_tasks = len(await self.get_tasks_by_state(TaskState.RUNNING))
                self.metrics.tasks_in_queue = len(self.queue)
                self.metrics.last_updated = datetime.utcnow()
                
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


class DefaultTaskExecutor(TaskExecutor):
    """Default task executor implementation"""
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute task"""
        start = datetime.utcnow()
        try:
            # Simulate task execution
            await asyncio.sleep(0.01)
            
            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
            return TaskResult(
                task_id=task.task_id,
                success=True,
                output=task.payload.get('expected_output'),
                execution_time_ms=elapsed
            )
        except Exception as e:
            elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
            return TaskResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time_ms=elapsed
            )
    
    async def supports(self, task_type: TaskType) -> bool:
        """Support all task types"""
        return True
    
    async def get_utilization(self) -> float:
        """Get utilization"""
        return 0.3
