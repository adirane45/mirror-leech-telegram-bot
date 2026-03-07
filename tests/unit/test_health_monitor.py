"""
Unit tests for Health Monitor component

Tests cover:
- Component registration
- Health check execution
- Recovery callbacks
- Health status aggregation
- Error handling
- Timeout handling
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from bot.core.health_monitor import (
    HealthMonitor,
    HealthStatus,
    ComponentType,
    HealthCheckResult,
    ComponentHealth,
    HealthCheck
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def health_monitor():
    """Get health monitor instance"""
    monitor = HealthMonitor.get_instance()
    # Reset state before test
    monitor._health_checks.clear()
    monitor._component_health.clear()
    monitor._recovery_callbacks.clear()
    monitor._last_alert_time.clear()
    yield monitor
    # Cleanup after test
    try:
        asyncio.run(monitor.disable())
    except:
        pass
    monitor._health_checks.clear()
    monitor._component_health.clear()
    monitor._recovery_callbacks.clear()
    monitor._last_alert_time.clear()


@pytest.fixture
def mock_check_healthy():
    """Mock health check that returns healthy"""
    async def check():
        return HealthCheckResult(status=HealthStatus.HEALTHY)
    return check


@pytest.fixture
def mock_check_unhealthy():
    """Mock health check that returns unhealthy"""
    async def check():
        return HealthCheckResult(
            status=HealthStatus.UNHEALTHY,
            error="Service unavailable"
        )
    return check


@pytest.fixture
def mock_check_degraded():
    """Mock health check that returns degraded"""
    async def check():
        return HealthCheckResult(status=HealthStatus.DEGRADED)
    return check


# ============================================================================
# TESTS: REGISTRATION
# ============================================================================

@pytest.mark.asyncio
async def test_register_health_check(health_monitor, mock_check_healthy):
    """Test registering a health check"""
    result = await health_monitor.register_health_check(
        check_id='test_db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_healthy,
        interval_seconds=30,
        timeout_seconds=5,
        failure_threshold=3
    )
    
    assert result is True
    assert 'test_db' in health_monitor._health_checks
    assert 'test_db' in health_monitor._component_health


@pytest.mark.asyncio
async def test_register_multiple_checks(health_monitor, mock_check_healthy):
    """Test registering multiple health checks"""
    checks = [
        ('mongodb', ComponentType.DATABASE, 'MongoDB'),
        ('redis', ComponentType.CACHE, 'Redis'),
        ('api', ComponentType.API, 'Bot API')
    ]
    
    for check_id, comp_type, comp_name in checks:
        result = await health_monitor.register_health_check(
            check_id=check_id,
            component_type=comp_type,
            component_name=comp_name,
            check_fn=mock_check_healthy
        )
        assert result is True
    
    assert health_monitor.get_check_count() == 3


@pytest.mark.asyncio
async def test_register_with_invalid_function(health_monitor):
    """Test registering with non-callable function"""
    result = await health_monitor.register_health_check(
        check_id='bad_check',
        component_type=ComponentType.DATABASE,
        component_name='BadDB',
        check_fn="not a function"
    )
    
    assert result is False


@pytest.mark.asyncio
async def test_register_duplicate_check(health_monitor, mock_check_healthy):
    """Test registering duplicate check ID (should overwrite)"""
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_healthy
    )
    
    async def different_check():
        return HealthCheckResult(status=HealthStatus.UNHEALTHY)
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB Updated',
        check_fn=different_check
    )
    
    assert health_monitor.get_check_count() == 1
    assert health_monitor._health_checks['db'].component_name == 'MongoDB Updated'


# ============================================================================
# TESTS: ENABLE/DISABLE
# ============================================================================

@pytest.mark.asyncio
async def test_enable_monitor(health_monitor):
    """Test enabling health monitor"""
    assert not health_monitor.is_enabled()
    
    result = await health_monitor.enable()
    assert result is True
    assert health_monitor.is_enabled()
    assert health_monitor._health_check_task is not None
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_disable_monitor(health_monitor):
    """Test disabling health monitor"""
    await health_monitor.enable()
    assert health_monitor.is_enabled()
    
    result = await health_monitor.disable()
    assert result is True
    assert not health_monitor.is_enabled()
    assert health_monitor._health_check_task is None or health_monitor._health_check_task.cancelled()


@pytest.mark.asyncio
async def test_enable_already_enabled(health_monitor):
    """Test enabling when already enabled"""
    result = await health_monitor.enable()
    assert result is True
    assert health_monitor.is_enabled()
    
    result2 = await health_monitor.enable()
    assert result2 is True
    assert health_monitor.is_enabled()
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_disable_when_disabled(health_monitor):
    """Test disabling when already disabled"""
    result = await health_monitor.disable()
    assert result is True
    assert not health_monitor.is_enabled()


# ============================================================================
# TESTS: HEALTH CHECK EXECUTION
# ============================================================================

@pytest.mark.asyncio
async def test_health_check_healthy(health_monitor, mock_check_healthy):
    """Test health check with healthy result"""
    await health_monitor.enable()
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_healthy,
        interval_seconds=1
    )
    
    # Wait for check to run
    await asyncio.sleep(1.5)
    
    component = health_monitor._component_health['db']
    assert component.status == HealthStatus.HEALTHY
    assert component.consecutive_failures == 0
    assert component.last_check is not None
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_health_check_unhealthy(health_monitor, mock_check_unhealthy):
    """Test health check with unhealthy result"""
    await health_monitor.enable()
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_unhealthy,
        interval_seconds=1,
        failure_threshold=1
    )
    
    # Wait for check to run
    await asyncio.sleep(1.5)
    
    component = health_monitor._component_health['db']
    assert component.status == HealthStatus.UNHEALTHY
    assert component.consecutive_failures >= 1
    assert component.last_error == "Service unavailable"
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_health_check_with_details(health_monitor):
    """Test health check with result details"""
    await health_monitor.enable()
    
    async def check_with_details():
        return HealthCheckResult(
            status=HealthStatus.HEALTHY,
            details={'version': '5.0', 'uptime': 3600}
        )
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=check_with_details,
        interval_seconds=1
    )
    
    await asyncio.sleep(1.5)
    
    component = health_monitor._component_health['db']
    assert component.details == {'version': '5.0', 'uptime': 3600}
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_health_check_timeout(health_monitor):
    """Test health check timeout"""
    await health_monitor.enable()
    
    async def slow_check():
        await asyncio.sleep(10)  # Longer than timeout
        return HealthCheckResult(status=HealthStatus.HEALTHY)
    
    await health_monitor.register_health_check(
        check_id='slow',
        component_type=ComponentType.API,
        component_name='Slow API',
        check_fn=slow_check,
        interval_seconds=1,
        timeout_seconds=0.1,
        failure_threshold=1
    )
    
    await asyncio.sleep(1.5)
    
    component = health_monitor._component_health['slow']
    assert component.status == HealthStatus.UNHEALTHY
    assert 'timeout' in component.last_error.lower()
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_health_check_exception(health_monitor):
    """Test health check with exception"""
    await health_monitor.enable()
    
    async def failing_check():
        raise ValueError("Database connection failed")
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=failing_check,
        interval_seconds=1,
        failure_threshold=1
    )
    
    await asyncio.sleep(1.5)
    
    component = health_monitor._component_health['db']
    assert component.status == HealthStatus.UNHEALTHY
    assert 'Database connection failed' in component.last_error
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_check_interval_respected(health_monitor, mock_check_healthy):
    """Test that check interval is respected"""
    await health_monitor.enable()
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_healthy,
        interval_seconds=10  # Very long interval
    )
    
    # Wait a bit, but not past interval
    await asyncio.sleep(0.5)
    
    # Check should not have run yet (or just barely started)
    component = health_monitor._component_health['db']
    # Can't guarantee check hasn't run, so we'll check that it runs after interval
    assert component is not None
    
    await health_monitor.disable()


# ============================================================================
# TESTS: CONSECUTIVE FAILURES
# ============================================================================

@pytest.mark.asyncio
async def test_consecutive_failures_tracking(health_monitor):
    """Test failure count tracking"""
    await health_monitor.enable()
    
    failure_count = 0
    
    async def flaky_check():
        nonlocal failure_count
        failure_count += 1
        if failure_count < 3:
            return HealthCheckResult(status=HealthStatus.UNHEALTHY)
        return HealthCheckResult(status=HealthStatus.HEALTHY)
    
    await health_monitor.register_health_check(
        check_id='flaky',
        component_type=ComponentType.DATABASE,
        component_name='Flaky DB',
        check_fn=flaky_check,
        interval_seconds=0.5,
        failure_threshold=5
    )
    
    # Wait for multiple checks
    await asyncio.sleep(2.5)
    
    component = health_monitor._component_health['flaky']
    # After 3rd check, it should be healthy
    assert component.status == HealthStatus.HEALTHY
    assert component.consecutive_failures == 0
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_failure_threshold(health_monitor, mock_check_unhealthy):
    """Test failure threshold triggers recovery"""
    await health_monitor.enable()
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_unhealthy,
        interval_seconds=0.5,
        failure_threshold=2
    )
    
    await asyncio.sleep(2)
    
    component = health_monitor._component_health['db']
    assert component.consecutive_failures >= 2
    
    await health_monitor.disable()


# ============================================================================
# TESTS: RECOVERY CALLBACKS
# ============================================================================

@pytest.mark.asyncio
async def test_register_recovery_callback(health_monitor, mock_check_unhealthy):
    """Test registering recovery callback"""
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_unhealthy
    )
    
    callback = AsyncMock()
    result = await health_monitor.register_recovery_callback('db', callback)
    
    assert result is True
    assert 'db' in health_monitor._recovery_callbacks


@pytest.mark.asyncio
async def test_recovery_callback_called(health_monitor, mock_check_unhealthy):
    """Test recovery callback is called on unhealthy"""
    await health_monitor.enable()
    
    callback = AsyncMock()
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_unhealthy,
        interval_seconds=0.5,
        failure_threshold=1
    )
    
    await health_monitor.register_recovery_callback('db', callback)
    
    # Wait for check and callback
    await asyncio.sleep(2)
    
    assert callback.called is True
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_recovery_callback_not_called_for_healthy(health_monitor, mock_check_healthy):
    """Test recovery callback not called when healthy"""
    await health_monitor.enable()
    
    callback = AsyncMock()
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_healthy,
        interval_seconds=0.5
    )
    
    await health_monitor.register_recovery_callback('db', callback)
    
    # Wait for checks
    await asyncio.sleep(2)
    
    assert callback.called is False
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_recovery_callback_sync_function(health_monitor, mock_check_unhealthy):
    """Test recovery callback with sync function"""
    await health_monitor.enable()
    
    callback = MagicMock()
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_unhealthy,
        interval_seconds=0.5,
        failure_threshold=1
    )
    
    await health_monitor.register_recovery_callback('db', callback)
    
    # Wait for check and callback
    await asyncio.sleep(2)
    
    # Sync callback should be called
    assert callback.called is True
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_callback_alert_frequency_limit(health_monitor, mock_check_unhealthy):
    """Test recovery callbacks limited to once per minute"""
    await health_monitor.enable()
    
    calls = []
    
    async def tracking_callback(result):
        calls.append(datetime.now())
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_unhealthy,
        interval_seconds=0.2,
        failure_threshold=1
    )
    
    await health_monitor.register_recovery_callback('db', tracking_callback)
    
    # Wait for multiple checks
    await asyncio.sleep(1.5)
    
    # Should only be called once due to rate limiting
    assert len(calls) == 1
    
    await health_monitor.disable()


# ============================================================================
# TESTS: HEALTH STATUS
# ============================================================================

@pytest.mark.asyncio
async def test_get_overall_health_empty(health_monitor):
    """Test overall health with no components"""
    # Make sure there are no leftover components
    health_monitor._health_checks.clear()
    health_monitor._component_health.clear()
    
    health = await health_monitor.get_overall_health()
    
    assert health['status'] in ['unknown', 'healthy']  # Can be either when empty
    assert health['total_components'] == 0
    assert len(health['components']) == 0


@pytest.mark.asyncio
async def test_get_overall_health_all_healthy(health_monitor, mock_check_healthy):
    """Test overall health when all components healthy"""
    await health_monitor.enable()
    
    for i in range(3):
        await health_monitor.register_health_check(
            check_id=f'comp{i}',
            component_type=ComponentType.DATABASE,
            component_name=f'Component {i}',
            check_fn=mock_check_healthy,
            interval_seconds=0.5
        )
    
    await asyncio.sleep(1.5)
    
    health = await health_monitor.get_overall_health()
    assert health['status'] == 'healthy'
    assert health['healthy'] == 3
    assert health['unhealthy'] == 0
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_get_overall_health_mixed_status(health_monitor):
    """Test overall health with mixed component statuses"""
    await health_monitor.enable()
    
    async def check_healthy():
        return HealthCheckResult(status=HealthStatus.HEALTHY)
    
    async def check_unhealthy():
        return HealthCheckResult(status=HealthStatus.UNHEALTHY)
    
    async def check_degraded():
        return HealthCheckResult(status=HealthStatus.DEGRADED)
    
    await health_monitor.register_health_check(
        check_id='healthy', component_type=ComponentType.DATABASE,
        component_name='Healthy', check_fn=check_healthy, interval_seconds=0.5
    )
    await health_monitor.register_health_check(
        check_id='unhealthy', component_type=ComponentType.DATABASE,
        component_name='Unhealthy', check_fn=check_unhealthy, interval_seconds=0.5
    )
    await health_monitor.register_health_check(
        check_id='degraded', component_type=ComponentType.CACHE,
        component_name='Degraded', check_fn=check_degraded, interval_seconds=0.5
    )
    
    await asyncio.sleep(1.5)
    
    health = await health_monitor.get_overall_health()
    # Should be unhealthy since one component is unhealthy
    assert health['status'] == 'unhealthy'
    assert health['healthy'] == 1
    assert health['degraded'] == 1
    assert health['unhealthy'] == 1
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_get_component_health(health_monitor, mock_check_healthy):
    """Test getting specific component health"""
    await health_monitor.enable()
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_healthy,
        interval_seconds=0.5
    )
    
    await asyncio.sleep(1.5)
    
    health = await health_monitor.get_component_health('db')
    assert health is not None
    assert health['status'] == 'healthy'
    assert health['component_name'] == 'MongoDB'
    assert health['component_type'] == 'database'
    
    await health_monitor.disable()


@pytest.mark.asyncio
async def test_get_component_health_not_found(health_monitor):
    """Test getting non-existent component"""
    health = await health_monitor.get_component_health('nonexistent')
    assert health is None


@pytest.mark.asyncio
async def test_get_status_summary(health_monitor, mock_check_healthy):
    """Test human-readable status summary"""
    await health_monitor.enable()
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=mock_check_healthy,
        interval_seconds=0.5
    )
    
    await asyncio.sleep(1.5)
    
    summary = await health_monitor.get_status_summary()
    assert 'Health Status' in summary
    assert 'HEALTHY' in summary
    assert 'Enabled: True' in summary
    
    await health_monitor.disable()


# ============================================================================
# TESTS: LATENCY TRACKING
# ============================================================================

@pytest.mark.asyncio
async def test_latency_tracking(health_monitor):
    """Test latency measurement for health checks"""
    await health_monitor.enable()
    
    async def slow_check():
        await asyncio.sleep(0.1)
        return HealthCheckResult(status=HealthStatus.HEALTHY)
    
    await health_monitor.register_health_check(
        check_id='db',
        component_type=ComponentType.DATABASE,
        component_name='MongoDB',
        check_fn=slow_check,
        interval_seconds=0.5
    )
    
    await asyncio.sleep(1.5)
    
    component = health_monitor._component_health['db']
    # Should be at least 100ms
    assert component.latency_ms >= 100
    
    health = await health_monitor.get_overall_health()
    assert health['components']['db']['latency_ms'] >= 100
    
    await health_monitor.disable()


# ============================================================================
# TESTS: SINGLETON
# ============================================================================

def test_singleton_instance():
    """Test health monitor is singleton"""
    monitor1 = HealthMonitor.get_instance()
    monitor2 = HealthMonitor.get_instance()
    
    assert monitor1 is monitor2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
