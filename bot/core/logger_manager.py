"""
Enhanced Logging Manager - Structured JSON Logging
Provides structured logging for better log aggregation and analysis
Safe Innovation Path - Phase 2

Enhanced by: justadi
Date: February 5, 2026
"""

import logging
import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Dict, Any
from logging import getLogger

from .config_manager import Config

LOGGER = getLogger(__name__)


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON for easy log aggregation"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data, default=str)


class LoggerManager:
    """
    Manages enhanced logging with JSON formatting
    Supports log rotation, filtering, and structured logging
    """

    _instance = None
    _enabled = False
    _handlers = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
        return cls._instance

    def enable(self):
        """Enable enhanced logging"""
        self._enabled = getattr(Config, "ENABLE_ENHANCED_LOGGING", False)
        
        if self._enabled:
            self._setup_json_logging()
            LOGGER.info("✅ Enhanced JSON logging enabled")
        else:
            LOGGER.debug("Enhanced logging disabled")

    def _setup_json_logging(self):
        """Setup JSON logging format"""
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # Get the root logger
            root_logger = logging.getLogger()

            # Remove existing handlers to avoid duplicates
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            # Create JSON formatter
            json_formatter = JSONFormatter()

            # File handler with JSON format
            log_file = log_dir / "bot.json.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(json_formatter)
            file_handler.setLevel(logging.INFO)
            root_logger.addHandler(file_handler)
            self._handlers.append(file_handler)

            # Console handler with JSON format (optional, can be plain text)
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(json_formatter)
            console_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(console_handler)
            self._handlers.append(console_handler)

            # Error file handler
            error_file = log_dir / "bot.errors.json.log"
            error_handler = logging.FileHandler(error_file)
            error_handler.setFormatter(json_formatter)
            error_handler.setLevel(logging.ERROR)
            root_logger.addHandler(error_handler)
            self._handlers.append(error_handler)

            LOGGER.info("JSON logging handlers configured")

        except Exception as e:
            LOGGER.error(f"Error setting up JSON logging: {e}")

    @property
    def is_enabled(self) -> bool:
        """Check if enhanced logging is enabled"""
        return self._enabled

    def log_custom_event(
        self,
        level: str,
        message: str,
        **extra_fields: Dict[str, Any]
    ):
        """
        Log a custom event with extra fields

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Main log message
            **extra_fields: Additional fields to include in JSON log
        """
        if not self._enabled:
            return

        logger = logging.getLogger(__name__)
        log_level = getattr(logging, level.upper(), logging.INFO)

        # Create a LogRecord with extra fields
        record = logger.makeRecord(
            logger.name,
            log_level,
            "(custom)",
            0,
            message,
            (),
            None,
        )
        record.extra_fields = extra_fields

        logger.handle(record)

    def log_download(
        self,
        task_id: str,
        filename: str,
        size_bytes: int,
        duration: float,
        speed: float,
        status: str = "completed",
    ):
        """Log a download event"""
        if not self._enabled:
            return

        self.log_custom_event(
            "INFO",
            f"Download completed: {filename}",
            event_type="download",
            task_id=task_id,
            filename=filename,
            size_bytes=size_bytes,
            duration_seconds=duration,
            speed_mbps=speed,
            status=status,
        )

    def log_upload(
        self,
        task_id: str,
        destination: str,
        size_bytes: int,
        duration: float,
        status: str = "completed",
    ):
        """Log an upload event"""
        if not self._enabled:
            return

        self.log_custom_event(
            "INFO",
            f"Upload completed to {destination}",
            event_type="upload",
            task_id=task_id,
            destination=destination,
            size_bytes=size_bytes,
            duration_seconds=duration,
            status=status,
        )

    def log_error_event(
        self,
        error_type: str,
        error_message: str,
        task_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Log an error event"""
        if not self._enabled:
            return

        extra = {
            "event_type": "error",
            "error_type": error_type,
            "error_message": error_message,
        }
        if task_id:
            extra["task_id"] = task_id
        if context:
            extra["context"] = context

        self.log_custom_event("ERROR", f"Error: {error_type}", **extra)

    def log_performance_event(
        self,
        operation: str,
        duration: float,
        metric_name: str,
        metric_value: float,
        **extra_fields: Dict[str, Any]
    ):
        """Log a performance event"""
        if not self._enabled:
            return

        data = {
            "event_type": "performance",
            "operation": operation,
            "duration_seconds": duration,
            metric_name: metric_value,
        }
        data.update(extra_fields)

        self.log_custom_event("INFO", f"Performance: {operation}", **data)

    def close(self):
        """Close all handlers"""
        for handler in self._handlers:
            handler.close()

        self._handlers.clear()
        LOGGER.debug("Logger handlers closed")

    def get_log_stats(self) -> Dict[str, Any]:
        """Get statistics about logs"""
        if not self._enabled:
            return {"enabled": False}

        log_dir = Path("logs")
        if not log_dir.exists():
            return {"enabled": True, "log_files": []}

        log_files = []
        total_size = 0

        for log_file in log_dir.glob("*.json.log"):
            size = log_file.stat().st_size
            log_files.append({
                "name": log_file.name,
                "size_bytes": size,
                "modified": log_file.stat().st_mtime,
            })
            total_size += size

        return {
            "enabled": True,
            "log_directory": str(log_dir),
            "total_size_bytes": total_size,
            "log_files": log_files,
            "log_file_count": len(log_files),
        }


# Singleton instance
logger_manager = LoggerManager()
