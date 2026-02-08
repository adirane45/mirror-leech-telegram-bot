"""
Task Models - Data structures for distributed task execution

Includes:
- Task priority and state enumerations
- Task, result, and assignment dataclasses
- Task executor and listener interfaces
- Default executor implementation
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Dict, List, Optional, Any


# ============================================================================
# ENUMS
# ============================================================================

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


# ============================================================================
# DATACLASSES
# ============================================================================

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
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
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
    assigned_at: datetime = field(default_factory=lambda: datetime.now(UTC))
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
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    
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


# ============================================================================
# TASK EXECUTORS AND LISTENERS
# ============================================================================

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


class DefaultTaskExecutor(TaskExecutor):
    """Default task executor implementation"""
    
    async def execute(self, task: Task) -> TaskResult:
        """Execute task"""
        import asyncio
        
        start = datetime.now(UTC)
        try:
            # Simulate task execution
            await asyncio.sleep(0.01)
            
            elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)
            return TaskResult(
                task_id=task.task_id,
                success=True,
                output=task.payload.get('expected_output'),
                execution_time_ms=elapsed
            )
        except Exception as e:
            elapsed = int((datetime.now(UTC) - start).total_seconds() * 1000)
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
