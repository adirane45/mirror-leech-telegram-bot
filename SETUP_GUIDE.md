# Setup & Installation Guide

**Modified by: justadi**  
**Version: 3.0.0**  
**Date: January 30, 2026**

---

## 📑 Table of Contents

1. [Quick Setup (5 minutes)](#quick-setup)
2. [Detailed Setup (Docker)](#docker-setup)
3. [Detailed Setup (Manual)](#manual-setup)
4. [First Run Configuration](#first-run-configuration)
5. [Verification Checklist](#verification-checklist)
6. [Post-Installation Steps](#post-installation-steps)

---

## ⚡ Quick Setup (5 minutes)

### For Docker Users

```bash
# 1. Clone repository
git clone https://github.com/anasty17/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# 2. Create configuration
cp config_sample.py config.py

# 3. Edit essential settings
nano config.py
# Change: BOT_TOKEN, AUTHORIZED_CHATS, OWNER_ID

# 4. Start bot
sudo docker-compose up --build

# 5. Open Telegram and search for your bot
# Send /start to initialize
```

**That's it! 🎉**

---

## 🐳 Docker Setup (Recommended)

### Step 1: Prerequisites

**Install Docker:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify installation
docker --version
docker-compose --version
```

**Verify Installation:**
```
Docker version 20.10+
Docker Compose version 1.29+
```

### Step 2: Clone Repository

```bash
# Clone
git clone https://github.com/anasty17/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Verify structure
ls -la
# Should see: Dockerfile, docker-compose.yml, config_sample.py
```

### Step 3: Get Required Credentials

#### 3A. Get Telegram Bot Token

```
1. Open Telegram
2. Search: @BotFather
3. Send: /start
4. Send: /newbot
5. Follow prompts:
   - Bot name: "My Mirror Bot"
   - Username: "my_mirror_bot_123" (must be unique)
6. Copy the TOKEN (example: 123456:ABC-DEF...)
```

**Save this token!**

#### 3B. Get Your Telegram User ID

```
1. Search: @userinfobot
2. Send: /start
3. Copy your ID (example: 987654321)
```

#### 3C. Get Chat ID (for AUTHORIZED_CHATS)

Option 1: Create a group
```
1. Create new group
2. Add your bot
3. Send any message
4. Use /log to see chat ID in logs
```

Option 2: Use your user ID
```
Just use your user ID from step 3B
```

#### 3D. Get Google Drive Credentials (Optional)

```
1. Go to: https://console.cloud.google.com
2. Create new project: "Mirror Bot"
3. Enable Google Drive API
4. Create OAuth 2.0 credentials
   - Type: Desktop app
   - Download JSON file
5. Run: python3 generate_drive_token.py
   - Authorize with Google account
   - Save token
```

### Step 4: Configure the Bot

**Copy sample config:**
```bash
cp config_sample.py config.py
```

**Edit configuration:**
```bash
nano config.py
```

**Essential settings to change:**

```python
# ===== TELEGRAM =====
BOT_TOKEN = "123456:ABC-DEF1234ghIkl"  # From BotFather
OWNER_ID = 987654321  # Your user ID
AUTHORIZED_CHATS = "987654321"  # Your user ID or group ID

# ===== DOWNLOAD =====
DOWNLOAD_DIR = "/downloads"  # Where files go
LEECH_DUMP_CHAT = 987654321  # Where to upload leeched files

# ===== CLIENTS =====
ARIA_PORT = 6800  # Aria2 port
QB_PORT = 8090    # qBittorrent port

# ===== OPTIONAL =====
# Skip if not using:
# - USE_SERVICE_ACCOUNTS = False
# - DATABASE_URL = ""
# - UPTOBOX_TOKEN = ""
```

**Example full config:**
```python
BOT_TOKEN = "123456:ABCdef-GHIjkl"
OWNER_ID = 123456789
AUTHORIZED_CHATS = "123456789"
DOWNLOAD_DIR = "/downloads"
LEECH_DUMP_CHAT = 123456789
ARIA_PORT = 6800
QB_PORT = 8090
USE_SERVICE_ACCOUNTS = False
DATABASE_URL = ""
```

### Step 5: Start the Bot

**First run (builds image):**
```bash
# Build and start
sudo docker-compose up --build

# Output should show:
# Building mirror-leech-telegram-bot-app
# ...
# Application startup complete
```

**Subsequent runs:**
```bash
# Just start (image already built)
sudo docker-compose up
```

**Run in background:**
```bash
# Start in background
sudo docker-compose up -d

# View logs
sudo docker-compose logs -f

# Stop bot
sudo docker-compose down
```

### Step 6: Verify Bot is Running

**In Telegram:**
```
1. Search for your bot (username you set)
2. Send: /start
3. Should see: Welcome message

4. Send: /stats
5. Should see: System statistics
```

**In Terminal:**
```bash
# Check logs
sudo docker-compose logs

# Check containers
docker ps
# Should see: mirror-leech-telegram-bot-app running
```

---

## 🔧 Manual Setup (Without Docker)

### Step 1: System Requirements

**Check Python version:**
```bash
python3 --version
# Should be 3.8+
```

**Update system:**
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### Step 2: Install Dependencies

**Python packages:**
```bash
# Install pip
sudo apt-get install python3-pip -y

# Install venv
sudo apt-get install python3-venv -y
```

**System dependencies:**
```bash
sudo apt-get install -y \
    ffmpeg \
    aria2 \
    mediainfo \
    qbittorrent-nox \
    sabnzbd \
    python3-dev \
    build-essential
```

**Verify installation:**
```bash
ffmpeg -version      # Should show version
aria2c --version     # Should show version
mediainfo --version  # Should show version
```

### Step 3: Clone Repository

```bash
# Clone repository
git clone https://github.com/anasty17/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Verify contents
ls -la
```

### Step 4: Create Virtual Environment

```bash
# Create venv
python3 -m venv mltbenv

# Activate venv
source mltbenv/bin/activate

# You should see: (mltbenv) in terminal
```

### Step 5: Install Python Packages

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation (no errors)
python3 -c "import pyrogram; print('OK')"
```

### Step 6: Configure the Bot

**Copy config:**
```bash
cp config_sample.py config.py
```

**Edit config:**
```bash
nano config.py
```

**Minimum required settings:**
```python
BOT_TOKEN = "your_token_here"
OWNER_ID = your_user_id
AUTHORIZED_CHATS = "your_user_id"
DOWNLOAD_DIR = "/path/to/downloads"
```

### Step 7: Setup Download Clients

#### Aria2 Setup

**Start Aria2:**
```bash
# Terminal 1
aria2c --enable-rpc --rpc-listen-all=true --rpc-port=6800

# Or as service
sudo systemctl start aria2
```

#### qBittorrent Setup

**Start qBittorrent:**
```bash
# Terminal 2
qbittorrent-nox --webui-port=8090

# Or as service
sudo systemctl start qbittorrent-nox
```

**Configure:**
```
1. Access: http://localhost:8090
2. Default: admin / admin
3. Change password
4. Leave running
```

#### SABnzbd Setup (Optional)

```bash
# Terminal 3
sabnzbd

# Access: http://localhost:8080
```

### Step 8: Start the Bot

```bash
# Make sure venv is activated
source mltbenv/bin/activate

# Run bot
python3 -m bot

# Should show:
# Starting bot...
# Bot running...
```

**For background running:**
```bash
# Use nohup
nohup python3 -m bot > bot.log 2>&1 &

# View logs
tail -f bot.log

# Stop bot
pkill -f "python3 -m bot"
```

---

## 🔑 First Run Configuration

### Initialization Dialog

**When bot starts for first time:**

```
1. Choose download client (Aria2 / qBittorrent / both)
2. Set download directory
3. Configure optional features
4. Initialize database (if MongoDB enabled)
5. Start monitoring
```

### In Telegram

**First command:**
```
/start
```

**Response:**
```
👋 Welcome to Mirror-Leech Bot!
🎯 Version: 3.0.0
📚 Enhanced Features: 15+

Quick Start:
/help - Show all commands
/stats - Check system status
/mirror <link> - Download file
/leech <link> - Leech from Drive

Use /help for complete command list
```

### Essential First Steps

1. **Check Authorization:**
```
/stats

Should show:
✅ You are authorized
📊 System ready
```

2. **Test Download:**
```
/mirror https://www.w3.org/WAI/WCAG21/Techniques/pdf/G161.pdf
```

Should download and show progress.

3. **Check Queue:**
```
/queue

Should show:
📋 Active Downloads: 1
```

4. **View Settings:**
```
/settings
```

---

## ✅ Verification Checklist

### Pre-Start Checks

- [ ] Docker installed (if using Docker)
- [ ] Python 3.8+ installed (if manual)
- [ ] Bot token obtained from @BotFather
- [ ] User ID obtained from @userinfobot
- [ ] Download directory exists and writable
- [ ] config.py created and configured
- [ ] All required services installed

### Post-Start Checks

```bash
# 1. Check bot process
ps aux | grep bot
# Should see: python3 -m bot (or docker container)

# 2. Check download clients
curl http://localhost:6800/jsonrpc
# Should return: 200 OK (Aria2)

curl http://localhost:8090/api/v2/app/webapiVersion
# Should return: API version (qBittorrent)

# 3. Test bot in Telegram
/start          # Should respond
/stats          # Should show system info
/help           # Should show commands
```

### Functionality Tests

```
Test 1: Direct Download
/mirror https://example.com/file.zip
→ Should download and show progress

Test 2: Queue Check
/queue
→ Should show active downloads

Test 3: History
/history
→ Should show recent downloads

Test 4: Web Dashboard (if enabled)
http://localhost:8050/dashboard
→ Should show real-time stats
```

---

## 📋 Post-Installation Steps

### Step 1: Optimize Configuration

**Based on system:**
```python
# High-end server (4GB+ RAM)
TASK_LIMIT = 5
BANDWIDTH_LIMIT = 0  # Unlimited

# Medium server (2GB RAM)
TASK_LIMIT = 3
BANDWIDTH_LIMIT = 50M  # 50 MB/s limit

# Low-end server (1GB RAM)
TASK_LIMIT = 1
BANDWIDTH_LIMIT = 10M  # 10 MB/s limit
```

### Step 2: Setup Auto-Start

**For Docker:**
```bash
# Auto-restart on reboot
sudo docker-compose up -d --restart always
```

**For Manual:**
```bash
# Create systemd service
sudo nano /etc/systemd/system/mltb.service
```

**Content:**
```ini
[Unit]
Description=Mirror Leech Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/mirror-leech-telegram-bot
ExecStart=/home/ubuntu/mirror-leech-telegram-bot/mltbenv/bin/python3 -m bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable mltb
sudo systemctl start mltb

# Check status
sudo systemctl status mltb
```

### Step 3: Setup Monitoring

**Monitor bot with:**
```bash
# View real-time logs
docker-compose logs -f

# Or for manual
tail -f bot.log

# Monitor system resources
top
# or
htop  # If installed
```

### Step 4: Backup Configuration

**Backup important files:**
```bash
# Copy config and credentials
cp config.py config.py.backup
cp *.json *.json.backup

# Store safely
```

### Step 5: Security Setup

**Change default passwords:**
```python
# qBittorrent
# Go to http://localhost:8090
# Settings → Change admin password

# SABnzbd (if used)
# Go to http://localhost:8080
# Settings → Security
```

**Secure Telegram credentials:**
```bash
# Never share:
# - BOT_TOKEN
# - OWNER_ID
# - Service account JSON files

# Use environment variables (advanced)
export BOT_TOKEN="your_token"
```

### Step 6: Set Up Monitoring

**Monitor resource usage:**
```
/stats  # In Telegram

Shows:
- CPU usage
- Memory usage
- Disk space
- Active downloads
```

**Enable alerts:**
```python
# In config.py
AUTO_PAUSE_CPU = 80      # Pause at 80% CPU
AUTO_PAUSE_MEMORY = 85   # Pause at 85% RAM

# Bot will automatically pause downloads
# when resources exceed thresholds
```

---

## 🚀 Next Steps After Setup

### 1. Read Documentation
- [ ] README_COMPLETE.md (Overview)
- [ ] This file (Setup)
- [ ] USAGE_GUIDE.md (How to use)
- [ ] ADVANCED_FEATURES_GUIDE.md (Advanced)

### 2. Configure Preferences
```
/settings  # User settings
/bsetting  # Bot settings (owner)
```

### 3. Add Download Sources
```
# Google Drive (optional)
python3 generate_drive_token.py

# Uptobox API (optional)
# Get token from uptobox.com
```

### 4. Setup Categories
```
/category

Create:
- Movies
- TV Shows
- Documents
- etc.
```

### 5. Schedule Tasks
```
/schedule https://example.com/backup.zip

Set time and recurrence
```

### 6. Monitor and Maintain
```
# Regular checks
/stats      # System status
/queue      # Active downloads
/log        # View logs (owner)
```

---

## 🔍 Troubleshooting Setup

### Docker won't start
```bash
# Check Docker service
sudo systemctl status docker

# View error logs
sudo docker-compose logs

# Rebuild
sudo docker-compose up --build
```

### Port already in use
```bash
# Find process using port 6800 (Aria2)
sudo lsof -i :6800

# Kill process
sudo kill -9 <PID>

# Or change port in config.py
```

### Bot doesn't respond
```
1. Check bot token: /log
2. Verify AUTHORIZED_CHATS includes your ID
3. Restart bot: sudo docker-compose restart
```

### Download clients not connecting
```bash
# Test Aria2
curl http://localhost:6800/jsonrpc

# Test qBittorrent
curl http://localhost:8090/api/v2/app/webapiVersion

# Restart services if needed
```

### Low performance
```python
# Reduce parallel tasks
TASK_LIMIT = 1

# Enable bandwidth limit
BANDWIDTH_LIMIT = 20M

# Restart bot
```

---

## ✨ Congratulations!

Your Mirror-Leech Telegram Bot is now ready to use! 🎉

**Next:** Read [USAGE_GUIDE.md](USAGE_GUIDE.md) to learn all commands and features.

---

**Modified by:** justadi  
**Date:** January 30, 2026  
**Version:** 3.0.0  
**Status:** ✅ Complete
