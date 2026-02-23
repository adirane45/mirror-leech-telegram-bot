<div align="center">

# 🚀 Mirror-Leech Telegram Bot

> **Enterprise-Grade Download Manager & Cloud Sync Bot for Telegram**

[![Python](https://img.shields.io/badge/Python-3.13+-3776ab.svg?logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker)](https://www.docker.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4.svg?logo=telegram)](https://telegram.org/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](docs/LICENSE)

**[📚 Documentation](#documentation) • [⚙️ Setup](#installation) • [🎮 Commands](#commands--features) • [🧪 Testing](#testing--validation) • [📞 Support](#support)**

</div>

---

## 🎯 What Is This?

**Mirror-Leech Telegram Bot** is a powerful, production-grade Telegram bot for managing downloads, automating cloud synchronization, and streamlining media workflows at scale.

Download files from **HTTP, torrents, NZB, YouTube, Google Drive** and stream them to **Telegram, Google Drive, or any cloud storage**. Built with enterprise-grade automation, monitoring, and observability from the ground up.

### Perfect For:
- 🔄 **Automating downloads** at scale with queueing and priority management
- ☁️ **Cloud sync workflows** with Google Drive, rclone, and multi-provider support
- 📊 **Monitoring downloads** with real-time dashboards and deep observability
- 🎯 **Batch operations** with scheduling, retries, and auto-recovery
- 📱 **Remote management** via Telegram with instant notifications

---

## ✨ Core Features

| Category | Features |
|----------|----------|
| **📥 Downloads** | HTTP/HTTPS • Torrents • NZB • YouTube • Google Drive • Mediafire • 1000+ sites |
| **☁️ Uploads** | Google Drive • Telegram • Rclone (40+ providers) • MyJDownloader |
| **🤖 Automation** | Queueing • Scheduling • RSS feeds • Auto-retry • Health monitoring |
| **📊 Management** | Real-time status • Web dashboard • User permissions • Download history |
| **🔍 Tools** | Archive management • Media extraction • Thumbnail generation • Search |
| **🛠️ Clients** | Aria2c • qBittorrent • SABnzbd • yt-dlp |
| **📈 Enterprise** | Phase 6-11 advanced features (see [testing docs](TESTING.md)) |

---

## 🚀 Quick Start (3 Minutes)

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Configure
cp config/.env.production.example config/.env.production
nano config/.env.production
# Update: BOT_TOKEN, TELEGRAM_API, TELEGRAM_HASH, OWNER_ID

# Deploy
docker compose -f deployment/docker-compose.yml up -d --build

# Verify (wait 30 seconds)
sleep 30 && docker compose -f deployment/docker-compose.yml logs app --tail=20
```

### Option 2: Manual Setup

```bash
# Prerequisites: Python 3.13+, pip, aria2c, qbittorrent-nox

# Setup
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp config/.env.production.example config/.env.production
nano config/.env.production

# In separate terminals:
aria2c --enable-rpc --rpc-listen-all=true --rpc-port=6800
qbittorrent-nox --webui-port=8090
python3 -m bot
```

### Test It

Send `/ping` to your bot on Telegram → Should respond `Pong!`

---

## ⚙️ Installation

| Topic | Link |
|-------|------|
| **Detailed Setup** | [docs/INSTALLATION.md](docs/INSTALLATION.md) |
| **Configuration Reference** | [docs/CONFIGURATION.md](docs/CONFIGURATION.md) |
| **Docker Deployment** | [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) |
| **Troubleshooting** | [docs/PRODUCTION_DEPLOYMENT_GUIDE.md](docs/PRODUCTION_DEPLOYMENT_GUIDE.md) |

---

## 🎮 Commands & Features

### Start Here
```
/start              Launch the bot
/help               View help menu
/cmdlist            See all available commands (+ BotFather file)
/ping               Verify bot is working
```

### Download & Upload
```
/mirror <link>      Download and mirror to cloud
/leech <link>       Download and send to Telegram
/qmirror <magnet>   Torrent download via qBittorrent
/qbleech <magnet>   Torrent leech to Telegram
/clone <folder>     Copy Google Drive folders
/ytdl <url>         Download YouTube and 1000+ sites
```

### Queue & Status
```
/status             Show active downloads
/queue              List all tasks
/cancel <id>        Cancel a task
/pqueue <id>        Pause task
/rqueue <id>        Resume task
```

### Web Dashboard
Access portal: **http://localhost:8060**
- Real-time download progress
- System metrics
- User settings
- Download history

See complete command list: [docs/COMMANDS.md](docs/COMMANDS.md)

---

## 📚 Documentation

### Getting Started (30 min)
1. [Installation](docs/INSTALLATION.md) – Setup guide
2. [Configuration](docs/CONFIGURATION.md) – All settings explained
3. [Commands](docs/COMMANDS.md) – Full command reference
4. [Testing](TESTING.md) – Verify everything works ⭐

### Advanced (1-2 hours)
- [API Reference](docs/API_REFERENCE.md) – Integration details
- [Automation Features](docs/AUTOMATION_FEATURES.md) – Tasks, scheduling, RSS
- [Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md) – Production deployment
- [Roadmap](docs/FEATURE_IMPLEMENTATION_ROADMAP.md) – Phases 6-11 details

### Operations
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT_GUIDE.md) – Scale it up
- [Development Journey](docs/DEVELOPMENT_JOURNEY.md) – Architecture & timeline
- [Runbooks](docs/runbooks/README.md) – On-call, recovery, and service guides
- [Postmortem Template](docs/runbooks/postmortem_template.md) – Incident writeups

---

## 🧪 Testing & Validation

All features (Phase 1-11) are tested and documented. See **[TESTING.md](TESTING.md)** for:

✅ **How to verify features work:**
- Short checklist for quick validation
- Step-by-step commands with expected output
- Phase-by-phase testing guide

❌ **When something breaks:**
- How to capture logs and debug info
- Steps to report issues on GitHub
- How to fix common problems locally

→ **[Open TESTING.md →](TESTING.md)**

---

## 🌟 Advanced Features (Phase 6-11)

| Phase | Features | Status |
|-------|----------|--------|
| **6** | Stream links, web logs, circuit breaker, auto-update | ✅ Complete |
| **7** | Performance optimization, reliability, monitoring | ✅ Complete |
| **8** | Advanced intelligence, metadata, cross-seed | ✅ Complete |
| **9** | Enterprise features, quota bypass, CAPTCHA | ✅ Complete |
| **10** | Ecosystem integrations, debrid, link bypassing | ✅ Complete |
| **11** | Zero-copy transfers, batch operations, optimization | ✅ Complete |

Each phase is fully tested. Run tests:
```bash
python -m pytest tests/ -o addopts=""
```

See detailed Phase 6-11 validation in [TESTING.md](TESTING.md).

---

## 💡 Key Concepts

### Mirroring vs Leeching
- **Mirror**: Download to cloud (Google Drive, rclone)
- **Leech**: Download to Telegram (as media files)

### Download Clients
- **Aria2**: HTTP/FTP/torrent fast downloader
- **qBittorrent**: Advanced torrent management
- **SABnzbd**: Usenet (NZB) client
- **yt-dlp**: Video downloaders (YouTube, etc.)

### Automation
- **Scheduling**: Run commands at specific times (`/schedule`)
- **RSS Feeds**: Auto-download new episodes (`/rss`)
- **Queue**: Download multiple files with priority
- **Health Checks**: Auto-recovery on failures

---

## 🐳 Docker Compose Services

```yaml
Services running after deployment:
├─ app          Python bot (main)
├─ mongo        Database (MongoDB)
├─ redis        Cache & queue
├─ aria2c       Download engine
├─ qbittorrent  Torrent client
└─ web          Dashboard (FastAPI)

Ports:
├─ 8060    Web dashboard
├─ 8090    qBittorrent UI
├─ 6800    Aria2 RPC
└─ 27017   MongoDB
```

---

## 📋 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Ubuntu 20.04+ | Ubuntu 22.04+ |
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 2 GB | 8+ GB |
| **Disk** | 10 GB | 50+ GB |
| **Internet** | 10 Mbps | 50+ Mbps |
| **Docker** | 20.10+ | Latest |
| **Python** | 3.11+ | 3.13+ |

---

## 🔧 Environment Variables

### Required
```env
BOT_TOKEN=your_telegram_bot_token
TELEGRAM_API=your_api_id
TELEGRAM_HASH=your_api_hash
OWNER_ID=your_telegram_user_id
```

### Important
```env
AUTHORIZED_CHATS=-1001234567890           # Chat IDs (comma-separated)
SUDO_USERS=123456789,987654321            # Sudo user IDs
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
RCLONE_CONFIG_PATH=/path/to/rclone.conf
```

See all 50+ options: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

---

## 🆘 Support & Issues

### Getting Help
1. **Read docs**: Check [docs/](docs/) and [TESTING.md](TESTING.md)
2. **Check logs**: `tail -n 100 data/logs/log.txt`
3. **Search issues**: [GitHub Issues](https://github.com/adirane45/mirror-leech-telegram-bot/issues)
4. **Ask community**: Telegram group (link in issues)

### Reporting Problems
See [TESTING.md - Reporting Issues](TESTING.md#reporting-issues) for:
- How to capture error logs
- What info to include
- How to submit a GitHub issue

### Common Issues
| Problem | Solution |
|---------|----------|
| Bot not responding | Check `docker compose logs app` |
| Download errors | Verify client running (aria2c/qbittorrent) |
| Database issues | Delete `data/bak/` and restart |
| Dashboard not loading | Check port 8060 is open |

---

## 📦 Project Structure

```
mirror-leech-telegram-bot/
├─ bot/              Main bot code
│  ├─ core/          Core modules & functionality
│  ├─ modules/       Feature modules (commands)
│  └─ helper/        Utilities & helpers
├─ docs/             Documentation
├─ tests/            Test suite (pytest)
├─ config/           Configuration templates
├─ data/             Runtime data (logs, cache, downloads)
├─ deployment/       Docker & deployment files
├─ scripts/          Utility scripts
└─ README.md         This file
```

---

## 📝 License

MIT License - See [docs/LICENSE](docs/LICENSE) for details.

---

## 👤 Author

**Aditya Rane** ([@rane_adi45](https://instagram.com/rane_adi45))
- Enhanced and maintained this project
- Built Phase 6-11 enterprise features
- Date: February 22, 2026

---

## 🎓 Learning Resources

### For Users
1. Start with this README
2. Read [docs/INSTALLATION.md](docs/INSTALLATION.md)
3. Run `python -m pytest tests/ -o addopts=""` to verify setup
4. Try commands from [docs/COMMANDS.md](docs/COMMANDS.md)

### For Operators
1. [PRODUCTION_DEPLOYMENT_GUIDE.md](docs/PRODUCTION_DEPLOYMENT_GUIDE.md) – Scale to production
2. [DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md) – Pre-deployment tasks
3. [AUTOMATION_FEATURES.md](docs/AUTOMATION_FEATURES.md) – Advanced workflows

### For Developers
1. [DEVELOPMENT_JOURNEY.md](docs/DEVELOPMENT_JOURNEY.md) – Architecture & design
2. [FEATURE_IMPLEMENTATION_ROADMAP.md](docs/FEATURE_IMPLEMENTATION_ROADMAP.md) – Future features
3. [API_REFERENCE.md](docs/API_REFERENCE.md) – Code structures

---

<div align="center">

**⭐ If you find this project useful, please star it on GitHub!**

[View on GitHub](https://github.com/adirane45/mirror-leech-telegram-bot) • [Report Issues](https://github.com/adirane45/mirror-leech-telegram-bot/issues) • [Documentation](docs/)

Made with ❤️ for the community

</div>
