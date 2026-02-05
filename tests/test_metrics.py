"""
Unit Tests for Metrics Collector
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

import pytest
from bot.core.metrics import MetricsCollector


@pytest.mark.unit
class TestMetricsCollector:
    """Test Metrics Collector functionality"""
    
    def test_initialization(self, metrics_collector):
        """Test metrics collector initialization"""
        assert metrics_collector is not None
        assert hasattr(metrics_collector, 'downloads_total')
        assert hasattr(metrics_collector, 'uploads_total')
        assert hasattr(metrics_collector, 'cpu_usage_percent')
    
    def test_is_enabled_when_disabled(self, metrics_collector):
        """Test is_enabled() when metrics are disabled"""
        assert metrics_collector.is_enabled() == False
    
    def test_record_download_when_disabled(self, metrics_collector):
        """Test record_download() doesn't fail when disabled"""
        # Should not raise any exception
        metrics_collector.record_download(
            source_type="http",
            size=1024,
            duration=10.5,
            status="success"
        )
    
    def test_record_upload_when_disabled(self, metrics_collector):
        """Test record_upload() doesn't fail when disabled"""
        metrics_collector.record_upload(
            destination="gdrive",
            size=2048,
            duration=15.5,
            status="success"
        )
    
    def test_record_command_when_disabled(self, metrics_collector):
        """Test record_command() doesn't fail when disabled"""
        metrics_collector.record_command(
            command="mirror",
            user_type="user"
        )
    
    def test_record_error_when_disabled(self, metrics_collector):
        """Test record_error() doesn't fail when disabled"""
        metrics_collector.record_error(
            error_type="download_failed",
            severity="error"
        )
    
    def test_generate_metrics_when_disabled(self, metrics_collector):
        """Test generate_metrics() returns placeholder when disabled"""
        result = metrics_collector.generate_metrics()
        assert isinstance(result, bytes)
        assert b"Metrics disabled" in result
    
    def test_get_content_type(self, metrics_collector):
        """Test get_content_type() returns correct type"""
        content_type = metrics_collector.get_content_type()
        assert isinstance(content_type, str)
        assert "text/plain" in content_type
