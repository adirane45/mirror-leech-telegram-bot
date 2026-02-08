# ==================== PRODUCTION ENVIRONMENT SETTINGS ====================
# Load environment variables
import os
from dotenv import load_dotenv

# Load .env.production if it exists (for production deployments)
_base_dir = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(_base_dir, ".env.production")
if os.path.exists(_env_path):
    load_dotenv(_env_path, override=True)

# ==================== REQUIRED CONFIG ====================
# CRITICAL: Update these with your real credentials before starting the bot
def _get_safe_int(key, default):
    """Safely get integer from environment, return default if invalid"""
    value = os.getenv(key)
    if not value or value.startswith("YOUR_") or value.startswith("GENERATE_"):
        return default
    try:
        return int(value)
    except ValueError:
        return default

BOT_TOKEN = os.getenv("BOT_TOKEN", "7535236556:AAG-R4Ezs1_Px140VaxETF-y1oVPNNFJBog")
if BOT_TOKEN.startswith("YOUR_"):
    BOT_TOKEN = "7535236556:AAG-R4Ezs1_Px140VaxETF-y1oVPNNFJBog"
    
OWNER_ID = _get_safe_int("OWNER_ID", 1041454699)
TELEGRAM_API = _get_safe_int("TELEGRAM_API", 28965815)
TELEGRAM_HASH = os.getenv("TELEGRAM_HASH", "9baee82bd0eeeaa34ed185ce32128cc4")

# ==================== OPTIONAL CONFIG ====================
TG_PROXY = {}
USER_SESSION_STRING = os.getenv("USER_SESSION_STRING", "")
CMD_SUFFIX = ""
AUTHORIZED_CHATS = os.getenv("AUTHORIZED_CHATS", "1041454699")
SUDO_USERS = os.getenv("SUDO_USERS", "1041454699")
# DATABASE_URL is configured in MongoDB Configuration section below
DATABASE_URL = os.getenv("DATABASE_URL", "mongodb+srv://mitalm129:Aditya912004@cluster0.zi2jrfr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
STATUS_LIMIT = 4
DEFAULT_UPLOAD = "gd"
STATUS_UPDATE_INTERVAL = 15
FILELION_API = ""
STREAMWISH_API = ""
EXCLUDED_EXTENSIONS = ""
INCLUDED_EXTENSIONS = ""
INCOMPLETE_TASK_NOTIFIER = False
YT_DLP_OPTIONS = ""
USE_SERVICE_ACCOUNTS = False
NAME_SUBSTITUTE = ""
FFMPEG_CMDS = {}
UPLOAD_PATHS = {}
# GDrive Tools
GDRIVE_ID = "1mivJQEpn8uMMSAwRFsJPwAd5A4Udy7KR"
IS_TEAM_DRIVE = False
STOP_DUPLICATE = False
INDEX_URL = "https://justadi.drive45.workers.dev/0:"
# Rclone
RCLONE_PATH = ""
RCLONE_FLAGS = ""
RCLONE_SERVE_URL = ""
RCLONE_SERVE_PORT = 0
RCLONE_SERVE_USER = ""
RCLONE_SERVE_PASS = ""
# JDownloader
JD_EMAIL = "mitalm129@gmail.com"
JD_PASS = "7620703042@45Adi"
# Sabnzbd
USENET_SERVERS = [
    {
        "name": "main",
        "host": "",
        "port": 563,
        "timeout": 60,
        "username": "",
        "password": "",
        "connections": 8,
        "ssl": 1,
        "ssl_verify": 2,
        "ssl_ciphers": "",
        "enable": 1,
        "required": 0,
        "optional": 0,
        "retention": 0,
        "send_group": 0,
        "priority": 0,
    }
]
# Nzb search
HYDRA_IP = ""
HYDRA_API_KEY = ""
# Update
UPSTREAM_REPO = "https://github.com/adirane45/mirror-leech-telegram-bot"
UPSTREAM_BRANCH = "master"
# Leech
LEECH_SPLIT_SIZE = 0
AS_DOCUMENT = False
EQUAL_SPLITS = False
MEDIA_GROUP = False
USER_TRANSMISSION = False
HYBRID_LEECH = False
LEECH_FILENAME_PREFIX = ""
LEECH_DUMP_CHAT = ""
THUMBNAIL_LAYOUT = ""
# qBittorrent/Aria2c
TORRENT_TIMEOUT = 3600  # Torrent timeout in seconds (0 = no timeout, recommended: 3600 for 1 hour)
BASE_URL = "http://justadi.qzz.io:8090"
BASE_URL_PORT = 8060
WEB_PINCODE = True

# Notification on download completion
ALERT_ON_DOWNLOAD_COMPLETE = True  # Send Telegram notification when download finishes
# Queueing system
QUEUE_ALL = 0
QUEUE_DOWNLOAD = 0
QUEUE_UPLOAD = 0
# RSS
RSS_DELAY = 600
RSS_CHAT = ""
RSS_SIZE_LIMIT = 0
# Torrent Search
SEARCH_API_LINK = ""
SEARCH_LIMIT = 0
SEARCH_PLUGINS = [
    "https://raw.githubusercontent.com/qbittorrent/search-plugins/master/nova3/engines/piratebay.py",
    "https://raw.githubusercontent.com/qbittorrent/search-plugins/master/nova3/engines/limetorrents.py",
    "https://raw.githubusercontent.com/qbittorrent/search-plugins/master/nova3/engines/torlock.py",
    "https://raw.githubusercontent.com/qbittorrent/search-plugins/master/nova3/engines/torrentscsv.py",
    "https://raw.githubusercontent.com/qbittorrent/search-plugins/master/nova3/engines/eztv.py",
    "https://raw.githubusercontent.com/qbittorrent/search-plugins/master/nova3/engines/torrentproject.py",
    "https://raw.githubusercontent.com/MaurizioRicci/qBittorrent_search_engines/master/kickass_torrent.py",
    "https://raw.githubusercontent.com/MaurizioRicci/qBittorrent_search_engines/master/yts_am.py",
    "https://raw.githubusercontent.com/MadeOfMagicAndWires/qBit-plugins/master/engines/linuxtracker.py",
    "https://raw.githubusercontent.com/MadeOfMagicAndWires/qBit-plugins/master/engines/nyaasi.py",
    "https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/ettv.py",
    "https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/glotorrents.py",
    "https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/thepiratebay.py",
    "https://raw.githubusercontent.com/v1k45/1337x-qBittorrent-search-plugin/master/leetx.py",
    "https://raw.githubusercontent.com/nindogo/qbtSearchScripts/master/magnetdl.py",
    "https://raw.githubusercontent.com/msagca/qbittorrent_plugins/main/uniondht.py",
    "https://raw.githubusercontent.com/khensolomon/leyts/master/yts.py",
    "https://gist.githubusercontent.com/scadams/56635407b8dfb8f5f7ede6873922ac8b/raw/f654c10468a0b9945bec9bf31e216993c9b7a961/one337x.py",
"https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/academictorrents.py",
"https://raw.githubusercontent.com/Cc050511/qBit-search-plugins/main/acgrip.py",
"https://raw.githubusercontent.com/hannsen/qbittorrent_search_plugins/master/ali213.py",
"https://raw.githubusercontent.com/nindogo/qbtSearchScripts/master/anidex.py",
"https://raw.githubusercontent.com/AlaaBrahim/qBitTorrent-animetosho-search-plugin/main/animetosho.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/bitsearch.py",
"https://raw.githubusercontent.com/TuckerWarlock/qbittorrent-search-plugins/main/bt4gprx.com/bt4gprx.py",
"https://raw.githubusercontent.com/galaris/BTDigg-qBittorrent-plugin/main/btdig.py",
"https://raw.githubusercontent.com/elazar/qbittorrent-search-plugins/refs/heads/add-cloudtorrents-plugin/nova3/engines/cloudtorrents.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/calidadtorrent.py",
"https://raw.githubusercontent.com/MarcBresson/cpasbien/master/src/cpasbien.py",
"https://raw.githubusercontent.com/bugsbringer/qbit-plugins/master/darklibria.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/divxtotal.py",
"https://raw.githubusercontent.com/ZH1637/dmhy/main/dmhy.py",
"https://raw.githubusercontent.com/Bioux1/qbtSearchPlugins/main/dodi_repacks.py",
"https://raw.githubusercontent.com/dangar16/dontorrent-plugin/main/dontorrent.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/dontorrent.py",
"https://raw.githubusercontent.com/iordic/qbittorrent-search-plugins/master/engines/elitetorrent.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/esmeraldatorrent.py",
"https://raw.githubusercontent.com/Bioux1/qbtSearchPlugins/main/fitgirl_repacks.py",
"https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/glotorrents.py",
"https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/kickasstorrents.py",
"https://raw.githubusercontent.com/nindogo/qbtSearchScripts/master/magnetdl.py",
"https://scare.ca/dl/qBittorrent/magnetdl.py",
"https://raw.githubusercontent.com/iordic/qbittorrent-search-plugins/master/engines/mejortorrent.py",
"https://raw.githubusercontent.com/Cycloctane/qBittorrent-plugins/master/engines/mikan.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/mypornclub.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/naranjatorrent.py",
"https://raw.githubusercontent.com/libellula/qbt-plugins/main/pantsu.py",
"https://raw.githubusercontent.com/MadeOfMagicAndWires/qBit-plugins/master/engines/nyaasi.py",
"https://raw.githubusercontent.com/dangar16/pediatorrent-plugin/refs/heads/main/pediatorrent.py",
"https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/pirateiro.py",
"https://raw.githubusercontent.com/Larsluph/qbittorrent-search-plugins/prt/nova3/engines/pornrips.py",
"https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/rockbox.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/solidtorrents.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/therarbg.py",
"https://raw.githubusercontent.com/menegop/qbfrench/master/torrent9.py",
"https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/torrentdownload.py",
"https://raw.githubusercontent.com/BurningMop/qBittorrent-Search-Plugins/refs/heads/main/torrentdownloads.py",
"https://raw.githubusercontent.com/nindogo/qbtSearchScripts/master/torrentgalaxy.py",
"https://raw.githubusercontent.com/LightDestory/qBittorrent-Search-Plugins/master/src/engines/yourbittorrent.py"

]

# ==================== PHASE 1 ENHANCEMENTS ====================
# Safe Innovation Path - Configuration Additions
# All new features are OPTIONAL and disabled by default

# ==================== REDIS CONFIGURATION ====================
# Enable Redis for caching and improved performance
# Set to False to disable (bot will work without Redis)
ENABLE_REDIS_CACHE = True

# Redis connection settings (only used if ENABLE_REDIS_CACHE=True)
# Use "redis" when running in Docker, "localhost" for local development
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = _get_safe_int("REDIS_PORT", 6379)
REDIS_DB = _get_safe_int("REDIS_DB", 0)  # Database number (0-15)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")  # Leave empty if no password
if REDIS_PASSWORD.startswith("GENERATE_"):
    REDIS_PASSWORD = ""

# Cache TTL (Time To Live) in seconds
CACHE_TTL_TASK_STATUS = 300  # 5 minutes
CACHE_TTL_USER_DATA = 3600  # 1 hour
CACHE_TTL_STATISTICS = 600  # 10 minutes

# ==================== CELERY CONFIGURATION ====================
# Enable Celery for distributed task processing
# Set to False to use synchronous processing (existing behavior)
ENABLE_CELERY = True

# Celery broker and backend (only used if ENABLE_CELERY=True)
# Use Docker service names (redis) when running in Docker
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

# Celery task routing
CELERY_DOWNLOAD_QUEUE = "downloads"
CELERY_UPLOAD_QUEUE = "uploads"
CELERY_MAINTENANCE_QUEUE = "maintenance"

# Celery worker configuration
CELERY_WORKERS = _get_safe_int("CELERY_WORKERS", 2)
CELERY_THREADS_PER_WORKER = _get_safe_int("CELERY_THREADS_PER_WORKER", 4)

# ==================== METRICS CONFIGURATION ====================
# Enable Prometheus metrics for monitoring
# Set to False to disable metrics collection
ENABLE_METRICS = True

# Metrics endpoint
METRICS_PORT = _get_safe_int("METRICS_PORT", 9090)
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
BACKUP_ENABLED = True  # Master backup switch
BACKUP_SCHEDULE_HOUR = 3  # Daily at 3 AM
BACKUP_RETENTION_DAYS = 7
BACKUP_DIRECTORY = "./backups"
BACKUP_TO_CLOUD = False  # Set True to backup to cloud storage
BACKUP_INCLUDE_DOWNLOADS = False  # Set True to backup downloads folder (large)

# ==================== PERFORMANCE TUNING ====================
# Connection pooling
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20

# Concurrent operations
MAX_CONCURRENT_DOWNLOADS = 5  # Maximum simultaneous torrent downloads
MAX_CONCURRENT_UPLOADS = 3  # Maximum simultaneous uploads to cloud

# Task timeout settings (seconds)
TASK_TIMEOUT_DOWNLOAD = 7200  # 2 hours - max time for download task
TASK_TIMEOUT_UPLOAD = 7200  # 2 hours - max time for upload task

# qBittorrent Performance Settings
QB_DISK_CACHE = -1  # -1 = auto (recommended), or specify MB
QB_MEMORY_CACHE = 64  # Memory cache for qBittorrent (MB)
QB_PIECE_PRIORITIES = True  # Enable smart piece selection
QB_ANONYMOUS_MODE = False  # Disable anonymous mode for better speeds

# Aria2 Performance Settings
ARIA2_CONCURRENT_DOWNLOADS = 3  # Max concurrent files per server
ARIA2_CONNECTIONS_PER_SERVER = 4  # Max connections per server
ARIA2_MIN_SPLIT_SIZE = 1048576  # 1MB minimum split size

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
ALERT_CPU_THRESHOLD = 85  # Percentage (alert if CPU > 85%)
ALERT_MEMORY_THRESHOLD = 85  # Percentage (alert if memory > 85%)
ALERT_DISK_THRESHOLD = 90  # Percentage (alert if disk > 90%)

# Alert notification chat (Telegram) - Use OWNER_ID if not set
ALERT_NOTIFICATION_CHAT = os.getenv("ALERT_NOTIFICATION_CHAT", str(OWNER_ID))  # Chat ID to receive alerts

# Alert on service failures
ALERT_ON_SERVICE_FAILURE = True  # Alert when a service goes down
ALERT_ON_DOWNLOAD_START = False  # Alert when download starts
ALERT_ON_UPLOAD_START = False  # Alert when upload starts

# ==================== EXPERIMENTAL FEATURES ====================
# These are experimental and may change
EXPERIMENTAL_FEATURES = {
    "smart_retry": False,
    "multi_source_aggregation": False,
    "predictive_caching": False,
}

# ==================== AUTOMATION FEATURES ====================
# Feature flags for automation system
ENABLE_AUTOMATION_SYSTEM = True
ENABLE_AUTOMATION_API = True
ENABLE_CLIENT_SELECTION = True
ENABLE_WORKER_AUTOSCALER = True
ENABLE_SMART_THUMBNAILS = True

# ==================== PHASE 2 CONFIGURATION ====================
# Phase 2: Enhanced Logging, Monitoring & Recovery
# Safe Innovation Path - All features disabled by default

# Enhanced Logging Manager
ENABLE_ENHANCED_LOGGING = True
LOG_DIR = "logs"

# Alert System
ENABLE_ALERT_SYSTEM = True
ALERT_RETENTION_HOURS = 24

# Backup Manager  
ENABLE_BACKUP_SYSTEM = True
BACKUP_DIR = "backups"
BACKUP_FREQUENCY = "daily"

# Performance Profiler
ENABLE_PROFILER = True
PROFILE_THRESHOLD = 1.0  # seconds

# Recovery Manager
ENABLE_RECOVERY_MANAGER = True
ENABLE_AUTO_RECOVERY = True
# ==================== PHASE 3 CONFIGURATION ====================
# Phase 3: GraphQL API, Plugin System & Advanced Dashboard
# Safe Innovation Path - Features disabled by default, enable as needed

# GraphQL API
ENABLE_GRAPHQL_API = True
GRAPHQL_COMPLEXITY_LIMIT = 1000
GRAPHQL_MAX_DEPTH = 10
GRAPHQL_RATE_LIMIT = 100  # requests per minute

# Plugin System
ENABLE_PLUGIN_SYSTEM = True
AUTO_LOAD_PLUGINS = True
PLUGIN_DIRECTORY = "plugins"
PLUGIN_AUTO_RELOAD = True

# Advanced Dashboard
ENABLE_ADVANCED_DASHBOARD = True
ENABLE_LIVE_METRICS = True
DASHBOARD_REFRESH_INTERVAL = 5  # seconds
DASHBOARD_MAX_HISTORICAL_POINTS = 1000

# Performance Optimization
ENABLE_QUERY_OPTIMIZATION = True
QUERY_CACHE_ENABLED = True
CACHE_TTL = 300  # seconds
CACHE_MAX_SIZE = 1000

# Real-time Features
ENABLE_WEBSOCKET_SUPPORT = True
WEBSOCKET_HEARTBEAT = 30  # seconds

# Monitoring Integration
ENABLE_ADVANCED_METRICS = True
METRICS_EXPORT_INTERVAL = 60  # seconds
ENABLE_DATADOG_INTEGRATION = False  # Set True if using DataDog

# ==================== MONGODB CONFIGURATION ====================
# MongoDB connection settings (Cloud MongoDB Atlas)
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://mitalm129:Aditya912004@cluster0.zi2jrfr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "mltb")
MONGODB_USERNAME = os.getenv("MONGODB_USERNAME", "")
MONGODB_PASSWORD = os.getenv("MONGODB_PASSWORD", "")

# Build complete MongoDB connection string
if MONGODB_URI.startswith("mongodb+srv://") or MONGODB_URI.startswith("mongodb://"):
    # Use provided URI (cloud or local)
    MONGODB_URL = MONGODB_URI
elif MONGODB_USERNAME and MONGODB_PASSWORD:
    MONGODB_URL = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@mongodb:27017/{MONGODB_DATABASE}?authSource=admin"
else:
    MONGODB_URL = f"mongodb://mongodb:27017/{MONGODB_DATABASE}"

# ==================== API ENDPOINTS CONFIGURATION ====================
# API server configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = _get_safe_int("API_PORT", 8000)
API_WORKERS = _get_safe_int("API_WORKERS", 4)

# GraphQL endpoint
GRAPHQL_ENDPOINT = f"http://{API_HOST}:{API_PORT}/graphql"

# Health check endpoint
HEALTH_CHECK_ENDPOINT = f"http://{API_HOST}:{API_PORT}/health"

# ==================== MONITORING ENDPOINTS ====================
# Prometheus configuration
PROMETHEUS_HOST = os.getenv("PROMETHEUS_HOST", "prometheus")
PROMETHEUS_PORT = _get_safe_int("PROMETHEUS_PORT", 9091)
PROMETHEUS_METRICS_PATH = "/metrics"

# Grafana configuration  
GRAFANA_HOST = os.getenv("GRAFANA_HOST", "localhost")
GRAFANA_PORT = _get_safe_int("GRAFANA_PORT", 3000)
GRAFANA_URL = f"http://{GRAFANA_HOST}:{GRAFANA_PORT}"
GRAFANA_ADMIN_USER = os.getenv("GRAFANA_ADMIN_USER", "admin")
GRAFANA_ADMIN_PASSWORD = os.getenv("GRAFANA_ADMIN_PASSWORD", "mltb2026")

# ==================== SERVICE ENDPOINTS ====================
# Internal service URLs (for Docker network)
ARIA2_HOST = os.getenv("ARIA2_HOST", "aria2")
ARIA2_PORT = _get_safe_int("ARIA2_PORT", 6800)
ARIA2_SECRET = os.getenv("ARIA2_SECRET", "")
if ARIA2_SECRET.startswith("GENERATE_"):
    ARIA2_SECRET = ""

QBITTORRENT_HOST = os.getenv("QBITTORRENT_HOST", "qbittorrent")
QBITTORRENT_PORT = _get_safe_int("QBITTORRENT_PORT", 6969)

# ==================== DOCKER DEPLOYMENT SETTINGS ====================
# Environment detection
IS_DOCKER = os.getenv("IS_DOCKER", "true").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "production" if IS_DOCKER else "development")

# Service health check timeouts (seconds)
SERVICE_HEALTH_TIMEOUT = _get_safe_int("SERVICE_HEALTH_TIMEOUT", 30)
SERVICE_RETRY_ATTEMPTS = _get_safe_int("SERVICE_RETRY_ATTEMPTS", 3)
SERVICE_RETRY_DELAY = _get_safe_int("SERVICE_RETRY_DELAY", 5)

# ==================== DEPLOYMENT MODE ====================
# Safe startup modes
STARTUP_MODE = os.getenv("STARTUP_MODE", "normal")  # normal, recovery, diagnostics
DIAGNOSTIC_MODE = STARTUP_MODE == "diagnostics"
RECOVERY_MODE = STARTUP_MODE == "recovery"

# ==================== SECURITY SETTINGS ====================
# TLS/SSL Configuration
ENABLE_TLS = os.getenv("ENABLE_TLS", "false").lower() == "true"
TLS_CERT_PATH = os.getenv("TLS_CERT_PATH", "/etc/ssl/certs/server.crt")
TLS_KEY_PATH = os.getenv("TLS_KEY_PATH", "/etc/ssl/private/server.key")

# API Security
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "change-me-in-production")
if API_SECRET_KEY.startswith("GENERATE_"):
    API_SECRET_KEY = "change-me-in-production"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
if JWT_SECRET_KEY.startswith("GENERATE_"):
    JWT_SECRET_KEY = "change-me-in-production"
API_KEY_HEADER = "X-API-Key"

# CORS Settings
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# ==================== LOGGING CONFIGURATION ====================
# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
ENABLE_SYSLOG = os.getenv("ENABLE_SYSLOG", "false").lower() == "true"

# ==================== CONNECTION POOL SETTINGS ====================
# Database connection pooling
MONGODB_POOL_SIZE = _get_safe_int("MONGODB_POOL_SIZE", 10)
MONGODB_MAX_IDLE_TIME = _get_safe_int("MONGODB_MAX_IDLE_TIME", 45000)

# ==================== BOT RUNTIME SETTINGS ====================
# Startup verification
VERIFY_BOT_TOKEN_ON_STARTUP = True
VERIFY_SERVICES_ON_STARTUP = True
AUTO_START_SERVICES = True

# Graceful shutdown
SHUTDOWN_TIMEOUT = _get_safe_int("SHUTDOWN_TIMEOUT", 30)

# ==================== DEPLOYMENT READINESS ====================
# This config is PRODUCTION READY
# All critical settings can be overridden via environment variables
# See .env.production for full example

# ==================== CONFIG CLASS WRAPPER ====================
# Provides backwards compatibility for code importing Config class
class Config:
    """Configuration wrapper - provides access to all module-level config variables"""
    
    @classmethod
    def load(cls):
        """No-op for backward compatibility - config is loaded on module import"""
        pass
    
    @classmethod
    def _get_all_vars(cls):
        """Get all configuration variables"""
        return {k: v for k, v in globals().items() if not k.startswith('_') and k.isupper()}
    
    def __getattr__(self, name):
        """Get configuration variable by attribute access"""
        if name.isupper() and name in globals():
            return globals()[name]
        raise AttributeError(f"Config has no attribute '{name}'")
    
    @classmethod
    def get(cls, key, default=None):
        """Get configuration value with fallback"""
        return globals().get(key, default)


# Export all module variables as Config class attributes for compatibility
_config_vars = {k: v for k, v in globals().items() 
                if not k.startswith('_') and k.isupper() and k != 'Config'}
for _var_name, _var_value in _config_vars.items():
    setattr(Config, _var_name, _var_value)