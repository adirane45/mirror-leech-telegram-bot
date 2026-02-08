"""
Centralized logging configuration for the Mirror-Leech Telegram Bot.

This module provides structured logging with:
- JSON formatting for log aggregation
- Request ID tracking across services
- Environment-based log levels
- Log rotation and retention
- Performance tracking
"""

import logging
import logging.handlers
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import os
import uuid


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def __init__(self, include_traceback: bool = True):
        super().__init__()
        self.include_traceback = include_traceback

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add user ID if available
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Add extra fields
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        # Add exception info if present
        if record.exc_info and self.include_traceback:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, default=str)


class RequestIdFilter(logging.Filter):
    """Add request ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID if not present."""
        if not hasattr(record, "request_id"):
            record.request_id = getattr(self, "request_id", str(uuid.uuid4()))
        return True


def setup_logging(
    app_name: str = "mirror-leech-bot",
    log_level: Optional[str] = None,
    log_dir: Optional[str] = None,
    json_logs: bool = True,
    console_output: bool = True,
) -> logging.Logger:
    """
    Setup centralized logging configuration.

    Args:
        app_name: Application name for logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        json_logs: Use JSON formatting for logs
        console_output: Enable console output

    Returns:
        Configured logger instance
    """
    # Get log level from environment or parameter
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")

    # Get log directory
    if log_dir is None:
        log_dir = os.getenv("LOG_DIR", "data/logs")

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.propagate = False

    # Remove existing handlers
    logger.handlers.clear()

    # Create formatters
    if json_logs:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(RequestIdFilter())
        logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / f"{app_name}.log",
        maxBytes=50 * 1024 * 1024,  # 50 MB
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestIdFilter())
    logger.addHandler(file_handler)

    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / f"{app_name}-error.log",
        maxBytes=50 * 1024 * 1024,  # 50 MB
        backupCount=10,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_handler.addFilter(RequestIdFilter())
    logger.addHandler(error_handler)

    # Performance log handler
    perf_handler = logging.handlers.RotatingFileHandler(
        filename=log_path / f"{app_name}-performance.log",
        maxBytes=50 * 1024 * 1024,  # 50 MB
        backupCount=5,
        encoding="utf-8",
    )
    perf_handler.setLevel(logging.INFO)
    perf_handler.setFormatter(formatter)
    perf_handler.addFilter(RequestIdFilter())

    # Create performance logger
    perf_logger = logging.getLogger(f"{app_name}.performance")
    perf_logger.setLevel(logging.INFO)
    perf_logger.addHandler(perf_handler)

    logger.info(
        f"Logging initialized - Level: {log_level}, "
        f"JSON: {json_logs}, Console: {console_output}"
    )

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance by name."""
    return logging.getLogger(name)


def log_performance(
    operation: str,
    duration: float,
    extra: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log performance metrics.

    Args:
        operation: Name of the operation
        duration: Duration in seconds
        extra: Additional context
        logger: Logger instance (uses performance logger if None)
    """
    if logger is None:
        logger = logging.getLogger("mirror-leech-bot.performance")

    log_data = {
        "operation": operation,
        "duration_seconds": round(duration, 4),
        "duration_ms": round(duration * 1000, 2),
    }

    if extra:
        log_data.update(extra)

    logger.info(f"Performance: {operation}", extra={"extra": log_data})


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set request ID for current context.

    Args:
        request_id: Request ID (generates new one if None)

    Returns:
        Request ID
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    # Store in thread-local storage
    import threading

    if not hasattr(threading.current_thread(), "request_id"):
        threading.current_thread().request_id = request_id

    return request_id


def get_request_id() -> Optional[str]:
    """Get request ID from current context."""
    import threading

    return getattr(threading.current_thread(), "request_id", None)


# Initialize default logger
default_logger = setup_logging()
