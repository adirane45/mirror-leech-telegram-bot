# Configuration Guide

Complete configuration reference for Enhanced MLTB v3.1.0

---

## Table of Contents

- [Configuration Files](#configuration-files)
- [Bot Settings](#bot-settings)
- [Download Configuration](#download-configuration)
- [Upload Configuration](#upload-configuration)
- [Phase Configuration](#phase-configuration)
- [Service Configuration](#service-configuration)
- [Advanced Settings](#advanced-settings)

---

## Configuration Files

### Primary Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `main_config.py` | Main bot configuration | `config/main_config.py` |
| `.env.production` | Environment variables | `config/.env.production` |
| `docker-compose.yml` | Service orchestration | `docker-compose.yml` |
| `docker-compose.secure.yml` | Production hardened config | `docker-compose.secure.yml` |

### Configuration Priority

1. Environment variables (`.env.production`)
2. Main config file (`main_config.py`)
3. Default values in code

---

## Bot Settings

### Basic Bot Configuration

**Location:** `config/main_config.py`

```python
# Bot Identity
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # REQUIRED
OWNER_ID = 123456789  # REQUIRED - Your Telegram user ID
BOT_NAME = "MirrorBot"  # Optional - Display name

# Authorization
AUTHORIZED_CHATS = "chat_id1 chat_id2"  # Space-separated IDs
SUDO_USERS = "user_id1 user_id2"  # Users with admin privileges
USER_SESSION_STRING = ""  # Optional - User bot session

# Command Prefix
CMD_PREFIX = "/"  # Default command prefix
```

### Bot Behavior

```python
# Auto-delete messages after task completion
AUTO_DELETE_MESSAGE_DURATION = 60  # seconds (-1 to disable)

# Stop duplicate downloads
STOP_DUPLICATE = True
STOP_DUPLICATE_TASKS = ["mirror", "leech", "clone"]

# Extension filter
EXTENSION_FILTER = ["exe", "apk"]  # Block these extensions
INCOMPLETE_TASK_NOTIFIER = True  # Notify on incomplete tasks

# Upload/Download naming
AS_DOCUMENT = False  # Upload as document instead of media
EQUAL_SPLITS = True  # Split files equally
MEDIA_GROUP = True  # Group split files in Telegram
```

### Bot Limits

```python
# Task Limits
MAX_CONCURRENT_DOWNLOADS = 5
MAX_CONCURRENT_UPLOADS = 5
QUEUE_ALL = False  # Queue all tasks instead of parallel

# Size Limits  
TORRENT_LIMIT = 0  # GB (0 = unlimited)
DIRECT_LIMIT = 0  # GB
YTDLP_LIMIT = 0  # GB
GDRIVE_LIMIT = 0  # GB
CLONE_LIMIT = 0  # GB
LEECH_LIMIT = 0  # GB
MEGA_LIMIT = 0  # GB

# Timeout Settings
DOWNLOAD_TIMEOUT = 3600  # seconds (1 hour)
UPLOAD_TIMEOUT = 3600  # seconds
```

---

## Download Configuration

### Directory Settings

```python
# Download Directory
DOWNLOAD_DIR = "/app/downloads"

# Temporary directory for processing
TEMP_DIR = "/app/temp"

# Cache directory
CACHE_DIR = "/app/cache"
```

### Split Configuration

```python
# Split Size for Google Drive uploads
MAX_SPLIT_SIZE = 2097152000  # bytes (2GB)

# Split Size for Telegram uploads
LEECH_SPLIT_SIZE = 2097152000  # bytes (2GB)

# Enable equal splits
EQUAL_SPLITS = True
```

### Aria2 Configuration

**Location:** `config/.env.production`

```bash
# Aria2 Connection
ARIA2_HOST=aria2
ARIA2_PORT=6800
ARIA2_SECRET=mltb_aria2_secret_2026

# Aria2 Settings (in docker-compose.yml)
DISK_CACHE=64M
IPV6_MODE=false
UPDATE_TRACKERS=true
```

### qBittorrent Configuration

```bash
# qBittorrent Connection
QB_HOST=qbittorrent
QB_PORT=8090
QB_USERNAME=admin
QB_PASSWORD=mltbmltb
```

**Docker Compose Settings:**
```yaml
qbittorrent:
  environment:
    - WEBUI_PORT=8090
    - WEBUI_PASSWORD=mltbmltb
```

### SABnzbd Configuration

```bash
# SABnzbd Connection
SABNZBD_HOST=localhost
SABNZBD_PORT=8080
SABNZBD_API_KEY=your_api_key_here
```

### JDownloader Configuration

```bash
# JDownloader Cloud Integration
JDOWNLOADER_EMAIL=your_email@example.com
JDOWNLOADER_PASSWORD=your_secure_password
JDOWNLOADER_DEVICE_NAME=mltb_jd
```

**Note:** Device will auto-register with MyJDownloader cloud service.

---

## Upload Configuration

### Google Drive

```python
# Drive Configuration
GDRIVE_FOLDER_ID = "your_folder_id_here"
IS_TEAM_DRIVE = False  # Set True for Team/Shared Drives

# Service Accounts
USE_SERVICE_ACCOUNTS = False
SERVICE_ACCOUNT_INDEX = 0  # Which SA to start with

# Index Link
INDEX_URL = "https://your-index-url.com"  # Optional

# Drive Search
GDRIVE_SEARCH_API_KEY = ""  # For public drive search
GDRIVE_SEARCH_ENGINE_ID = ""
```

### Multiple Drive IDs

```python
# Support for multiple upload destinations
MULTI_DRIVE_LIST = {
    "main": "folder_id_1",
    "backup": "folder_id_2",
    "movies": "folder_id_3"
}
```

### Rclone Configuration

```python
# Rclone Upload
RCLONE_SERVE_URL = ""
RCLONE_SERVE_PORT = 8080
RCLONE_SERVE_USER = "username"
RCLONE_SERVE_PASS = "password"

# Rclone Path
RCLONE_PATH = ""  # e.g., "myremote:path/to/folder"
```

### Thumbnail Configuration

```python
# Thumbnail Settings
THUMBNAIL_URL = ""  # Default thumbnail URL
THUMBNAIL_SIZE = (320, 320)  # Pixels
```

---

## Phase Configuration

### Phase 1: Infrastructure

```python
# Enable Phase 1 (Redis + Prometheus)
ENABLE_PHASE_1 = True

# Redis Configuration
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = ""  # Empty for no auth

# Prometheus Configuration
PROMETHEUS_PORT = 9090
ENABLE_METRICS = True
METRICS_EXPORT_PORT = 9090
```

### Phase 2: Advanced Services

```python
# Enable Phase 2 Services
ENABLE_PHASE_2 = True

# Logger Manager
ENABLE_LOGGER_MANAGER = True
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_ROTATION_SIZE = 10485760  # bytes (10MB)
LOG_BACKUP_COUNT = 5

# Alert Manager
ENABLE_ALERT_MANAGER = True
ALERT_ON_ERROR = True
ALERT_ON_COMPLETE = False
ALERT_CHANNEL_ID = ""  # Telegram channel for alerts

# Backup Manager
ENABLE_BACKUP_MANAGER = True
BACKUP_INTERVAL = 86400  # seconds (24 hours)
BACKUP_RETENTION = 7  # days
BACKUP_DIRECTORY = "/app/data/backups"

# Profiler
ENABLE_PROFILER = True
PROFILE_SLOW_OPERATIONS = True
SLOW_OPERATION_THRESHOLD = 5  # seconds

# Recovery Manager
ENABLE_RECOVERY_MANAGER = True
AUTO_RECOVERY = True
RECOVERY_RETRY_COUNT = 3
```

### Phase 3: Advanced Features

```python
# Enable Phase 3 Features
ENABLE_PHASE_3 = True

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

# Query Optimization
ENABLE_QUERY_OPTIMIZATION = True
QUERY_CACHE_ENABLED = True
CACHE_TTL = 300  # seconds
```

---

## Service Configuration

### Database Configuration

```python
# MongoDB (Optional - disabled by default for faster startup)
DATABASE_URL = ""  # Empty to disable
MONGODB_URI = ""

# When enabled:
# DATABASE_URL = "mongodb://username:password@mongodb:27017/mltb"
# MONGO_DB = "mltb"
# MONGO_USERNAME = "admin"
# MONGO_PASSWORD = "password"
```

### Celery Configuration

```python
# Celery Task Queue
CELERY_BROKER_URL = "redis://redis:6379/0"
CELERY_RESULT_BACKEND = "redis://redis:6379/1"

# Worker Configuration
CELERY_WORKER_CONCURRENCY = 4  # Number of worker processes
CELERY_WORKER_MAX_TASKS = 20  # Tasks per worker before restart
CELERY_TIME_LIMIT = 3700  # seconds
CELERY_SOFT_TIME_LIMIT = 3600  # seconds
```

### Web Server Configuration

```python
# Web Server
BASE_URL = "http://localhost"
BASE_URL_PORT = 8060
WEB_WORKERS = 4  # Gunicorn workers

# CORS Configuration
CORS_ORIGINS = ["*"]  # Allowed origins
CORS_CREDENTIALS = True
```

---

## Advanced Settings

### Rate Limiting

```python
# Global Rate Limits
RATE_LIMIT_ENABLED = True
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 30  # per window

# Per-user Rate Limits
USER_RATE_LIMIT = 10  # commands per minute
```

### Cache Configuration

```python
# Redis Cache Settings
CACHE_ENABLED = True
CACHE_DEFAULT_TTL = 3600  # seconds (1 hour)
CACHE_MAX_SIZE = 1000  # Maximum cached items

# Cache per feature
CACHE_GDRIVE_RESULTS = True
CACHE_YTDL_INFO = True
CACHE_TORRENT_METADATA = True
```

### Security Settings

```python
# Security
ENABLE_SECURITY_CHECKS = True
ALLOWED_HOSTS = ["*"]  # Web server allowed hosts
SECRET_KEY = "your-secret-key-here"  # For session encryption

# Bot Security
BLOCK_FORWARDED_MESSAGES = False
BLOCK_EDITED_MESSAGES = False
ENABLE_FLOOD_PROTECTION = True
```

### Notification Settings

```python
# Status Updates
STATUS_UPDATE_INTERVAL = 10  # seconds
STATUS_LIMIT = 10  # Show in status command

# Progress Updates
UPDATE_PROGRESS_INTERVAL = 5  # seconds
SHOW_PROGRESS_BAR = True
```

### YouTube-DL Configuration

```python
# YT-DLP Settings
YTDLP_QUALITY = "best"
YTDLP_FORMAT = "bestvideo+bestaudio/best"

# Audio Downloads
AUDIO_FORMAT = "mp3"
AUDIO_QUALITY = "320"  # kbps

# Video Downloads
VIDEO_FORMAT = "mp4"
VIDEO_QUALITY = "1080"  # max height
```

### Custom Commands

```python
# Custom Command Aliases
CUSTOM_COMMANDS = {
    "/m": "/mirror",
    "/l": "/leech",
    "/c": "/clone",
    "/s": "/stats"
}
```

### Language Configuration

```python
# Bot Language
LANGUAGE = "en"  # English
TIMEZONE = "UTC"

# Date Format
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
```

---

## Docker Compose Configuration

### Resource Limits

Edit `docker-compose.yml`:

```yaml
app:
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '1.0'
        memory: 1G
```

### Port Mapping

```yaml
app:
  ports:
    - "8060:8060"  # Web interface
    - "9090:9090"  # Metrics

aria2:
  ports:
    - "6800:6800"  # RPC
    - "6888:6888"  # Listening port
```

### Volume Configuration

```yaml
app:
  volumes:
    - downloads:/app/downloads
    - ./bot:/app/bot:ro
    - ./config/main_config.py:/app/config.py:ro
    - ./config/.env.production:/app/.env.production:ro
    - logs:/app/logs
```

### Network Configuration

```yaml
networks:
  mltb-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

---

## Environment Variables Reference

### Complete `.env.production` Template

```bash
# ========== TELEGRAM CONFIGURATION ==========
BOT_TOKEN=your_bot_token_here
OWNER_ID=123456789
AUTHORIZED_CHATS=""
SUDO_USERS=""

# ========== DATABASE ==========
DATABASE_URL=
MONGODB_URI=

# ========== REDIS ==========
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ========== DOWNLOAD CLIENTS ==========
# Aria2
ARIA2_HOST=aria2
ARIA2_PORT=6800
ARIA2_SECRET=mltb_aria2_secret_2026

# qBittorrent
QB_HOST=qbittorrent
QB_PORT=8090
QB_USERNAME=admin
QB_PASSWORD=mltbmltb

# SABnzbd
SABNZBD_HOST=localhost
SABNZBD_PORT=8080
SABNZBD_API_KEY=

# JDownloader
JDOWNLOADER_EMAIL=
JDOWNLOADER_PASSWORD=
JDOWNLOADER_DEVICE_NAME=mltb_jd

# ========== GOOGLE DRIVE ==========
GDRIVE_FOLDER_ID=
IS_TEAM_DRIVE=False
USE_SERVICE_ACCOUNTS=False
SERVICE_ACCOUNT_INDEX=0
INDEX_URL=

# ========== RCLONE ==========
RCLONE_SERVE_URL=
RCLONE_SERVE_PORT=8080
RCLONE_SERVE_USER=
RCLONE_SERVE_PASS=
RCLONE_PATH=

# ========== BOT SETTINGS ==========
DOWNLOAD_DIR=/app/downloads
MAX_SPLIT_SIZE=2097152000
LEECH_SPLIT_SIZE=2097152000
MAX_CONCURRENT_DOWNLOADS=5
MAX_CONCURRENT_UPLOADS=5

# ========== PHASE ACTIVATION ==========
ENABLE_PHASE_1=True
ENABLE_PHASE_2=True
ENABLE_PHASE_3=True
ENABLE_GRAPHQL_API=True
ENABLE_PLUGIN_SYSTEM=True
ENABLE_ADVANCED_DASHBOARD=True

# ========== WEB SERVER ==========
BASE_URL_PORT=8060
WEB_WORKERS=4

# ========== CELERY ==========
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_WORKER_CONCURRENCY=4

# ========== ADVANCED ==========
LOG_LEVEL=INFO
AUTO_DELETE_MESSAGE_DURATION=60
STOP_DUPLICATE=True
EXTENSION_FILTER="exe apk"
```

---

## Configuration Examples

### High-Performance Configuration

For powerful servers (8+ cores, 16GB+ RAM):

```python
# Concurrent Operations
MAX_CONCURRENT_DOWNLOADS = 10
MAX_CONCURRENT_UPLOADS = 10
CELERY_WORKER_CONCURRENCY = 8

# Cache Settings
CACHE_ENABLED = True
CACHE_MAX_SIZE = 10000

# Aria2 Settings (docker-compose.yml)
DISK_CACHE=256M
```

### Low-Resource Configuration

For VPS (2 cores, 2GB RAM):

```python
# Concurrent Operations
MAX_CONCURRENT_DOWNLOADS = 2
MAX_CONCURRENT_UPLOADS = 2
CELERY_WORKER_CONCURRENCY = 2

# Disable Heavy Features
ENABLE_PROFILER = False
CACHE_ENABLED = False

# Aria2 Settings
DISK_CACHE=32M
```

### Security-Focused Configuration

For production with security emphasis:

```bash
# Use secure compose file
docker-compose -f docker-compose.secure.yml up -d
```

Additional settings:
```python
# Restrict Access
AUTHORIZED_CHATS = "chat_id1"  # Only specific chats
BLOCK_FORWARDED_MESSAGES = True
ENABLE_FLOOD_PROTECTION = True

# Secure Redis
REDIS_PASSWORD = "strong_password_here"

# Disable Public Access
CORS_ORIGINS = ["http://localhost:8060"]
```

---

## Validation & Testing

### Validate Configuration

```bash
# Test configuration syntax
python3 config/main_config.py

# Verify environment variables
docker-compose config
```

### Configuration Health Check

```bash
# Check if all required variables are set
./scripts/verify_config.py

# Test bot connectivity
docker exec mltb-app python3 -c "from bot.core.config_manager import Config; print(Config.BOT_TOKEN[:10] + '...')"
```

---

## Troubleshooting Configuration

### Common Issues

**Bot not responding:**
- Verify `BOT_TOKEN` is correct
- Check `OWNER_ID` matches your Telegram ID
- Ensure no typos in configuration

**Download failures:**
- Verify `ARIA2_SECRET` matches in both config and docker-compose
- Check `DOWNLOAD_DIR` has write permissions
- Ensure sufficient disk space

**Upload failures:**
- Verify `GDRIVE_FOLDER_ID` is accessible
- Check Google Drive API credentials
- Ensure `MAX_SPLIT_SIZE` is appropriate

**Memory issues:**
- Reduce `MAX_CONCURRENT_DOWNLOADS`
- Lower `CELERY_WORKER_CONCURRENCY`
- Disable `CACHE_ENABLED`

---

## Next Steps

- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [API Documentation](API.md) - API reference
- [Features Guide](FEATURES.md) - Feature documentation
- [Troubleshooting](TROUBLESHOOTING.md) - Problem solving

---

**Configuration complete! Proceed to deployment or feature exploration.** 🚀
