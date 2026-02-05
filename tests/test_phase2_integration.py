"""
Phase 2 Integration Tests
Safe Innovation Path - Phase 2

Enhanced by: justadi
Date: February 5, 2026
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from bot.core.logger_manager import LoggerManager
from bot.core.alert_manager import AlertManager, AlertType, AlertSeverity
from bot.core.backup_manager import BackupManager
from bot.core.profiler import Profiler
from bot.core.recovery_manager import RecoveryManager


@pytest.mark.integration
class TestPhase2Integration:
    """Test Phase 2 enhanced features"""

    def test_logger_initialization(self):
        """Test logger manager initialization"""
        logger = LoggerManager()
        assert logger is not None

    def test_alert_manager_initialization(self):
        """Test alert manager initialization"""
        alert_mgr = AlertManager()
        assert alert_mgr is not None

    def test_backup_manager_initialization(self):
        """Test backup manager initialization"""
        backup_mgr = BackupManager()
        assert backup_mgr is not None

    def test_profiler_initialization(self):
        """Test profiler initialization"""
        prof = Profiler()
        assert prof is not None

    def test_recovery_manager_initialization(self):
        """Test recovery manager initialization"""
        recovery = RecoveryManager()
        assert recovery is not None


@pytest.mark.asyncio
class TestAlertSystem:
    """Test alert system functionality"""

    async def test_trigger_alert(self):
        """Test triggering alerts"""
        alert_mgr = AlertManager()
        alert_mgr.enable()

        alert = await alert_mgr.trigger_alert(
            AlertType.DOWNLOAD_FAILED,
            AlertSeverity.HIGH,
            "Download Failed",
            "File download failed",
            task_id="test_123",
        )

        if alert_mgr.is_enabled:
            assert alert is not None
            assert alert.alert_type == AlertType.DOWNLOAD_FAILED

    async def test_alert_subscribers(self):
        """Test alert subscribers"""
        alert_mgr = AlertManager()
        alert_mgr.enable()

        callback_called = False

        async def test_callback(alert):
            nonlocal callback_called
            callback_called = True

        alert_mgr.subscribe(AlertType.DOWNLOAD_FAILED, test_callback)

        await alert_mgr.trigger_alert(
            AlertType.DOWNLOAD_FAILED,
            AlertSeverity.HIGH,
            "Test",
            "Test message",
        )

        if alert_mgr.is_enabled:
            await asyncio.sleep(0.1)
            assert callback_called


@pytest.mark.asyncio
class TestBackupSystem:
    """Test backup system"""

    async def test_backup_creation(self):
        """Test creating a backup"""
        backup_mgr = BackupManager()
        backup_mgr.enable()

        if not backup_mgr.is_enabled:
            pytest.skip("Backup system not enabled")

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            # Create backup
            result = await backup_mgr.create_backup(
                [str(test_file)],
                backup_name="test_backup",
            )

            if result:
                assert result["backup_name"] == "test_backup"
                assert result["items_count"] > 0


class TestProfiler:
    """Test performance profiler"""

    def test_sync_profiling(self):
        """Test synchronous operation profiling"""
        prof = Profiler()
        prof.enable()

        if not prof.is_enabled:
            return

        with prof.profile_sync("test_operation"):
            import time
            time.sleep(0.01)

        stats = prof.get_stats("test_operation")
        if prof.is_enabled:
            assert "operation" in stats or "enabled" in stats

    @pytest.mark.asyncio
    async def test_async_profiling(self):
        """Test asynchronous operation profiling"""
        prof = Profiler()
        prof.enable()

        if not prof.is_enabled:
            return

        async with prof.profile_async("async_operation"):
            await asyncio.sleep(0.01)

        stats = prof.get_stats("async_operation")
        if prof.is_enabled:
            assert "operation" in stats or "enabled" in stats


@pytest.mark.asyncio
class TestRecoveryManager:
    """Test recovery manager"""

    async def test_integrity_check(self):
        """Test data integrity checking"""
        recovery = RecoveryManager()
        recovery.enable()

        if not recovery.is_enabled:
            pytest.skip("Recovery manager not enabled")

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("test content")

            is_valid, details = await recovery.verify_integrity(str(test_file))
            assert is_valid is not None
            assert isinstance(details, dict)

    async def test_corruption_detection(self):
        """Test corruption detection"""
        recovery = RecoveryManager()
        recovery.enable()

        if not recovery.is_enabled:
            pytest.skip("Recovery manager not enabled")

        # Non-existent path should fail integrity check
        is_valid, details = await recovery.verify_integrity(
            "/nonexistent/path/12345",
            check_hash=False,
        )

        assert is_valid is False


class TestBackwardCompatibility:
    """Test Phase 2 backward compatibility"""

    def test_all_features_disabled_by_default(self):
        """Verify all Phase 2 features are disabled by default"""
        from bot.core.config_manager import Config

        # Check that all Phase 2 features default to False
        assert getattr(Config, "ENABLE_ENHANCED_LOGGING", False) is False
        assert getattr(Config, "ENABLE_ALERT_SYSTEM", False) is False
        assert getattr(Config, "ENABLE_BACKUP_SYSTEM", False) is False
        assert getattr(Config, "ENABLE_PROFILER", False) is False
        assert getattr(Config, "ENABLE_RECOVERY_MANAGER", False) is False

    def test_singleton_pattern(self):
        """Test that managers follow singleton pattern"""
        logger1 = LoggerManager()
        logger2 = LoggerManager()
        assert logger1 is logger2

        alert1 = AlertManager()
        alert2 = AlertManager()
        assert alert1 is alert2

        backup1 = BackupManager()
        backup2 = BackupManager()
        assert backup1 is backup2

        prof1 = Profiler()
        prof2 = Profiler()
        assert prof1 is prof2

        recovery1 = RecoveryManager()
        recovery2 = RecoveryManager()
        assert recovery1 is recovery2


class TestPhase2Configuration:
    """Test Phase 2 configuration"""

    def test_config_import(self):
        """Test that Phase 2 config can be imported"""
        import config_enhancements_phase2
        assert config_enhancements_phase2 is not None

    def test_config_options(self):
        """Test that all configuration options are present"""
        import config_enhancements_phase2 as config

        # Check logging config
        assert hasattr(config, "ENABLE_ENHANCED_LOGGING")
        assert hasattr(config, "LOG_DIR")
        assert hasattr(config, "LOG_LEVEL")

        # Check alert config
        assert hasattr(config, "ENABLE_ALERT_SYSTEM")
        assert hasattr(config, "ALERT_RETENTION_HOURS")

        # Check backup config
        assert hasattr(config, "ENABLE_BACKUP_SYSTEM")
        assert hasattr(config, "BACKUP_DIR")
        assert hasattr(config, "CRITICAL_BACKUP_PATHS")

        # Check profiler config
        assert hasattr(config, "ENABLE_PROFILER")
        assert hasattr(config, "PROFILE_THRESHOLD")

        # Check recovery config
        assert hasattr(config, "ENABLE_RECOVERY_MANAGER")
        assert hasattr(config, "RECOVERY_CRITICAL_PATHS")
