# 🚀 Mirror-Leech Telegram Bot v3.1.0 - Phase 2

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-brightgreen.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)](https://github.com/adirane45/mirror)

**Enhanced by: Aditya Rane** | **Version: 3.1.0 Phase 2** | **Date: February 5, 2026** | **Release: [v3.1.0-phase2](https://github.com/adirane45/mirror-leech-telegram-bot/releases/tag/v3.1.0-phase2)**  
**Contact:** adityrane45@gmail.com

[🔗 LinkedIn](https://www.linkedin.com/in/aditya-rane-a912004r/) • [📱 Instagram](https://www.instagram.com/rane_adi45) • [💬 Telegram](https://t.me/rane_adi45) • [📚 Documentation](#-complete-documentation) • [🚀 Getting Started](#-quick-start)

</div>

---

## ✨ What is This Bot?

A **powerful, production-grade Telegram bot** for managing downloads efficiently. Mirror files from the internet to Google Drive or leech them to Telegram with an advanced queue system, real-time monitoring, JSON-structured logging, and comprehensive web dashboard.

**Now with Phase 2 Enhancements:**
- 📊 **JSON-Structured Logging** - Machine-parsable logs for monitoring systems
- 🔔 **Alert System** - Real-time notifications with configurable delivery channels
- 💾 **Automatic Backups** - State snapshots with recovery capabilities
- ⚡ **Performance Profiling** - Request latency and function timing analysis
- 🔄 **Recovery Manager** - Automatic failover and state recovery

**Perfect for:**
- 🔄 Automating file transfers at scale
- ☁️ Backing up files to cloud storage with instant recovery
- 📊 Monitoring downloads with deep observability
- 🎯 Batch processing multiple files with reliability
- 📱 Remote file management via Telegram with confidence

---

## 🎯 Quick Features

<table>
<tr>
<td width="50%">

### ⬇️ Download & Upload
- Mirror from any source
- Leech to Telegram
- Multi-client support
- Queue management
- Priority control

</td>
<td width="50%">

### 🚀 Advanced Features
- Task scheduling
- Bandwidth limiting
- Archive management
- Web dashboard
- Auto-pause on load

</td>
</tr>
<tr>
<td width="50%">

### 🛠️ Tools & Operations
- Archive (ZIP, 7Z, RAR, TAR)
- Media info extraction
- Thumbnail generation
- Search & filter
- RSS automation

</td>
<td width="50%">

### 👨‍💼 Management
- User authorization
- Role-based access
- Download history
- Task categorization
- Settings panel

</td>
</tr>
<tr>
<td width="50%">

### 📊 Phase 2: Monitoring & Recovery
- JSON-structured logging
- Real-time alert system
- Automatic backups & recovery
- Performance profiling
- Health monitoring

</td>
<td width="50%">

### 🔍 Observability
- Machine-parsable logs
- Metrics collection (Prometheus)
- Event tracking
- System profiling
- State recovery

</td>


---

## 📦 Supported Sources

| Source | Mirror | Leech | Notes |
|--------|--------|-------|-------|
| **Direct Links** | ✅ | ✅ | HTTP, FTP, etc. |
| **Torrents** | ✅ | ✅ | Via qBittorrent |
| **Google Drive** | ✅ | ✅ | Native support |
| **YouTube** | ✅ | ✅ | YT-DLP integrated |
| **NZB Files** | ✅ | ✅ | Via SABnzbd |
| **JDownloader** | ✅ | ❌ | Premium sources |

---

## ⚡ 5-Minute Quick Start

### Prerequisites
- **Telegram Bot Token** (from [@BotFather](https://t.me/botfather))
- **Docker** (optional, for easiest setup)
- **Linux/Ubuntu** (recommended)

### Installation

**Option 1: Docker (Easiest)**
```bash
# Clone repository
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Setup config
cp config/.env.security.example config/.env.production
nano config/.env.production  # Add BOT_TOKEN, OWNER_ID, AUTHORIZED_CHATS

# Start
sudo docker compose -f deployment/docker-compose.yml up -d --build
```

**Option 2: Manual**
```bash
# Clone and setup
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot
python3 -m venv mltbenv
source mltbenv/bin/activate
pip install -r requirements.txt

# Configure
cp config/.env.security.example config/.env.production
nano config/.env.production

# Start services (in separate terminals)
aria2c --enable-rpc --rpc-listen-all=true --rpc-port=6800
qbittorrent-nox --webui-port=8090
python3 -m bot
```

### First Use
```
1. Search for your bot in Telegram
2. Send: /start
3. Send: /stats  (verify it's working)
4. Try: /mirror https://example.com/file.zip
```

**See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions!**

---

## 📚 Complete Documentation

### 📖 Core Documentation

| Document | Purpose | Type |
|----------|---------|------|
| [**INSTALLATION.md**](INSTALLATION.md) | 🚀 Setup & deployment | Required |
| [**CONFIGURATION.md**](CONFIGURATION.md) | ⚙️ Configuration guide | Required |
| [**API_REFERENCE.md**](API_REFERENCE.md) | 📚 API endpoints & classes | Reference |
| [**AUTOMATION_FEATURES.md**](AUTOMATION_FEATURES.md) | 🤖 Automation capabilities | Guide |
| [**DEPLOYMENT_CHECKLIST.md**](DEPLOYMENT_CHECKLIST.md) | ✅ Production deployment | Checklist |
| [**FEATURE_IMPLEMENTATION_ROADMAP.md**](FEATURE_IMPLEMENTATION_ROADMAP.md) | 🗺️ Future features (Phase 6-11) | Planning |
| [**RESTRUCTURING_NOTES.md**](RESTRUCTURING_NOTES.md) | 📁 Project organization | Reference |

### 📚 Archived Documentation

All completed phase documentation, implementation reports, and legacy guides are organized in the [**ARCHIVE/**](ARCHIVE/ARCHIVE_INDEX.md) folder.

**Quick access to archived materials:**
- [**ARCHIVE_INDEX.md**](ARCHIVE_INDEX.md) - Complete archive guide and index
- [**ARCHIVE/phases/**](ARCHIVE/phases/) - Phase 1-3 completion documentation
- [**ARCHIVE/reports/**](ARCHIVE/reports/) - Implementation reports and summaries
- [**ARCHIVE/TIER3_/**](ARCHIVE/) - Full Tier 3 (Phase 5) deployment documentation

📌 **See [ARCHIVE_INDEX.md](ARCHIVE_INDEX.md) for a complete list of archived materials and when to reference them.**

### 🎓 Learning Paths

**👶 Beginner** (1-2 hours)
1. Read [README.md](../README.md) in root
2. Follow [INSTALLATION.md](INSTALLATION.md)
3. Review [CONFIGURATION.md](CONFIGURATION.md)
4. Try basic commands from [API_REFERENCE.md](API_REFERENCE.md)

**👤 Intermediate** (3-4 hours)
1. Complete beginner path
2. Read [AUTOMATION_FEATURES.md](AUTOMATION_FEATURES.md)
3. Explore [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
4. Review [ARCHIVE/TIER3_TIER3_IMPLEMENTATION_PLAN.md](ARCHIVE/TIER3_TIER3_IMPLEMENTATION_PLAN.md) for architecture

**🧑‍💻 Advanced** (5+ hours)
1. Complete intermediate path
2. Review [FEATURE_IMPLEMENTATION_ROADMAP.md](FEATURE_IMPLEMENTATION_ROADMAP.md)
3. Check [ARCHIVE_INDEX.md](ARCHIVE_INDEX.md) for implementation patterns
4. Explore archived Tier documentation for best practices

---

## 🎮 Command Examples

### Download & Mirror
```
/mirror https://example.com/file.zip
→ Downloads file and uploads to Google Drive

/qmirror magnet:?xt=urn:btih:...
→ Downloads torrent via qBittorrent

/leech file_id
→ Downloads from Drive and sends to Telegram
```

### Queue Management
```
/queue                  View all active downloads
/pqueue abc123         Pause specific download
/rqueue abc123         Resume download
/prqueue abc123 1      Set high priority
/pauseall             Pause everything (owner only)
```

### File Operations
```
/zip /path/to/folder           Create archive
/unzip /path/to/archive.zip    Extract files
/mediainfo /path/to/video.mp4  Get media details
/thumbnail /path/to/video.mkv  Extract thumbnail
```

### System & Monitoring
```
/stats               System statistics
/speed              Internet speed test
/dashboard          Web-based dashboard
/history            Download history
/search video       Search downloads
```

**→ See [COMMANDS.md](COMMANDS.md) for the full command list with usage and shortcuts.**

---

## 🌐 Web Dashboard

Access a modern, real-time web interface:
```
http://your-server:8060/dashboard
```

**Features:**
- 📊 Real-time task monitoring
- 📈 System resource usage
- 🎮 Interactive task controls
- 📁 File explorer
- 📱 Mobile-responsive design

---

## 🏗️ Architecture

```
Mirror-Leech Telegram Bot
├── 📥 Download Clients
│   ├── Aria2 (direct links, torrents)
│   ├── qBittorrent (torrents)
│   ├── SABnzbd (NZB files)
│   └── JDownloader (premium sources)
├── ☁️ Cloud Integration
│   ├── Google Drive (mirror & leech)
│   ├── Telegram (upload/download)
│   └── rclone (multiple clouds)
├── 🎮 User Interface
│   ├── Telegram Bot (commands)
│   ├── Web Dashboard (real-time)
│   └── Inline Keyboards (interactive)
├── 💾 Storage
│   ├── MongoDB (optional)
│   └── Local Files
└── 🔧 Utilities
    ├── Archive Manager
    ├── Media Info
    ├── Task Scheduler
    └── Bandwidth Limiter
```

---

## 📋 System Requirements

### Minimum
- **OS:** Linux (Ubuntu 20.04+)
- **Python:** 3.8+
- **Memory:** 1GB RAM
- **Storage:** 5GB for downloads
- **Network:** Stable internet

### Recommended
- **OS:** Ubuntu 22.04 LTS
- **CPU:** 2+ cores
- **Memory:** 4GB RAM
- **Storage:** 50GB+ (SSD)
- **Bandwidth:** 100 Mbps+

---

## 🔧 Configuration

### Essential Settings (config.py)

```python
# Telegram
BOT_TOKEN = "your_token_here"
OWNER_ID = your_user_id
AUTHORIZED_CHATS = "user_id_1 user_id_2"

# Download
DOWNLOAD_DIR = "/downloads"
LEECH_DUMP_CHAT = "your_chat_id"

# Clients
ARIA_PORT = 6800
QB_PORT = 8090

# Optional
DATABASE_URL = "mongodb://localhost:27017"
BANDWIDTH_LIMIT = 0  # 0 = unlimited
TASK_LIMIT = 2      # max parallel downloads
```

**→ See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete configuration!**

---

## 🚀 Advanced Features

### ⏰ Task Scheduling
Schedule downloads at specific times with recurring options.
```
/schedule https://example.com/backup.zip
→ Choose time and frequency (daily, weekly, etc.)
```

### 📊 Bandwidth Control
Limit global or per-task bandwidth.
```
/limit 20M          Global limit to 20 MB/s
/limit_task gid 5M  Limit specific task to 5 MB/s
```

### 🏷️ Task Categorization
Organize downloads into categories.
```
/category           Create/manage categories
/categorize gid Movies    Assign to category
```

### 📌 Auto-Pause Feature
Bot automatically pauses when system load is high.
```
AUTO_PAUSE_CPU = 80      Pause at 80% CPU
AUTO_PAUSE_MEMORY = 85   Pause at 85% RAM
```

**→ See [ADVANCED_FEATURES_GUIDE.md](ADVANCED_FEATURES_GUIDE.md) for more!**

---

## 📊 What's New (v3.0.0)

✨ **Enhanced by: Aditya Rane** on January 30, 2026  
✉️ **Contact:** adityrane45@gmail.com

### New Features
- ✅ Task scheduling system
- ✅ Bandwidth limiting (global & per-task)
- ✅ Task categorization
- ✅ Web-based dashboard
- ✅ Archive management (ZIP, 7Z, RAR)
- ✅ Media information extraction
- ✅ Advanced search & filtering
- ✅ Interactive UI with inline keyboards

### Improvements
- ⚡ Better performance and stability
- 🎯 Improved queue management
- 📊 Real-time progress visualization
- 🎨 Modern UI/UX
- 📚 Comprehensive documentation

### Documentation
- ✅ 4,400+ lines of guides
- ✅ 100+ real examples
- ✅ Multiple learning paths
- ✅ Step-by-step tutorials
- ✅ Troubleshooting guides

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Make** your changes
4. **Test** thoroughly
5. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
6. **Push** to branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

**Please ensure:**
- ✅ Code follows project style
- ✅ No breaking changes
- ✅ Tests pass
- ✅ Documentation updated

---

## 📝 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) file for details.

**Original Author:** [anasty17](https://github.com/anasty17)  
**Enhanced by:** Aditya Rane (January 2026)  
**Email:** adityrane45@gmail.com

---

## 💬 Support

### Getting Help

1. **Documentation** - Read the guides linked above
2. **Issues** - Check [GitHub Issues](https://github.com/adirane45/mirror/issues)
3. **Discussions** - Use [GitHub Discussions](https://github.com/adirane45/mirror/discussions)
4. **Telegram Channel** - https://t.me/mltb_official_channel
5. **Telegram Group** - https://t.me/mltb_official_support

### Quick Troubleshooting

**Bot not responding?**
- Check `/ping` command
- View logs with `/log` (owner only)
- Check config.py settings

**Download failed?**
- Check available storage
- Verify download link
- Try `/cancel` and retry

**Performance issues?**
- Reduce `TASK_LIMIT` in config
- Enable `BANDWIDTH_LIMIT`
- Check available system resources

→ See [Troubleshooting](README_COMPLETE.md#-troubleshooting) section for more help!

---

## 🔐 Security Notes

⚠️ **Important:**
- Never share your `BOT_TOKEN`
- Keep `config.py` private
- Use strong passwords for services
- Limit `AUTHORIZED_CHATS` to trusted users
- Run on secure servers
- Keep dependencies updated

---

## 📊 Project Stats

- **Total Documentation:** 4,400+ lines
- **Total Commands:** 50+
- **Real Examples:** 100+
- **Download Clients:** 4 supported
- **Cloud Platforms:** 5+ supported
- **Lines of Code:** 10,000+

---

## 🎯 Roadmap

### Current (v3.0.0)
- ✅ Full documentation
- ✅ Advanced features
- ✅ Web dashboard
- ✅ Task scheduling

### Future Plans
- 📅 Enhanced API
- 📅 Mobile app
- 📅 More cloud integrations
- 📅 Machine learning features
- 📅 Advanced analytics

---

## 🙏 Credits & Acknowledgments

- **Original Creator:** [anasty17](https://github.com/anasty17)
- **Enhanced by:** Aditya Rane (January 2026)
- **Email:** adityrane45@gmail.com
- **Based on:** [python-aria-mirror-bot](https://github.com/lzzy12/python-aria-mirror-bot)
- **Technologies:** 
  - [Pyrogram](https://github.com/pyrogram/pyrogram) - Telegram client library
  - [FastAPI](https://fastapi.tiangolo.com/) - Web framework
  - [Aria2](https://github.com/aria2/aria2) - Download manager
  - [qBittorrent](https://www.qbittorrent.org/) - Torrent client
  - [SABnzbd](https://sabnzbd.org/) - NZB client

---

## 📞 Get Started Now!

<div align="center">

### 📖 [Read Complete Guide](README_COMPLETE.md)
### 🚀 [Follow Setup Instructions](SETUP_GUIDE.md)
### 💡 [Learn All Commands](USAGE_GUIDE.md)

---

**Made with ❤️ by Aditya Rane**  
**Version 3.0.0 | Production Ready ✅**

### 🔗 Connect With Me
- 📧 **Email:** adityrane45@gmail.com
- 💼 **LinkedIn:** [aditya-rane-a912004r](https://www.linkedin.com/in/aditya-rane-a912004r/)
- 📸 **Instagram:** [@rane_adi45](https://www.instagram.com/rane_adi45)
- 💬 **Telegram:** [@rane_adi45](https://t.me/rane_adi45)

[![GitHub Stars](https://img.shields.io/github/stars/adirane45/mirror-leech-telegram-bot.svg?style=social)](https://github.com/adirane45/mirror-leech-telegram-bot)
[![GitHub Forks](https://img.shields.io/github/forks/adirane45/mirror-leech-telegram-bot.svg?style=social)](https://github.com/adirane45/mirror-leech-telegram-bot/fork)

</div>

---

<details>
<summary>📌 Table of Quick Links</summary>

- 📚 **Documentation**
  - [README_COMPLETE.md](README_COMPLETE.md) - Full overview
  - [SETUP_GUIDE.md](SETUP_GUIDE.md) - Installation guide
  - [USAGE_GUIDE.md](USAGE_GUIDE.md) - Commands reference
  - [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick lookup
  - [ADVANCED_FEATURES_GUIDE.md](ADVANCED_FEATURES_GUIDE.md) - Advanced topics

- 🔗 **Important Links**
  - [GitHub Repository](https://github.com/adirane45/mirror-leech-telegram-bot)
  - [Official Channel](https://t.me/mltb_official_channel)
  - [Support Group](https://t.me/mltb_official_support)
  - [Report Issue](https://github.com/adirane45/mirror-leech-telegram-bot/issues)
  - [Discussions](https://github.com/adirane45/mirror-leech-telegram-bot/discussions)
  - [LinkedIn](https://www.linkedin.com/in/aditya-rane-a912004r/)
  - [Instagram](https://www.instagram.com/rane_adi45)
  - [Telegram](https://t.me/rane_adi45)

- 🛠️ **Tools & Resources**
  - [Get Bot Token](https://t.me/botfather)
  - [Get User ID](https://t.me/userinfobot)
  - [Docker Documentation](https://docs.docker.com/)
  - [Python Documentation](https://www.python.org/doc/)

</details>

---

**Ready to get started? Open [README_COMPLETE.md](README_COMPLETE.md) now!** 👉
