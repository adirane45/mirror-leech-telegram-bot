# Safe Innovation Path - Configuration Additions
# Add these to your existing config.py file
# All new features are OPTIONAL and disabled by default

# ==================== REDIS CONFIGURATION ====================
# Enable Redis for caching and improved performance
# Set to False to disable (bot will work without Redis)
ENABLE_REDIS_CACHE = False

# Redis connection settings (only used if ENABLE_REDIS_CACHE=True)
REDIS_HOST = "redis"  # Docker service name or IP address
REDIS_PORT = 6379
REDIS_DB = 0  # Database number (0-15)
REDIS_PASSWORD = ""  # Leave empty if no password

# Cache TTL (Time To Live) in seconds
CACHE_TTL_TASK_STATUS = 300  # 5 minutes
CACHE_TTL_USER_DATA = 3600  # 1 hour
CACHE_TTL_STATISTICS = 600  # 10 minutes

# ==================== CELERY CONFIGURATION ====================
# Enable Celery for distributed task processing
# Set to False to use synchronous processing (existing behavior)
ENABLE_CELERY = False

# Celery broker and backend (only used if ENABLE_CELERY=True)
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/1"

# Celery task routing
CELERY_DOWNLOAD_QUEUE = "downloads"
CELERY_UPLOAD_QUEUE = "uploads"
CELERY_MAINTENANCE_QUEUE = "maintenance"

# ==================== METRICS CONFIGURATION ====================
# Enable Prometheus metrics for monitoring
# Set to False to disable metrics collection
ENABLE_METRICS = False

# Metrics endpoint
METRICS_PORT = 9090
METRICS_PATH = "/metrics"

# Update system metrics interval (seconds)
METRICS_UPDATE_INTERVAL = 60

# ==================== RATE LIMITING ====================
# Rate limiting per user (requires Redis)
ENABLE_RATE_LIMITING = False

# Download limits per user
RATE_LIMIT_DOWNLOADS_PER_HOUR = 10
RATE_LIMIT_DOWNLOADS_PER_DAY = 50

# Upload limits per user
RATE_LIMIT_UPLOADS_PER_HOUR = 10
RATE_LIMIT_UPLOADS_PER_DAY = 50

# Command execution limits
RATE_LIMIT_COMMANDS_PER_MINUTE = 5

# ==================== AUTO-CLEANUP CONFIGURATION ====================
# Automatic cleanup of old files
ENABLE_AUTO_CLEANUP = True

# Delete files older than X hours
AUTO_CLEANUP_MAX_AGE_HOURS = 24

# Run cleanup daily at this hour (0-23)
AUTO_CLEANUP_SCHEDULE_HOUR = 2

# ==================== NOTIFICATION ENHANCEMENTS ====================
# Enhanced notification system
ENABLE_ENHANCED_NOTIFICATIONS = True

# Notification milestones (send notification at these percentages)
NOTIFICATION_MILESTONES = [25, 50, 75]

# Email notifications (optional)
ENABLE_EMAIL_NOTIFICATIONS = False
EMAIL_SMTP_SERVER = ""
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = ""
EMAIL_PASSWORD = ""
EMAIL_FROM_ADDRESS = ""
EMAIL_TO_ADDRESSES = []  # List of email addresses

# ==================== BACKUP CONFIGURATION ====================
# Automatic database backups
ENABLE_AUTO_BACKUP = True
BACKUP_SCHEDULE_HOUR = 3  # Daily at 3 AM
BACKUP_RETENTION_DAYS = 7
BACKUP_DIRECTORY = "./backups"

# ==================== PERFORMANCE TUNING ====================
# Connection pooling
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20

# Concurrent operations
MAX_CONCURRENT_DOWNLOADS = 5
MAX_CONCURRENT_UPLOADS = 3

# Task timeout settings (seconds)
TASK_TIMEOUT_DOWNLOAD = 7200  # 2 hours
TASK_TIMEOUT_UPLOAD = 7200  # 2 hours

# ==================== SECURITY ENHANCEMENTS ====================
# API authentication (for GraphQL and REST)
ENABLE_API_AUTH = False
API_SECRET_KEY = ""  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# JWT token expiration (seconds)
JWT_EXPIRATION = 3600  # 1 hour

# IP whitelisting for API
API_WHITELIST_IPS = []  # Empty = allow all

# ==================== LOGGING ENHANCEMENTS ====================
# Structured JSON logging
ENABLE_JSON_LOGGING = False

# Log to file
LOG_TO_FILE = True
LOG_FILE_PATH = "logs/mltb.log"
LOG_FILE_MAX_SIZE_MB = 100
LOG_FILE_BACKUP_COUNT = 5

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = "INFO"

# ==================== FEATURE FLAGS ====================
# Toggle new features on/off without code changes
FEATURE_FLAGS = {
    "enhanced_dashboard": True,
    "graphql_api": False,  # Phase 3
    "plugin_system": False,  # Phase 3
    "ai_categorization": False,  # Phase 3
    "webhook_notifications": False,
}

# ==================== MONITORING ALERTS ====================
# Alert thresholds
ALERT_CPU_THRESHOLD = 90  # Percentage
ALERT_MEMORY_THRESHOLD = 90  # Percentage
ALERT_DISK_THRESHOLD = 90  # Percentage

# Alert notification chat (Telegram)
ALERT_NOTIFICATION_CHAT = ""  # Chat ID to receive alerts

# ==================== EXPERIMENTAL FEATURES ====================
# These are experimental and may change
EXPERIMENTAL_FEATURES = {
    "smart_retry": False,
    "multi_source_aggregation": False,
    "predictive_caching": False,
}
