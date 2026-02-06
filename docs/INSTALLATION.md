# Installation Guide

Complete installation instructions for Enhanced MLTB v3.1.0

---

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Installation](#quick-installation)
- [Detailed Installation](#detailed-installation)
- [Post-Installation](#post-installation)
- [Verification](#verification)

---

## System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+, Debian 10+, or similar)
- **RAM**: 2GB (4GB recommended)
- **Disk Space**: 10GB (20GB+ for downloads)
- **CPU**: 2 cores (4+ recommended)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### Network Requirements
- Stable internet connection
- Open ports: 8060, 6379, 6800, 8090, 9091, 3000
- No firewall blocking Docker containers

### Prerequisites
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- Telegram User ID (get from [@userinfobot](https://t.me/userinfobot))
- Optional: Google Drive API credentials for cloud upload
- Optional: Rclone configuration for additional cloud storage

---

## Quick Installation

### 1. Install Docker

**Ubuntu/Debian:**
```bash
# Update package index
sudo apt-get update

# Install dependencies
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up stable repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Verify installation
docker --version
```

**Docker Compose:**
```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Apply executable permissions
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### 2. Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/mirror-leech-telegram-bot.git

# Navigate to directory
cd mirror-leech-telegram-bot

# Verify file structure
ls -la
```

### 3. Configure Environment

```bash
# Copy example configuration
cp config/.env.security.example config/.env.production

# Edit configuration
nano config/.env.production
```

**Minimum required settings:**
```bash
# Telegram Bot Token (REQUIRED)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Owner ID (REQUIRED)
OWNER_ID=123456789

# Authorized users/chats (Optional)
AUTHORIZED_CHATS=""

# Download directory
DOWNLOAD_DIR=/app/downloads

# Database URL (leave empty to disable MongoDB)
DATABASE_URL=
```

### 4. Start Services

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 5. Verify Installation

```bash
# Run health check
./scripts/quick_health_check.sh

# Expected output:
# ✅ Docker daemon responsive
# ✅ All containers running
# ✅ Redis accessible
# ✅ Web Dashboard accessible
# ✅ GraphQL API working
# Status: ✅ All critical systems operational
```

---

## Detailed Installation

### Step 1: System Preparation

#### Update System Packages
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

#### Install Required Packages
```bash
sudo apt-get install -y \
  git \
  curl \
  wget \
  net-tools \
  build-essential \
  python3 \
  python3-pip
```

#### Configure Firewall (Optional but Recommended)
```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow bot web interface
sudo ufw allow 8060/tcp

# Allow Grafana
sudo ufw allow 3000/tcp

# Enable firewall
sudo ufw enable
```

### Step 2: Docker Installation

#### Add Docker User Group
```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker

# Verify
docker run hello-world
```

#### Configure Docker Daemon
```bash
# Create daemon config
sudo mkdir -p /etc/docker

# Edit daemon.json
sudo nano /etc/docker/daemon.json
```

Add the following:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
```

Restart Docker:
```bash
sudo systemctl restart docker
sudo systemctl enable docker
```

### Step 3: Repository Setup

#### Clone with Specific Version
```bash
# Clone repository
git clone https://github.com/yourusername/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Checkout specific version (optional)
git checkout v3.1.0

# Verify workspace structure
tree -L 2 -I venv
```

#### Set Permissions
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Set proper ownership
sudo chown -R $USER:$USER .
```

### Step 4: Configuration

#### Main Configuration (`config/main_config.py`)

Edit the file:
```bash
nano config/main_config.py
```

Key settings:
```python
# Bot Identity
BOT_TOKEN = "your_bot_token_here"
OWNER_ID = 123456789
BOT_NAME = "MyMirrorBot"

# Authorization
AUTHORIZED_CHATS = "chat_id1 chat_id2"
SUDO_USERS = "user_id1 user_id2"

# Download Settings
DOWNLOAD_DIR = "/app/downloads"
MAX_SPLIT_SIZE = 2097152000  # 2GB
LEECH_SPLIT_SIZE = 2097152000

# Upload Settings
GDRIVE_FOLDER_ID = "your_folder_id"
INDEX_URL = "https://your-index-url.com"

# Phase Activation
ENABLE_PHASE_1 = True  # Redis + Prometheus
ENABLE_PHASE_2 = True  # Advanced Services
ENABLE_PHASE_3 = True  # GraphQL + Plugins

# Features
ENABLE_GRAPHQL_API = True
ENABLE_PLUGIN_SYSTEM = True
ENABLE_ADVANCED_DASHBOARD = True
```

#### Environment Configuration (`config/.env.production`)

```bash
nano config/.env.production
```

Complete settings:
```bash
# Telegram Configuration
BOT_TOKEN=your_bot_token_here
OWNER_ID=123456789

# Database (MongoDB - Optional)
DATABASE_URL=
MONGODB_URI=

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Aria2 Configuration
ARIA2_HOST=aria2
ARIA2_PORT=6800
ARIA2_SECRET=mltb_aria2_secret_2026

# qBittorrent Configuration
QB_HOST=qbittorrent
QB_PORT=8090
QB_USERNAME=admin
QB_PASSWORD=mltbmltb

# SABnzbd Configuration (Optional)
SABNZBD_HOST=localhost
SABNZBD_PORT=8080
SABNZBD_API_KEY=

# JDownloader Configuration (Optional)
JDOWNLOADER_EMAIL=your_email@example.com
JDOWNLOADER_PASSWORD=your_password
JDOWNLOADER_DEVICE_NAME=mltb_jd

# Google Drive (Optional)
GDRIVE_FOLDER_ID=
SERVICE_ACCOUNT_INDEX=0
IS_TEAM_DRIVE=False

# Rclone (Optional)
RCLONE_SERVE_URL=
RCLONE_SERVE_PORT=8080
RCLONE_SERVE_USER=
RCLONE_SERVE_PASS=

# Advanced Settings
MAX_CONCURRENT_DOWNLOADS=5
MAX_CONCURRENT_UPLOADS=5
BASE_URL_PORT=8060
```

#### Docker Compose Customization

If you need custom ports or resource limits:
```bash
nano docker-compose.yml
```

Example modifications:
```yaml
app:
  ports:
    - "8060:8060"  # Change first port for external access
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
  environment:
    - MAX_CONCURRENT_DOWNLOADS=10
```

### Step 5: Optional Services

#### Google Drive Setup

1. Create a Google Cloud Project
2. Enable Google Drive API
3. Create OAuth 2.0 credentials
4. Generate token.pickle

```bash
# Run token generator
docker exec -it mltb-app python3 /app/scripts/generate_drive_token.py
```

#### Rclone Setup

```bash
# Enter container
docker exec -it mltb-app bash

# Configure rclone
rclone config

# Test configuration
rclone lsd your-remote:
```

#### JDownloader Setup

JDownloader is automatically configured with the settings in `.env.production`. To verify:

1. Log in to [my.jdownloader.org](https://my.jdownloader.org)
2. Look for device: `mltb_jd` (or your custom name)
3. Accept the device if prompted

### Step 6: Build and Start

#### Build Docker Images
```bash
# Build from scratch
docker-compose build --no-cache

# Or pull pre-built images
docker-compose pull
```

#### Start Services
```bash
# Start in detached mode
docker-compose up -d

# Or start with logs
docker-compose up

# Start specific services
docker-compose up -d app redis aria2
```

#### Verify Services
```bash
# Check container status
docker-compose ps

# Expected output:
# NAME                STATUS              PORTS
# mltb-app           running (healthy)    0.0.0.0:8060->8060/tcp
# mltb-redis         running (healthy)    0.0.0.0:6379->6379/tcp
# mltb-aria2         running (healthy)    0.0.0.0:6800->6800/tcp
# mltb-qbittorrent   running (healthy)    0.0.0.0:8090->8090/tcp
# mltb-prometheus    running (healthy)    0.0.0.0:9091->9090/tcp
# mltb-grafana       running (healthy)    0.0.0.0:3000->3000/tcp
```

---

## Post-Installation

### 1. Initial Bot Configuration

Message your bot on Telegram:
```
/start
/help
/settings
```

### 2. Set Bot Commands

Use [@BotFather](https://t.me/BotFather):
```
/setcommands

mirror - Mirror a file/link to Google Drive
leech - Leech a file to Telegram
clone - Clone Google Drive files/folders
ytdl - Download from YouTube/supported sites
stats - Show bot statistics
help - Show help message
settings - Configure bot settings
```

### 3. Configure Grafana Dashboards

1. Access Grafana: http://localhost:3000
2. Login: admin / mltbadmin
3. Import dashboards from `integrations/monitoring/grafana/provisioning/dashboards/`

### 4. Test Download

Send to your bot:
```
/mirror https://example.com/test.zip
```

### 5. Set Up Automatic Backups

```bash
# Add to crontab
crontab -e

# Add line for daily backup at 2 AM
0 2 * * * cd /path/to/mirror-leech-telegram-bot && docker exec mltb-app python3 -c "from bot.core.backup_manager import backup_manager; import asyncio; asyncio.run(backup_manager.create_backup())"
```

---

## Verification

### Health Check Script

Run comprehensive diagnostics:
```bash
./scripts/health_check_comprehensive.sh
```

Expected results:
- ✅ All containers running and healthy
- ✅ All services accessible
- ✅ Configuration files present
- ✅ Phase 1/2/3 initialized
- ✅ Disk usage healthy
- ✅ Memory usage normal

### Manual Tests

#### Test Redis
```bash
docker exec mltb-redis redis-cli ping
# Expected: PONG
```

#### Test Aria2
```bash
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","id":"1","method":"aria2.getVersion","params":["token:mltb_aria2_secret_2026"]}' \
  http://localhost:6800/jsonrpc
# Expected: {"id":"1","jsonrpc":"2.0","result":{"version":"...",...}}
```

#### Test Web Dashboard
```bash
curl http://localhost:8060/
# Expected: HTML content
```

#### Test GraphQL API
```bash
curl -X POST -H "Content-Type: application/json" \
  --data '{"query":"{status{version}}"}' \
  http://localhost:8060/graphql
# Expected: {"data":{"status":{"version":"3.1.0"}}}
```

### Run Test Suite

```bash
docker exec mltb-app python3 -m pytest tests/ -v
```

Expected: 46+ tests passing

---

## Troubleshooting Installation

### Issue: Docker permission denied
```bash
# Solution: Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: Port already in use
```bash
# Find process using port 8060
sudo netstat -tlnp | grep 8060

# Kill process or change port in docker-compose.yml
```

### Issue: Container fails to start
```bash
# Check logs
docker-compose logs app

# Common fixes:
# 1. Verify .env.production has BOT_TOKEN
# 2. Check docker-compose.yml syntax
# 3. Ensure no conflicting containers: docker-compose down && docker-compose up -d
```

### Issue: Out of disk space
```bash
# Check disk usage
df -h

# Clean Docker resources
docker system prune -a --volumes
```

---

## Next Steps

- [Configuration Guide](CONFIGURATION.md) - Detailed configuration options
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [API Documentation](API.md) - API reference
- [Features Guide](FEATURES.md) - Complete feature list

---

**Installation complete! Your bot is ready to use.** 🎉
