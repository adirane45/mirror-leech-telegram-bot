"""
Phase 2 Configuration - Enhanced Logging, Monitoring, Backups
Safe Innovation Path - Phase 2 Enhancement Options

Enhanced by: justadi
Date: February 5, 2026
"""

# ============================================================================
# ENHANCED LOGGING CONFIGURATION
# ============================================================================

# Enable structured JSON logging for better log aggregation
ENABLE_ENHANCED_LOGGING = False

# Log directory (relative to bot root)
LOG_DIR = "logs"

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# Maximum log file size before rotation (in bytes)
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

# Number of backup log files to keep
LOG_BACKUP_COUNT = 5

# ============================================================================
# ALERT SYSTEM CONFIGURATION
# ============================================================================

# Enable alert system for error tracking
ENABLE_ALERT_SYSTEM = False

# Keep alerts for this many hours
ALERT_RETENTION_HOURS = 24

# Critical error thresholds
ALERT_THRESHOLDS = {
    "disk_full_percent": 90,
    "memory_high_percent": 85,
    "cpu_high_percent": 95,
    "api_error_rate": 10,  # errors per minute
}

# Alert notification channels
ALERT_CHANNELS = {
    "critical": ["telegram", "email"],  # Critical errors go to both
    "high": ["telegram"],
    "medium": ["log"],
    "low": ["log"],
}

# ============================================================================
# BACKUP SYSTEM CONFIGURATION
# ============================================================================

# Enable automated backup system
ENABLE_BACKUP_SYSTEM = False

# Backup directory
BACKUP_DIR = "backups"

# Critical paths to backup automatically
CRITICAL_BACKUP_PATHS = [
    "config.py",  # Bot configuration
    "tokens",     # Authentication tokens (if stored locally)
    "data",       # User/task data
]

# Backup schedule (cron format for Celery beat)
BACKUP_SCHEDULE = {
    "hourly": "0 * * * *",  # Every hour
    "daily": "0 0 * * *",   # Daily at midnight
    "weekly": "0 0 * * 0",  # Weekly on Sunday
}

# Default backup frequency (hourly, daily, weekly)
BACKUP_FREQUENCY = "daily"

# Number of backups to keep per schedule
BACKUP_RETENTION = {
    "hourly": 24,   # Keep 24 hourly backups
    "daily": 30,    # Keep 30 daily backups
    "weekly": 12,   # Keep 12 weekly backups
}

# ============================================================================
# PERFORMANCE PROFILER CONFIGURATION
# ============================================================================

# Enable performance profiler
ENABLE_PROFILER = False

# Operations to profile (None = all operations)
PROFILED_OPERATIONS = None  # Set to a list to profile specific operations

# Profile threshold - log operations slower than this (seconds)
PROFILE_THRESHOLD = 1.0

# Keep profiler metrics for this many hours
PROFILER_RETENTION_HOURS = 24

# ============================================================================
# RECOVERY & DATA INTEGRITY CONFIGURATION
# ============================================================================

# Enable recovery manager
ENABLE_RECOVERY_MANAGER = False

# Enable automatic recovery attempts
ENABLE_AUTO_RECOVERY = False

# Critical paths that require automatic recovery
RECOVERY_CRITICAL_PATHS = [
    "config.py",
    "bot/__main__.py",
]

# Verification schedule (check integrity)
INTEGRITY_CHECK_INTERVAL = 3600  # seconds (1 hour)

# ============================================================================
# LOG AGGREGATION (ELK Stack) CONFIGURATION
# ============================================================================

# Enable ELK stack integration
ENABLE_ELK_INTEGRATION = False

# Elasticsearch configuration
ELASTICSEARCH_HOST = "localhost"
ELASTICSEARCH_PORT = 9200
ELASTICSEARCH_INDEX = "mltb-logs"

# Kibana configuration (for dashboards)
KIBANA_HOST = "localhost"
KIBANA_PORT = 5601

# ============================================================================
# NOTIFICATION CONFIGURATION
# ============================================================================

# Email notifications for critical alerts
SMTP_SERVER = None  # e.g., "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = None
SMTP_PASSWORD = None
SMTP_FROM_EMAIL = None
SMTP_TO_EMAILS = []  # List of recipient emails

# Telegram notifications for alerts
ALERT_TELEGRAM_CHAT_ID = None  # Chat ID for alert messages

# ============================================================================
# PERFORMANCE THRESHOLDS
# ============================================================================

# Warning thresholds for various operations
PERFORMANCE_THRESHOLDS = {
    "download_timeout": 300,      # seconds
    "upload_timeout": 300,         # seconds
    "api_timeout": 30,             # seconds
    "slow_download_speed": 0.1,    # MB/s
    "slow_upload_speed": 0.1,      # MB/s
}

# ============================================================================
# CLEANUP POLICIES
# ============================================================================

# Auto-cleanup configuration
ENABLE_AUTO_CLEANUP = True

# Cleanup old logs after this many days
LOG_CLEANUP_DAYS = 7

# Cleanup old backups after this many days
BACKUP_CLEANUP_DAYS = 30

# Cleanup old alerts after this many hours
ALERT_CLEANUP_HOURS = 24

# Cleanup old profiler metrics after this many hours
PROFILER_CLEANUP_HOURS = 24
