from importlib import import_module
from ast import literal_eval
from os import getenv

from bot import LOGGER


class Config:
    AS_DOCUMENT = False
    AUTHORIZED_CHATS = ""
    BASE_URL = ""
    BASE_URL_PORT = 80
    BOT_TOKEN = ""
    CMD_SUFFIX = ""
    DATABASE_URL = ""
    DATABASE_NAME = "mltb"
    DEFAULT_UPLOAD = "rc"
    EQUAL_SPLITS = False
    EXCLUDED_EXTENSIONS = ""
    INCLUDED_EXTENSIONS = ""
    FFMPEG_CMDS = {}
    FILELION_API = ""
    GDRIVE_ID = ""
    INCOMPLETE_TASK_NOTIFIER = False
    INDEX_URL = ""
    IS_TEAM_DRIVE = False
    JD_EMAIL = ""
    JD_PASS = ""
    LEECH_DUMP_CHAT = ""
    LEECH_FILENAME_PREFIX = ""
    LEECH_SPLIT_SIZE = 2097152000
    MEDIA_GROUP = False
    HYBRID_LEECH = False
    HYDRA_IP = ""
    HYDRA_API_KEY = ""
    NAME_SUBSTITUTE = r""
    OWNER_ID = 0
    QUEUE_ALL = 0
    QUEUE_DOWNLOAD = 0
    QUEUE_UPLOAD = 0
    RCLONE_FLAGS = ""
    RCLONE_PATH = ""
    RCLONE_SERVE_URL = ""
    RCLONE_SERVE_USER = ""
    RCLONE_SERVE_PASS = ""
    RCLONE_SERVE_PORT = 8080
    RSS_CHAT = ""
    RSS_DELAY = 600
    RSS_SIZE_LIMIT = 0
    SEARCH_API_LINK = ""
    SEARCH_LIMIT = 0
    SEARCH_PLUGINS = []
    STATUS_LIMIT = 4
    STATUS_UPDATE_INTERVAL = 15
    STOP_DUPLICATE = False
    STREAMWISH_API = ""
    SUDO_USERS = ""
    TELEGRAM_API = 0
    TELEGRAM_HASH = ""
    TG_PROXY = {}
    THUMBNAIL_LAYOUT = ""
    TORRENT_TIMEOUT = 0
    UPLOAD_PATHS = {}
    UPSTREAM_REPO = ""
    UPSTREAM_BRANCH = "master"
    USENET_SERVERS = []
    USER_SESSION_STRING = ""
    USER_TRANSMISSION = False
    USE_SERVICE_ACCOUNTS = False
    WEB_PINCODE = False
    YT_DLP_OPTIONS = {}
    
    # ==================== PHASE 1 ENHANCEMENTS ====================
    # Redis Configuration
    ENABLE_REDIS_CACHE = False
    REDIS_HOST = "redis"
    REDIS_PORT = 6379
    REDIS_DB = 0
    REDIS_PASSWORD = ""
    CACHE_TTL_TASK_STATUS = 300
    CACHE_TTL_USER_DATA = 3600
    CACHE_TTL_STATISTICS = 600
    
    # Celery Configuration
    ENABLE_CELERY = False
    CELERY_BROKER_URL = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND = "redis://redis:6379/1"
    CELERY_DOWNLOAD_QUEUE = "downloads"
    CELERY_UPLOAD_QUEUE = "uploads"
    CELERY_MAINTENANCE_QUEUE = "maintenance"
    
    # Metrics Configuration
    ENABLE_METRICS = False
    METRICS_PORT = 9090
    METRICS_PATH = "/metrics"
    METRICS_UPDATE_INTERVAL = 60
    
    # Rate Limiting
    ENABLE_RATE_LIMITING = False
    RATE_LIMIT_DOWNLOADS_PER_HOUR = 10
    RATE_LIMIT_DOWNLOADS_PER_DAY = 50
    RATE_LIMIT_UPLOADS_PER_HOUR = 10
    RATE_LIMIT_UPLOADS_PER_DAY = 50
    RATE_LIMIT_COMMANDS_PER_MINUTE = 5
    
    # Auto-Cleanup
    ENABLE_AUTO_CLEANUP = True
    AUTO_CLEANUP_MAX_AGE_HOURS = 24
    AUTO_CLEANUP_SCHEDULE_HOUR = 2
    
    # Notifications
    ENABLE_ENHANCED_NOTIFICATIONS = True
    NOTIFICATION_MILESTONES = [25, 50, 75]
    ENABLE_EMAIL_NOTIFICATIONS = False
    EMAIL_SMTP_SERVER = ""
    EMAIL_SMTP_PORT = 587
    EMAIL_USERNAME = ""
    EMAIL_PASSWORD = ""
    EMAIL_FROM_ADDRESS = ""
    EMAIL_TO_ADDRESSES = []
    
    # Backup
    ENABLE_AUTO_BACKUP = True
    BACKUP_SCHEDULE_HOUR = 3
    BACKUP_RETENTION_DAYS = 7
    BACKUP_DIRECTORY = "./backups"
    
    # Performance Tuning
    DB_POOL_SIZE = 10
    DB_MAX_OVERFLOW = 20
    MAX_CONCURRENT_DOWNLOADS = 5
    MAX_CONCURRENT_UPLOADS = 3
    TASK_TIMEOUT_DOWNLOAD = 7200
    TASK_TIMEOUT_UPLOAD = 7200
    
    # Security
    ENABLE_API_AUTH = False
    API_SECRET_KEY = ""
    JWT_EXPIRATION = 3600
    API_WHITELIST_IPS = []
    
    # Logging
    ENABLE_JSON_LOGGING = False
    LOG_TO_FILE = True
    LOG_FILE_PATH = "logs/mltb.log"
    LOG_FILE_MAX_SIZE_MB = 100
    LOG_FILE_BACKUP_COUNT = 5
    LOG_LEVEL = "INFO"

    # ==================== PHASE 2 CONFIGURATION ====================
    ENABLE_ENHANCED_LOGGING = False
    LOG_DIR = "logs"

    ENABLE_ALERT_SYSTEM = False
    ALERT_RETENTION_HOURS = 24

    ENABLE_BACKUP_SYSTEM = False
    BACKUP_DIR = "./backups"
    BACKUP_FREQUENCY = "daily"

    ENABLE_PROFILER = False
    PROFILE_THRESHOLD = 1.0

    ENABLE_RECOVERY_MANAGER = False
    ENABLE_AUTO_RECOVERY = False
    
    # Feature Flags
    FEATURE_FLAGS = {}
    ALERT_CPU_THRESHOLD = 90
    ALERT_MEMORY_THRESHOLD = 90
    ALERT_DISK_THRESHOLD = 90
    ALERT_NOTIFICATION_CHAT = ""
    
    # Experimental
    EXPERIMENTAL_FEATURES = {}

    @classmethod
    def _convert(cls, key: str, value):
        if not hasattr(cls, key):
            raise KeyError(f"{key} is not a valid configuration key.")

        expected_type = type(getattr(cls, key))

        if value is None:
            return None

        if isinstance(value, expected_type):
            return value

        if expected_type is bool:
            return str(value).strip().lower() in {"true", "1", "yes"}

        if expected_type in [list, dict]:
            if not isinstance(value, str):
                raise TypeError(
                    f"{key} should be {expected_type.__name__}, got {type(value).__name__}"
                )

            if not value:
                return expected_type()

            try:
                evaluated = literal_eval(value)
                if not isinstance(evaluated, expected_type):
                    raise TypeError(
                        f"Expected {expected_type.__name__}, got {type(evaluated).__name__}"
                    )
                return evaluated
            except (ValueError, SyntaxError, TypeError) as e:
                raise TypeError(
                    f"{key} should be {expected_type.__name__}, got invalid string: {value}"
                ) from e

        try:
            return expected_type(value)
        except (ValueError, TypeError) as exc:
            raise TypeError(
                f"Invalid type for {key}: expected {expected_type}, got {type(value)}"
            ) from exc

    @classmethod
    def get(cls, key: str):
        return getattr(cls, key, None)

    @classmethod
    def set(cls, key: str, value) -> None:
        if not hasattr(cls, key):
            raise KeyError(f"{key} is not a valid configuration key.")

        converted_value = cls._convert(key, value)
        setattr(cls, key, converted_value)

    @classmethod
    def get_all(cls):
        return {
            key: getattr(cls, key)
            for key in cls.__dict__.keys()
            if not key.startswith("__") and not callable(getattr(cls, key))
        }

    @classmethod
    def _is_valid_config_attr(cls, attr: str) -> bool:
        if attr.startswith("__") or callable(getattr(cls, attr, None)):
            return False
        return hasattr(cls, attr)

    @classmethod
    def _process_config_value(cls, attr: str, value):
        if not value:
            return None

        converted_value = cls._convert(attr, value)

        if isinstance(converted_value, str):
            converted_value = converted_value.strip()

        if attr == "DEFAULT_UPLOAD" and converted_value != "gd":
            return "rc"

        if attr in {
            "BASE_URL",
            "RCLONE_SERVE_URL",
            "SEARCH_API_LINK",
        }:
            return converted_value.strip("/") if converted_value else ""

        if attr == "USENET_SERVERS" and (
            not converted_value or not converted_value[0].get("host")
        ):
            return None

        return converted_value

    @classmethod
    def _load_from_module(cls) -> bool:
        try:
            settings = import_module("config")
        except ModuleNotFoundError:
            return False

        for attr in dir(settings):
            if not cls._is_valid_config_attr(attr):
                continue

            raw_value = getattr(settings, attr)
            processed_value = cls._process_config_value(attr, raw_value)

            if processed_value is not None:
                setattr(cls, attr, processed_value)

        return True

    @classmethod
    def _load_from_env(cls) -> None:
        for attr in dir(cls):
            if not cls._is_valid_config_attr(attr):
                continue

            env_value = getenv(attr)
            if env_value is None:
                continue

            processed_value = cls._process_config_value(attr, env_value)
            if processed_value is not None:
                setattr(cls, attr, processed_value)

    @classmethod
    def _validate_required_config(cls) -> None:
        required_keys = ["BOT_TOKEN", "OWNER_ID", "TELEGRAM_API", "TELEGRAM_HASH"]

        for key in required_keys:
            value = getattr(cls, key)
            if isinstance(value, str):
                value = value.strip()
            if not value:
                raise ValueError(f"{key} variable is missing!")

    @classmethod
    def load(cls) -> None:
        if not cls._load_from_module():
            LOGGER.info(
                "Config module not found, loading from environment variables..."
            )
            cls._load_from_env()

        cls._validate_required_config()

    @classmethod
    def load_dict(cls, config_dict) -> None:
        for key, value in config_dict.items():
            if not hasattr(cls, key):
                continue

            processed_value = cls._process_config_value(key, value)

            if key == "USENET_SERVERS" and processed_value is None:
                processed_value = []

            if processed_value is not None:
                setattr(cls, key, processed_value)

        cls._validate_required_config()
