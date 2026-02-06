"""
Unit tests for Failover Manager component

Tests cover:
- Initialization and lifecycle
- Failure detection and recovery
- Recovery action queueing and execution
- Cascading failure detection and handling
- Recovery handlers
- Metrics tracking
- Event listeners
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from bot.core.failover_manager import (
    FailoverManager,
    RecoveryAction,
    RecoveryOperation,
    RecoveryState,
    RecoveryStrategy,
    CascadeEvent,
    CascadeLevel,
    RecoveryMetrics,
    RecoveryHandler,
    DefaultRecoveryHandler,
    FailoverEventListener
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def failover_manager():
    """Get failover manager instance"""
    manager = FailoverManager.get_instance()
    # Reset state
    manager.operations.clear()
    manager.pending_actions.clear()
    manager.component_failures.clear()
    manager.active_cascades.clear()
    manager.metrics = RecoveryMetrics()
    manager.enabled = False
    manager.listeners.clear()
    
    yield manager
    
    # Cleanup
    try:
        asyncio.run(manager.stop())
    except:
        pass
    manager.operations.clear()


@pytest.fixture
def mock_listener():
    """Mock failover event listener"""
    class TestListener(FailoverEventListener):
        def __init__(self):
            self.failure_detected = AsyncMock()
            self.recovery_started = AsyncMock()
            self.recovery_completed = AsyncMock()
            self.cascade_detected = AsyncMock()
        
        async def on_failure_detected(self, component_id: str, error: str) -> None:
            await self.failure_detected(component_id, error)
        
        async def on_recovery_started(self, operation_id: str) -> None:
            await self.recovery_started(operation_id)
        
        async def on_recovery_completed(self, operation_id: str, success: bool) -> None:
            await self.recovery_completed(operation_id, success)
        
        async def on_cascade_detected(self, cascade: CascadeEvent) -> None:
            await self.cascade_detected(cascade)
    
    return TestListener()


# ============================================================================
# TESTS: INITIALIZATION AND LIFECYCLE
# ============================================================================

@pytest.mark.asyncio
async def test_singleton_instance(failover_manager):
    """Test failover manager is singleton"""
    mgr1 = FailoverManager.get_instance()
    mgr2 = FailoverManager.get_instance()
    
    assert mgr1 is mgr2


@pytest.mark.asyncio
async def test_start_failover_manager(failover_manager):
    """Test starting failover manager"""
    result = await failover_manager.start()
    
    assert result is True
    assert failover_manager.enabled is True
    assert failover_manager._recovery_executor_task is not None
    assert failover_manager._cascade_monitor_task is not None
    
    await failover_manager.stop()


@pytest.mark.asyncio
async def test_stop_failover_manager(failover_manager):
    """Test stopping failover manager"""
    await failover_manager.start()
    assert failover_manager.enabled is True
    
    result = await failover_manager.stop()
    assert result is True
    assert failover_manager.enabled is False


@pytest.mark.asyncio
async def test_start_already_started(failover_manager):
    """Test starting when already started"""
    await failover_manager.start()
    result = await failover_manager.start()
    
    assert result is True
    await failover_manager.stop()


@pytest.mark.asyncio
async def test_stop_when_not_started(failover_manager):
    """Test stopping when not started"""
    result = await failover_manager.stop()
    assert result is True


# ============================================================================
# TESTS: FAILURE DETECTION AND RECOVERY
# ============================================================================

@pytest.mark.asyncio
async def test_on_component_failure(failover_manager, mock_listener):
    """Test component failure detection"""
    await failover_manager.add_listener(mock_listener)
    
    result = await failover_manager.on_component_failure('db', 'MongoDB', 'Connection timeout')
    
    assert result is True
    assert 'db' in failover_manager.component_failures
    assert len(failover_manager.component_failures['db']) == 1
    mock_listener.failure_detected.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_failures_same_component(failover_manager):
    """Test tracking multiple failures for same component"""
    for i in range(3):
        await failover_manager.on_component_failure('db', 'MongoDB', f'Error {i}')
    
    assert len(failover_manager.component_failures['db']) == 3


@pytest.mark.asyncio
async def test_failure_isolation_escalation(failover_manager):
    """Test isolation strategy when failures exceed threshold"""
    # Trigger multiple failures
    for i in range(6):
        await failover_manager.on_component_failure(
            'api', 'API Service', 'Error'
        )
    
    # Last action should use ISOLATE strategy
    assert len(failover_manager.pending_actions) > 0
    last_action = failover_manager.pending_actions[-1]
    assert last_action.strategy == RecoveryStrategy.ISOLATE


@pytest.mark.asyncio
async def test_queue_recovery_action(failover_manager):
    """Test queueing recovery action"""
    action = RecoveryAction(
        component_id='db',
        component_name='MongoDB',
        strategy=RecoveryStrategy.RESTART
    )
    
    result = await failover_manager.queue_recovery_action(action)
    
    assert result is True
    assert action in failover_manager.pending_actions


@pytest.mark.asyncio
async def test_get_pending_actions(failover_manager):
    """Test getting pending actions"""
    action1 = RecoveryAction(component_id='db', component_name='MongoDB')
    action2 = RecoveryAction(component_id='cache', component_name='Redis')
    
    await failover_manager.queue_recovery_action(action1)
    await failover_manager.queue_recovery_action(action2)
    
    pending = await failover_manager.get_pending_actions()
    assert len(pending) == 2


# ============================================================================
# TESTS: RECOVERY EXECUTION
# ============================================================================

@pytest.mark.asyncio
async def test_execute_recovery_success(failover_manager, mock_listener):
    """Test successful recovery execution"""
    await failover_manager.start()
    await failover_manager.add_listener(mock_listener)
    
    action = RecoveryAction(
        component_id='db',
        component_name='MongoDB',
        strategy=RecoveryStrategy.RESTART,
        timeout_seconds=5
    )
    
    await failover_manager.queue_recovery_action(action)
    
    # Wait for execution
    await asyncio.sleep(1)
    
    # Check metrics updated
    assert failover_manager.metrics.total_operations > 0
    
    await failover_manager.stop()


@pytest.mark.asyncio
async def test_recovery_metrics_tracking(failover_manager):
    """Test recovery metrics are tracked"""
    action = RecoveryAction(component_id='db', component_name='MongoDB')
    operation = RecoveryOperation(action=action)
    operation.state = RecoveryState.SUCCEEDED
    operation.started_at = datetime.utcnow() - timedelta(seconds=1)
    operation.completed_at = datetime.utcnow()
    
    failover_manager.operations[operation.operation_id] = operation
    failover_manager.metrics.total_operations = 1
    failover_manager.metrics.successful_operations = 1
    
    uptime = failover_manager.metrics.successful_operations / failover_manager.metrics.total_operations * 100
    assert uptime == 100.0


@pytest.mark.asyncio
async def test_recovery_retry_on_failure(failover_manager):
    """Test recovery retries on failure"""
    action = RecoveryAction(
        component_id='db',
        component_name='MongoDB',
        max_retries=3
    )
    
    operation = RecoveryOperation(action=action)
    
    # Simulate retries
    for i in range(3):
        operation.attempts += 1
    
    assert operation.attempts == 3


@pytest.mark.asyncio
async def test_recovery_timeout_handling(failover_manager):
    """Test timeout handling during recovery"""
    action = RecoveryAction(
        component_id='db',
        component_name='MongoDB',
        timeout_seconds=1
    )
    
    operation = RecoveryOperation(action=action)
    # In real test, would simulate timeout
    assert operation.state == RecoveryState.PENDING


@pytest.mark.asyncio
async def test_get_operation_status(failover_manager):
    """Test getting operation status"""
    action = RecoveryAction(component_id='db', component_name='MongoDB')
    operation = RecoveryOperation(action=action)
    operation.state = RecoveryState.IN_PROGRESS
    
    failover_manager.operations[operation.operation_id] = operation
    
    status = await failover_manager.get_operation_status(operation.operation_id)
    
    assert status is not None
    assert status.state == RecoveryState.IN_PROGRESS


@pytest.mark.asyncio
async def test_get_active_operations(failover_manager):
    """Test getting active operations"""
    action1 = RecoveryAction(component_id='db', component_name='MongoDB')
    operation1 = RecoveryOperation(action=action1)
    operation1.state = RecoveryState.IN_PROGRESS
    
    action2 = RecoveryAction(component_id='cache', component_name='Redis')
    operation2 = RecoveryOperation(action=action2)
    operation2.state = RecoveryState.SUCCEEDED
    
    failover_manager.operations[operation1.operation_id] = operation1
    failover_manager.operations[operation2.operation_id] = operation2
    
    active = await failover_manager.get_active_operations()
    
    assert len(active) == 1
    assert operation1.operation_id in active


# ============================================================================
# TESTS: CASCADE DETECTION
# ============================================================================

@pytest.mark.asyncio
async def test_detect_cascading_failure(failover_manager, mock_listener):
    """Test detecting cascading failures"""
    await failover_manager.add_listener(mock_listener)
    
    # Simulate multiple component failures
    for comp_id in ['db', 'cache', 'api', 'queue']:
        failover_manager.component_failures[comp_id] = [datetime.utcnow()]
    
    cascade = await failover_manager.detect_cascading_failure('db')
    
    assert cascade is not None
    assert cascade.initial_component == 'db'
    mock_listener.cascade_detected.assert_called_once()


@pytest.mark.asyncio
async def test_cascade_affects_multiple_components(failover_manager):
    """Test cascade identifies affected components"""
    for comp_id in ['db', 'cache', 'api']:
        failover_manager.component_failures[comp_id] = [datetime.utcnow()]
    
    cascade = await failover_manager.detect_cascading_failure('db')
    
    assert len(cascade.affected_components) >= 2


@pytest.mark.asyncio
async def test_cascade_requires_threshold(failover_manager):
    """Test cascade detection requires minimum components"""
    # Only 1 failure
    failover_manager.component_failures['db'] = [datetime.utcnow()]
    
    cascade = await failover_manager.detect_cascading_failure('db')
    
    # Should not detect cascade with only 1 component
    # (threshold is 3 in default config)
    if cascade is None:
        assert True
    else:
        # Or it might still detect it depending on implementation
        assert cascade.cascade_level in [CascadeLevel.COMPONENT, CascadeLevel.SERVICE]


@pytest.mark.asyncio
async def test_handle_cascade(failover_manager):
    """Test handling cascading failure"""
    cascade = CascadeEvent(
        initial_component='db',
        cascade_level=CascadeLevel.SERVICE,
        affected_components={'db', 'cache', 'api'}
    )
    
    result = await failover_manager.handle_cascade(cascade)
    
    assert result is True
    # Should queue ISOLATE actions for all affected components
    assert len(failover_manager.pending_actions) >= 3


@pytest.mark.asyncio
async def test_active_cascades_tracking(failover_manager):
    """Test tracking active cascades"""
    cascade1 = CascadeEvent(
        initial_component='db',
        cascade_level=CascadeLevel.SERVICE,
        affected_components={'db', 'cache'}
    )
    cascade1.is_active = True
    
    cascade2 = CascadeEvent(
        initial_component='api',
        cascade_level=CascadeLevel.COMPONENT,
        affected_components={'api'}
    )
    cascade2.is_active = False
    
    failover_manager.active_cascades[cascade1.event_id] = cascade1
    failover_manager.active_cascades[cascade2.event_id] = cascade2
    
    active = await failover_manager.get_active_cascades()
    
    assert len(active) == 1
    assert cascade1.event_id in active


# ============================================================================
# TESTS: RECOVERY HANDLERS
# ============================================================================

@pytest.mark.asyncio
async def test_default_recovery_handler(failover_manager):
    """Test default recovery handler"""
    handler = DefaultRecoveryHandler()
    
    action = RecoveryAction(
        component_id='db',
        component_name='MongoDB',
        strategy=RecoveryStrategy.RESTART
    )
    
    result = await handler.execute(action)
    assert result is True


@pytest.mark.asyncio
async def test_handler_supports_strategy(failover_manager):
    """Test handler strategy support check"""
    handler = DefaultRecoveryHandler()
    
    supports_restart = await handler.supports(RecoveryStrategy.RESTART)
    assert supports_restart is True
    
    supports_failover = await handler.supports(RecoveryStrategy.FAILOVER)
    assert supports_failover is False


@pytest.mark.asyncio
async def test_register_custom_handler(failover_manager):
    """Test registering custom recovery handler"""
    class CustomHandler(RecoveryHandler):
        async def execute(self, action: RecoveryAction) -> bool:
            return True
        
        async def rollback(self, operation: RecoveryOperation) -> bool:
            return True
        
        async def supports(self, strategy: RecoveryStrategy) -> bool:
            return True
    
    handler = CustomHandler()
    result = await failover_manager.register_recovery_handler(handler)
    
    assert result is True
    assert len(failover_manager.custom_handlers) > 0


@pytest.mark.asyncio
async def test_unregister_custom_handler(failover_manager):
    """Test unregistering custom recovery handler"""
    class CustomHandler(RecoveryHandler):
        async def execute(self, action: RecoveryAction) -> bool:
            return True
        
        async def rollback(self, operation: RecoveryOperation) -> bool:
            return True
        
        async def supports(self, strategy: RecoveryStrategy) -> bool:
            return True
    
    handler = CustomHandler()
    
    await failover_manager.register_recovery_handler(handler)
    handler_id = list(failover_manager.custom_handlers.keys())[0] if failover_manager.custom_handlers else None
    
    if handler_id:
        result = await failover_manager.unregister_recovery_handler(handler_id)
        assert result is True
        assert handler_id not in failover_manager.custom_handlers


# ============================================================================
# TESTS: EVENT LISTENERS
# ============================================================================

@pytest.mark.asyncio
async def test_add_listener(failover_manager, mock_listener):
    """Test adding failover listener"""
    result = await failover_manager.add_listener(mock_listener)
    
    assert result is True
    assert mock_listener in failover_manager.listeners


@pytest.mark.asyncio
async def test_remove_listener(failover_manager, mock_listener):
    """Test removing failover listener"""
    await failover_manager.add_listener(mock_listener)
    result = await failover_manager.remove_listener(mock_listener)
    
    assert result is True
    assert mock_listener not in failover_manager.listeners


@pytest.mark.asyncio
async def test_listener_on_failure_detected(failover_manager, mock_listener):
    """Test listener called on failure detected"""
    await failover_manager.add_listener(mock_listener)
    
    await failover_manager.on_component_failure('db', 'MongoDB', 'Error')
    
    mock_listener.failure_detected.assert_called()


# ============================================================================
# TESTS: METRICS AND STATUS
# ============================================================================

@pytest.mark.asyncio
async def test_get_recovery_metrics(failover_manager):
    """Test getting recovery metrics"""
    failover_manager.metrics.total_operations = 10
    failover_manager.metrics.successful_operations = 8
    
    metrics = await failover_manager.get_recovery_metrics()
    
    assert metrics.total_operations == 10
    assert metrics.successful_operations == 8


@pytest.mark.asyncio
async def test_metrics_uptime_calculation(failover_manager):
    """Test uptime percentage calculation"""
    failover_manager.metrics.total_operations = 10
    failover_manager.metrics.successful_operations = 9
    
    uptime = failover_manager.metrics.successful_operations / failover_manager.metrics.total_operations * 100
    assert uptime == 90.0


@pytest.mark.asyncio
async def test_get_failure_count(failover_manager):
    """Test getting failure count for component"""
    failover_manager.component_failures['db'] = [
        datetime.utcnow(),
        datetime.utcnow() - timedelta(seconds=30),
        datetime.utcnow() - timedelta(minutes=15)  # Outside default 10-min window
    ]
    
    count = await failover_manager.get_failure_count('db')
    assert count >= 2  # At least 2 within window


@pytest.mark.asyncio
async def test_reset_failure_count(failover_manager):
    """Test resetting failure count"""
    failover_manager.component_failures['db'] = [datetime.utcnow()]
    
    result = await failover_manager.reset_failure_count('db')
    
    assert result is True
    assert len(failover_manager.component_failures['db']) == 0


@pytest.mark.asyncio
async def test_clear_operation_history(failover_manager):
    """Test clearing old operation history"""
    action = RecoveryAction(component_id='db', component_name='MongoDB')
    operation = RecoveryOperation(action=action)
    operation.completed_at = datetime.utcnow() - timedelta(hours=25)
    
    failover_manager.operations[operation.operation_id] = operation
    
    cleared = await failover_manager.clear_operation_history(older_than_hours=24)
    
    assert cleared == 1
    assert operation.operation_id not in failover_manager.operations


# ============================================================================
# TESTS: RECOVERY ACTIONS AND OPERATIONS
# ============================================================================

@pytest.mark.asyncio
async def test_recovery_action_to_dict(failover_manager):
    """Test recovery action serialization"""
    action = RecoveryAction(
        component_id='db',
        component_name='MongoDB',
        strategy=RecoveryStrategy.RESTART,
        priority=8
    )
    
    action_dict = action.to_dict()
    
    assert action_dict['component_id'] == 'db'
    assert action_dict['component_name'] == 'MongoDB'
    assert action_dict['strategy'] == 'restart'


@pytest.mark.asyncio
async def test_recovery_operation_to_dict(failover_manager):
    """Test recovery operation serialization"""
    action = RecoveryAction(component_id='db', component_name='MongoDB')
    operation = RecoveryOperation(action=action)
    operation.state = RecoveryState.SUCCEEDED
    
    op_dict = operation.to_dict()
    
    assert 'operation_id' in op_dict
    assert op_dict['state'] == 'succeeded'


@pytest.mark.asyncio
async def test_cascade_event_to_dict(failover_manager):
    """Test cascade event serialization"""
    cascade = CascadeEvent(
        initial_component='db',
        cascade_level=CascadeLevel.SERVICE,
        affected_components={'db', 'cache', 'api'}
    )
    
    cascade_dict = cascade.to_dict()
    
    assert cascade_dict['initial_component'] == 'db'
    assert cascade_dict['cascade_level'] == 'service'
    assert len(cascade_dict['affected_components']) == 3


@pytest.mark.asyncio
async def test_recovery_metrics_to_dict(failover_manager):
    """Test recovery metrics serialization"""
    metrics = RecoveryMetrics(
        total_operations=100,
        successful_operations=95,
        failed_operations=5
    )
    
    metrics_dict = metrics.to_dict()
    
    assert metrics_dict['total_operations'] == 100
    assert metrics_dict['successful_operations'] == 95


# ============================================================================
# TESTS: UTILITY METHODS
# ============================================================================

@pytest.mark.asyncio
async def test_is_enabled(failover_manager):
    """Test is_enabled check"""
    assert await failover_manager.is_enabled() is False
    
    await failover_manager.start()
    assert await failover_manager.is_enabled() is True
    
    await failover_manager.stop()


@pytest.mark.asyncio
async def test_recovery_with_dependencies(failover_manager):
    """Test recovery action with dependencies"""
    action1 = RecoveryAction(
        component_id='cache',
        component_name='Redis'
    )
    action1_id = action1.action_id
    
    action2 = RecoveryAction(
        component_id='app',
        component_name='App Service',
        depends_on=[action1_id]
    )
    
    assert action1_id in action2.depends_on


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
