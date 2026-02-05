"""
Phase 2 Integration Examples
Shows how to use Phase 2 features throughout the codebase

Safe Innovation Path - Phase 2

Examples for:
1. Logging important events
2. Triggering alerts
3. Creating backups
4. Profiling operations
5. Verifying data integrity
"""

from .logger_manager import logger_manager
from .alert_manager import alert_manager, AlertType, AlertSeverity
from .backup_manager import backup_manager
from .profiler import profiler
from .recovery_manager import recovery_manager


# ============ Example 1: Logging Events ============
def example_logging():
    """
    Example: Using Logger Manager to log custom events
    """
    # Log a download event
    logger_manager.log_download(
        client="aria2",
        filename="movie.mkv",
        size_bytes=2048576000,
        duration_seconds=300,
        speed_mbps=50.5,
        status="completed",
    )

    # Log an upload event
    logger_manager.log_upload(
        service="google_drive",
        files=["video1.mp4", "video2.mp4"],
        total_size_bytes=5242880000,
        duration_seconds=600,
        avg_speed_mbps=25.2,
        status="completed",
    )

    # Log a performance event
    logger_manager.log_performance_event(
        operation="database_query",
        duration_ms=250,
        status="slow",  # Flagged as slow
        details={"query": "find_files", "records": 1000},
    )

    # Log an error event
    logger_manager.log_error_event(
        error_type="ConnectionError",
        message="Failed to connect to Redis",
        severity="high",
        traceback="...",
        context={"component": "redis_manager"},
    )


# ============ Example 2: Alert System ============
async def example_alerts():
    """
    Example: Using Alert Manager to trigger and handle alerts
    """
    # Define alert handler
    async def on_disk_full(alert):
        print(f"ALERT: {alert.alert_type} - {alert.message}")
        # Send notification, log, etc.

    # Subscribe to specific alert type
    alert_manager.subscribe(AlertType.DISK_FULL, on_disk_full)

    # Trigger alerts
    alert_manager.trigger_alert(
        alert_type=AlertType.DISK_FULL,
        severity=AlertSeverity.CRITICAL,
        message="Disk space critically low (5% remaining)",
    )

    alert_manager.trigger_alert(
        alert_type=AlertType.DOWNLOAD_FAILED,
        severity=AlertSeverity.HIGH,
        message="Download failed: Connection timeout",
        metadata={"url": "https://example.com/file.zip", "retries": 3},
    )

    # Get alert summary
    summary = alert_manager.get_alert_summary()
    print(f"Alerts by severity: {summary}")


# ============ Example 3: Backup System ============
async def example_backups():
    """
    Example: Using Backup Manager for critical data
    """
    # Create backup
    backup_id = await backup_manager.create_backup(
        description="Pre-update backup of all tasks",
        paths=["/data/tasks", "/data/downloads"],
    )
    print(f"Backup created: {backup_id}")

    # Verify backup integrity
    is_valid = await backup_manager.verify_backup(backup_id)
    print(f"Backup valid: {is_valid}")

    # List all backups
    backups = backup_manager.list_backups()
    print(f"Available backups: {len(backups)}")

    # Get backup statistics
    stats = backup_manager.get_backup_stats()
    print(f"Total backups: {stats['total_backups']}, Total size: {stats['total_size_gb']} GB")


# ============ Example 4: Profiling ============
async def example_profiling():
    """
    Example: Using Profiler to monitor operation performance
    """
    # Profile a synchronous operation
    with profiler.profile_sync("file_processing"):
        # Simulate work
        total = sum(i for i in range(1000000))

    # Profile an async operation
    async def slow_database_query():
        # Simulate slow query
        import asyncio

        await asyncio.sleep(0.1)
        return "result"

    async with profiler.profile_async("db_query"):
        result = await slow_database_query()

    # Get statistics for specific operation
    stats = profiler.get_stats("file_processing")
    if stats:
        print(f"File processing - Count: {stats.count}, Avg: {stats.avg_duration_ms}ms")

    # Get slow operations (> 5 seconds)
    slow_ops = profiler.get_slow_operations()
    print(f"Slow operations: {len(slow_ops)}")


# ============ Example 5: Data Recovery ============
async def example_recovery():
    """
    Example: Using Recovery Manager for data integrity
    """
    # Verify integrity of critical paths
    critical_paths = ["/data/downloads", "/data/metadata"]
    check_result = await recovery_manager.verify_integrity(critical_paths)

    print(f"Integrity check passed: {check_result.passed}")
    if not check_result.passed:
        print(f"Issues found: {check_result.errors}")

    # Auto-repair corrupted files
    if not check_result.passed:
        recovery_result = await recovery_manager.repair_corrupted_data(
            check_result.errors
        )
        print(f"Repair completed: {recovery_result}")

    # Get recovery history
    history = recovery_manager.get_integrity_history()
    print(f"Recent integrity checks: {len(history)}")


# ============ Example 6: Combined Usage ============
async def example_combined_usage():
    """
    Example: Combining multiple Phase 2 features
    """
    # Profile a complex download operation
    async with profiler.profile_async("download_and_backup"):
        # Perform download
        print("Starting download...")

        logger_manager.log_download(
            client="aria2",
            filename="large_file.zip",
            size_bytes=1073741824,
            duration_seconds=120,
            speed_mbps=70,
            status="in_progress",
        )

        # Check if we need to make a backup before proceeding
        await backup_manager.create_backup(
            description="Pre-download backup",
            paths=["/data/downloads"],
        )

        logger_manager.log_download(
            client="aria2",
            filename="large_file.zip",
            size_bytes=1073741824,
            duration_seconds=120,
            speed_mbps=70,
            status="completed",
        )

        # Verify integrity after download
        check = await recovery_manager.verify_integrity(["/data/downloads"])
        if not check.passed:
            alert_manager.trigger_alert(
                alert_type=AlertType.CUSTOM,
                severity=AlertSeverity.HIGH,
                message="Data integrity issues detected after download",
            )


# ============ Example 7: Error Handling ============
def example_error_handling():
    """
    Example: Proper error handling with Phase 2 features
    """
    try:
        # Some operation that might fail
        result = some_risky_operation()
    except Exception as e:
        # Log the error
        logger_manager.log_error_event(
            error_type=type(e).__name__,
            message=str(e),
            severity="high",
            context={"operation": "some_risky_operation"},
        )

        # Trigger alert
        alert_manager.trigger_alert(
            alert_type=AlertType.CUSTOM,
            severity=AlertSeverity.HIGH,
            message=f"Operation failed: {e}",
        )

        # Attempt recovery
        try:
            recovery_manager.auto_recover()
        except Exception as recovery_e:
            logger_manager.log_error_event(
                error_type="RecoveryError",
                message=str(recovery_e),
                severity="critical",
            )


def some_risky_operation():
    """Placeholder for a risky operation"""
    return "success"


# ============ Example 8: Testing Phase 2 ============
async def test_all_phase2_features():
    """
    Comprehensive test of all Phase 2 features
    """
    print("\n=== Testing Phase 2 Features ===\n")

    print("1. Testing Logger Manager...")
    example_logging()
    print("✅ Logger test complete\n")

    print("2. Testing Alert Manager...")
    await example_alerts()
    print("✅ Alert test complete\n")

    print("3. Testing Backup Manager...")
    await example_backups()
    print("✅ Backup test complete\n")

    print("4. Testing Profiler...")
    await example_profiling()
    print("✅ Profiler test complete\n")

    print("5. Testing Recovery Manager...")
    await example_recovery()
    print("✅ Recovery test complete\n")

    print("6. Testing Combined Usage...")
    await example_combined_usage()
    print("✅ Combined test complete\n")

    print("=== All Phase 2 Tests Complete ===\n")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_all_phase2_features())
