"""
Test suite for Task Coordinator
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from bot.core.task_coordinator import (
    TaskCoordinator, Task, TaskResult, TaskAssignment, CoordinatorMetrics,
    TaskPriority, TaskState, TaskType, TaskDependency, TaskExecutor,
    TaskCoordinatorListener, DefaultTaskExecutor
)


class MockTaskCoordinatorListener(TaskCoordinatorListener):
    """Test listener implementation"""
    
    def __init__(self):
        self.queued_tasks = []
        self.started_tasks = []
        self.completed_tasks = []
        self.failed_tasks = []
    
    async def on_task_queued(self, task: Task) -> None:
        self.queued_tasks.append(task.task_id)
    
    async def on_task_started(self, task: Task, node_id: str) -> None:
        self.started_tasks.append((task.task_id, node_id))
    
    async def on_task_completed(self, task: Task, result: TaskResult) -> None:
        self.completed_tasks.append((task.task_id, result))
    
    async def on_task_failed(self, task: Task, error: str) -> None:
        self.failed_tasks.append((task.task_id, error))


@pytest.fixture
def task_coordinator():
    """Get task coordinator instance"""
    manager = TaskCoordinator.get_instance()
    # Reset state
    manager.enabled = False
    manager.node_id = ""
    manager.tasks.clear()
    manager.queue.clear()
    manager.results.clear()
    manager.assignments.clear()
    manager.peers.clear()
    manager.listeners.clear()
    manager.executors.clear()
    manager.metrics = CoordinatorMetrics()
    
    yield manager
    
    # Cleanup
    try:
        asyncio.run(manager.stop())
    except:
        pass
    manager.enabled = False
    if manager._scheduler_task:
        manager._scheduler_task.cancel()
    if manager._monitor_task:
        manager._monitor_task.cancel()


class TestTaskCoordinatorBasic:
    """Test basic coordinator functionality"""
    
    @pytest.mark.asyncio
    async def test_singleton_instance(self, task_coordinator):
        """Test singleton pattern"""
        c1 = TaskCoordinator.get_instance()
        c2 = TaskCoordinator.get_instance()
        assert c1 is c2
    
    @pytest.mark.asyncio
    async def test_start_stop(self, task_coordinator):
        """Test start and stop"""
        coordinator = task_coordinator
        assert not coordinator.enabled
        
        assert await coordinator.start("test-node")
        assert coordinator.enabled
        assert coordinator.node_id == "test-node"
        
        assert await coordinator.stop()
        assert not coordinator.enabled
    
    @pytest.mark.asyncio
    async def test_start_idempotent(self, task_coordinator):
        """Test start is idempotent"""
        coordinator = task_coordinator
        
        assert await coordinator.start("node1")
        assert coordinator.enabled
        
        # Second start should succeed
        assert await coordinator.start("node2")
        assert coordinator.enabled
        # Node ID should be unchanged
        assert coordinator.node_id == "node1"
    
    @pytest.mark.asyncio
    async def test_stop_when_disabled(self, task_coordinator):
        """Test stop when already disabled"""
        coordinator = task_coordinator
        assert not coordinator.enabled
        
        # Stop when disabled should succeed
        assert await coordinator.stop()


class TestTaskSubmission:
    """Test task submission"""
    
    @pytest.mark.asyncio
    async def test_submit_single_task(self, task_coordinator):
        """Test task submission"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task = Task(name="test", task_type=TaskType.COMPUTE)
        assert await coordinator.submit_task(task)
        
        assert task.task_id in coordinator.tasks
        assert task.state == TaskState.QUEUED
        assert task.task_id in coordinator.queue
        assert coordinator.metrics.total_tasks == 1
        assert coordinator.metrics.tasks_in_queue == 1
    
    @pytest.mark.asyncio
    async def test_submit_batch(self, task_coordinator):
        """Test batch submission"""
        coordinator = task_coordinator
        await coordinator.start()
        
        tasks = [Task(name=f"task{i}") for i in range(5)]
        assert await coordinator.submit_batch(tasks)
        
        assert len(coordinator.tasks) == 5
        assert len(coordinator.queue) == 5
        assert coordinator.metrics.total_tasks == 5
    
    @pytest.mark.asyncio
    async def test_submit_when_disabled(self, task_coordinator):
        """Test submission when disabled"""
        coordinator = task_coordinator
        
        task = Task(name="test")
        assert not await coordinator.submit_task(task)
        assert len(coordinator.tasks) == 0
    
    @pytest.mark.asyncio
    async def test_task_get(self, task_coordinator):
        """Test getting task"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task = Task(task_id="task123", name="test")
        await coordinator.submit_task(task)
        
        retrieved = await coordinator.get_task("task123")
        assert retrieved is task
        
        assert await coordinator.get_task("nonexistent") is None


class TestTaskCancellation:
    """Test task cancellation"""
    
    @pytest.mark.asyncio
    async def test_cancel_queued_task(self, task_coordinator):
        """Test cancelling queued task"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task = Task(name="test")
        await coordinator.submit_task(task)
        assert task.state == TaskState.QUEUED
        
        assert await coordinator.cancel_task(task.task_id)
        assert task.state == TaskState.CANCELLED
        assert task.task_id not in coordinator.queue
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_task(self, task_coordinator):
        """Test cancelling nonexistent task"""
        coordinator = task_coordinator
        await coordinator.start()
        
        assert not await coordinator.cancel_task("nonexistent")
    
    @pytest.mark.asyncio
    async def test_cannot_cancel_running_task(self, task_coordinator):
        """Test cannot cancel running task"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task = Task(name="test")
        await coordinator.submit_task(task)
        task.state = TaskState.RUNNING
        
        # Cannot cancel running task
        assert not await coordinator.cancel_task(task.task_id)


class TestTaskState:
    """Test task state queries"""
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_state(self, task_coordinator):
        """Test getting tasks by state"""
        coordinator = task_coordinator
        await coordinator.start()
        
        # Submit 5 tasks
        for i in range(5):
            task = Task(name=f"task{i}")
            await coordinator.submit_task(task)
        
        # All should be queued
        queued = await coordinator.get_tasks_by_state(TaskState.QUEUED)
        assert len(queued) == 5
        
        # Change one to running
        task_to_run = coordinator.tasks[coordinator.queue[0]]
        task_to_run.state = TaskState.RUNNING
        
        queued = await coordinator.get_tasks_by_state(TaskState.QUEUED)
        assert len(queued) == 4
        
        running = await coordinator.get_tasks_by_state(TaskState.RUNNING)
        assert len(running) == 1


class TestTaskCompletion:
    """Test task completion"""
    
    @pytest.mark.asyncio
    async def test_complete_task(self, task_coordinator):
        """Test completing a task"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task = Task(name="test")
        await coordinator.submit_task(task)
        
        result = TaskResult(
            task_id=task.task_id,
            success=True,
            output="success"
        )
        
        assert await coordinator.complete_task(task.task_id, result)
        assert task.state == TaskState.COMPLETED
        assert task.result is result
        assert task.task_id in coordinator.results
        assert coordinator.metrics.completed_tasks == 1
    
    @pytest.mark.asyncio
    async def test_complete_nonexistent_task(self, task_coordinator):
        """Test completing nonexistent task"""
        coordinator = task_coordinator
        await coordinator.start()
        
        result = TaskResult(task_id="nonexistent", success=True)
        assert not await coordinator.complete_task("nonexistent", result)


class TestTaskFailure:
    """Test task failure handling"""
    
    @pytest.mark.asyncio
    async def test_fail_with_retry(self, task_coordinator):
        """Test failure with retry"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task = Task(name="test", max_retries=2)
        await coordinator.submit_task(task)
        
        # First failure
        assert await coordinator.fail_task(task.task_id, "error1")
        assert task.retry_count == 1
        assert task.state == TaskState.RETRYING
        assert task.task_id in coordinator.queue
    
    @pytest.mark.asyncio
    async def test_fail_max_retries(self, task_coordinator):
        """Test failure after max retries"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task = Task(name="test", max_retries=2)
        await coordinator.submit_task(task)
        
        # Exhaust retries
        await coordinator.fail_task(task.task_id, "error1")
        await coordinator.fail_task(task.task_id, "error2")
        await coordinator.fail_task(task.task_id, "error3")
        
        assert task.state == TaskState.FAILED
        assert coordinator.metrics.failed_tasks == 1


class TestTaskDependencies:
    """Test task dependencies"""
    
    @pytest.mark.asyncio
    async def test_check_dependencies_satisfied(self, task_coordinator):
        """Test checking satisfied dependencies"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task1 = Task(task_id="task1", name="task1")
        task2 = Task(
            task_id="task2",
            name="task2",
            dependencies=[TaskDependency(task_id="task1")]
        )
        
        await coordinator.submit_task(task1)
        await coordinator.submit_task(task2)
        
        # task1 not completed - dependencies not satisfied
        assert not await coordinator.check_dependencies(task2)
        
        # Complete task1
        result = TaskResult(task_id="task1", success=True)
        await coordinator.complete_task("task1", result)
        task1.state = TaskState.COMPLETED
        
        # Now dependencies satisfied
        assert await coordinator.check_dependencies(task2)
    
    @pytest.mark.asyncio
    async def test_check_missing_dependency(self, task_coordinator):
        """Test checking missing dependency"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task = Task(
            name="task",
            dependencies=[TaskDependency(task_id="missing")]
        )
        
        assert not await coordinator.check_dependencies(task)


class TestTaskPriority:
    """Test task priority handling"""
    
    @pytest.mark.asyncio
    async def test_priority_queuing(self, task_coordinator):
        """Test task queueing with priority"""
        coordinator = task_coordinator
        await coordinator.start()
        
        # Submit tasks with different priorities
        low = Task(name="low", priority=TaskPriority.LOW)
        critical = Task(name="critical", priority=TaskPriority.CRITICAL)
        normal = Task(name="normal", priority=TaskPriority.NORMAL)
        
        await coordinator.submit_task(low)
        await coordinator.submit_task(critical)
        await coordinator.submit_task(normal)
        
        # All should be in queue
        assert len(coordinator.queue) == 3


class TestTaskMetrics:
    """Test metrics tracking"""
    
    @pytest.mark.asyncio
    async def test_metrics_initialization(self, task_coordinator):
        """Test metrics initialization"""
        coordinator = task_coordinator
        await coordinator.start()
        
        metrics = await coordinator.get_metrics()
        assert metrics.total_tasks == 0
        assert metrics.completed_tasks == 0
        assert metrics.failed_tasks == 0
        assert metrics.tasks_in_queue == 0
    
    @pytest.mark.asyncio
    async def test_metrics_updates(self, task_coordinator):
        """Test metrics updating"""
        coordinator = task_coordinator
        await coordinator.start()
        
        # Submit task
        task = Task(name="test")
        await coordinator.submit_task(task)
        
        metrics = await coordinator.get_metrics()
        assert metrics.total_tasks == 1
        assert metrics.tasks_in_queue == 1
        
        # Complete task
        result = TaskResult(task_id=task.task_id, success=True)
        await coordinator.complete_task(task.task_id, result)
        
        metrics = await coordinator.get_metrics()
        assert metrics.completed_tasks == 1
    
    @pytest.mark.asyncio
    async def test_metrics_serialization(self, task_coordinator):
        """Test metrics can be serialized"""
        coordinator = task_coordinator
        await coordinator.start()
        
        task = Task(name="test")
        await coordinator.submit_task(task)
        
        metrics = await coordinator.get_metrics()
        data = metrics.to_dict()
        
        assert data['total_tasks'] == 1
        assert data['tasks_in_queue'] == 1
        assert 'last_updated' in data


class TestTaskListeners:
    """Test task coordinator listeners"""
    
    @pytest.mark.asyncio
    async def test_add_listener(self, task_coordinator):
        """Test adding listener"""
        coordinator = task_coordinator
        await coordinator.start()
        
        listener = MockTaskCoordinatorListener()
        assert await coordinator.add_listener(listener)
        assert listener in coordinator.listeners
    
    @pytest.mark.asyncio
    async def test_listener_on_task_queued(self, task_coordinator):
        """Test listener on task queued"""
        coordinator = task_coordinator
        await coordinator.start()
        
        listener = MockTaskCoordinatorListener()
        await coordinator.add_listener(listener)
        
        task = Task(task_id="task123", name="test")
        await coordinator.submit_task(task)
        
        await asyncio.sleep(0.1)
        assert "task123" in listener.queued_tasks
    
    @pytest.mark.asyncio
    async def test_listener_on_task_completed(self, task_coordinator):
        """Test listener on task completed"""
        coordinator = task_coordinator
        await coordinator.start()
        
        listener = MockTaskCoordinatorListener()
        await coordinator.add_listener(listener)
        
        task = Task(task_id="task123", name="test")
        await coordinator.submit_task(task)
        
        result = TaskResult(task_id="task123", success=True)
        await coordinator.complete_task("task123", result)
        
        await asyncio.sleep(0.1)
        assert len(listener.completed_tasks) > 0


class TestTaskAssignment:
    """Test task assignment"""
    
    @pytest.mark.asyncio
    async def test_assign_task_to_node(self, task_coordinator):
        """Test assigning task to node"""
        coordinator = task_coordinator
        await coordinator.start("node1")
        
        task = Task(name="test")
        await coordinator.submit_task(task)
        
        assert await coordinator._assign_task(task, "node2")
        assert task.assigned_node == "node2"
        assert task.state == TaskState.ASSIGNED
        assert task.task_id not in coordinator.queue
    
    @pytest.mark.asyncio
    async def test_select_target_node(self, task_coordinator):
        """Test node selection"""
        coordinator = task_coordinator
        await coordinator.start("node1")
        
        task = Task(name="test")
        node = await coordinator._select_target_node(task)
        
        # Should return local node when no peers
        assert node == "node1"
    
    @pytest.mark.asyncio
    async def test_register_peer(self, task_coordinator):
        """Test registering peer node"""
        coordinator = task_coordinator
        await coordinator.start("node1")
        
        assert await coordinator.register_peer("node2")
        assert "node2" in coordinator.peers
        
        assert await coordinator.register_peer("node3")
        assert "node3" in coordinator.peers
    
    @pytest.mark.asyncio
    async def test_node_selection_with_peers(self, task_coordinator):
        """Test node selection with peers"""
        coordinator = task_coordinator
        await coordinator.start("node1")
        
        await coordinator.register_peer("node2")
        await coordinator.register_peer("node3")
        
        task = Task(name="test")
        node = await coordinator._select_target_node(task)
        
        # Should select a valid node
        assert node in ["node1", "node2", "node3"]


class TestTaskExecutor:
    """Test task executor"""
    
    @pytest.mark.asyncio
    async def test_add_executor(self, task_coordinator):
        """Test adding executor"""
        coordinator = task_coordinator
        await coordinator.start()
        
        executor = DefaultTaskExecutor()
        assert await coordinator.add_executor(TaskType.COMPUTE, executor)
        assert coordinator.executors[TaskType.COMPUTE] is executor
    
    @pytest.mark.asyncio
    async def test_default_executor(self, task_coordinator):
        """Test default executor"""
        executor = DefaultTaskExecutor()
        
        assert await executor.supports(TaskType.COMPUTE)
        assert await executor.supports(TaskType.IO)
        
        util = await executor.get_utilization()
        assert 0 <= util <= 1
    
    @pytest.mark.asyncio
    async def test_execute_task(self, task_coordinator):
        """Test executing task"""
        executor = DefaultTaskExecutor()
        
        task = Task(
            name="test",
            payload={"expected_output": "result"}
        )
        
        result = await executor.execute(task)
        assert result.success
        assert result.output == "result"


class TestQueueOperations:
    """Test queue operations"""
    
    @pytest.mark.asyncio
    async def test_queue_size(self, task_coordinator):
        """Test getting queue size"""
        coordinator = task_coordinator
        await coordinator.start()
        
        assert await coordinator.get_queue_size() == 0
        
        for i in range(3):
            task = Task(name=f"task{i}")
            await coordinator.submit_task(task)
        
        assert await coordinator.get_queue_size() == 3
    
    @pytest.mark.asyncio
    async def test_is_enabled(self, task_coordinator):
        """Test is_enabled check"""
        coordinator = task_coordinator
        
        assert not await coordinator.is_enabled()
        
        await coordinator.start()
        assert await coordinator.is_enabled()
        
        await coordinator.stop()
        assert not await coordinator.is_enabled()


class TestTaskSerialization:
    """Test task serialization"""
    
    @pytest.mark.asyncio
    async def test_task_to_dict(self, task_coordinator):
        """Test task serialization"""
        task = Task(
            task_id="task123",
            name="test",
            task_type=TaskType.COMPUTE,
            priority=TaskPriority.HIGH
        )
        
        data = task.to_dict()
        assert data['task_id'] == "task123"
        assert data['name'] == "test"
        assert data['task_type'] == "compute"
        assert data['priority'] == "high"
    
    @pytest.mark.asyncio
    async def test_result_to_dict(self, task_coordinator):
        """Test result serialization"""
        result = TaskResult(
            task_id="task123",
            success=True,
            output="test output"
        )
        
        data = result.to_dict()
        assert data['task_id'] == "task123"
        assert data['success']
        assert data['output'] == "test output"


class TestConcurrency:
    """Test concurrent operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_submissions(self, task_coordinator):
        """Test concurrent task submissions"""
        coordinator = task_coordinator
        await coordinator.start()
        
        tasks = [Task(name=f"task{i}") for i in range(10)]
        
        # Submit concurrently
        results = await asyncio.gather(*[
            coordinator.submit_task(task) for task in tasks
        ])
        
        assert all(results)
        assert len(coordinator.tasks) == 10
    
    @pytest.mark.asyncio
    async def test_concurrent_completions(self, task_coordinator):
        """Test concurrent completions"""
        coordinator = task_coordinator
        await coordinator.start()
        
        # Submit tasks
        tasks = [Task(name=f"task{i}") for i in range(5)]
        for task in tasks:
            await coordinator.submit_task(task)
        
        # Complete concurrently
        results = await asyncio.gather(*[
            coordinator.complete_task(
                task.task_id,
                TaskResult(task_id=task.task_id, success=True)
            ) for task in tasks
        ])
        
        assert all(results)
        assert coordinator.metrics.completed_tasks == 5
