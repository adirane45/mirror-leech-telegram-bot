<div align="center">

# 🚀 Mirror-Leech Telegram Bot

### *Production-Ready Multi-Protocol Download Manager & Cloud Sync Bot*

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker)](https://www.docker.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4.svg?logo=telegram)](https://telegram.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](docs/LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()

**A powerful, enterprise-grade Telegram bot for automated downloads, cloud synchronization, and media management with advanced automation features and monitoring capabilities.**

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Documentation](#-documentation) • [Support](#-support)

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Commands](#-commands)
- [Architecture](#-architecture)
- [Web Dashboard](#-web-dashboard)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [Support](#-support)
- [Credits](#-credits)
- [License](#-license)

---

## 🌟 Overview

**Mirror-Leech Telegram Bot** is a comprehensive, production-ready solution for managing downloads and cloud storage operations through Telegram. Built with modularity, scalability, and reliability in mind, it supports multiple download protocols, intelligent client selection, auto-recovery mechanisms, and real-time monitoring.

Whether you're downloading torrents, direct links, NZB files, or syncing with cloud storage, this bot provides a seamless experience with advanced automation features, smart download assistance, and enterprise-level monitoring.

---

## ✨ Features

### 🔥 Core Features

- **🌐 Multi-Protocol Downloads**
  - HTTP/HTTPS direct links
  - Torrent files and magnet links
  - NZB files with SABnzbd integration
  - Google Drive, Mediafire, and other cloud sources
  - YouTube and 1000+ sites via yt-dlp

- **☁️ Cloud Synchronization**
  - Google Drive upload and management
  - Rclone support for 40+ cloud providers
  - MyJDownloader integration
  - Automatic folder organization

- **🤖 Intelligent Automation**
  - Smart client selection based on link type and load
  - Auto-recovery with health monitoring
  - Automatic retry mechanisms for failed downloads
  - Queue management with priority scheduling
  - RSS feed monitoring and auto-download

- **🎯 Advanced UX Features**
  - Quick Actions Menu - One-click common tasks
  - Smart Download Assistant - Context-aware suggestions
  - Command auto-suggestions and typo correction
  - Mobile-optimized layouts
  - Interactive file selector

### 📊 Management & Monitoring

- **Real-Time Status**
  - Live download progress tracking
  - Speed, ETA, and size monitoring
  - Multiple concurrent downloads
  - Queue status and history

- **Web Dashboard**
  - Modern web interface on port 8060
  - Real-time metrics and statistics
  - API endpoints for integrations
  - Prometheus metrics on port 9090

- **User Management**
  - Multi-user support with authorization
  - Individual user settings and preferences
  - Bandwidth throttling per user
  - Usage statistics and quotas

### 🔍 Search & Discovery

- **Torrent Search**
  - Multi-provider torrent search
  - Advanced filtering by quality, size, seeders
  - Direct download from search results
  - Custom search plugins support

- **NZB Search**
  - Integrated NZB search providers
  - Quality-based filtering
  - Direct SABnzbd integration

- **Google Drive Search**
  - Search your Google Drive
  - Count files and folders
  - Delete and manage files

### 🛠️ Advanced Features

- **Media Tools**
  - MediaInfo extraction
  - Archive extraction (zip, rar, 7z, tar)
  - Split and join files
  - Thumbnail generation

- **Download Managers**
  - Aria2c - Fast multi-connection downloader
  - qBittorrent - Advanced torrent client
  - SABnzbd - Usenet downloader
  - yt-dlp - Universal media downloader

- **Automation**
  - TV series tracking
  - Scheduled downloads
  - RSS feed automation
  - Webhook support

---

## 🛠️ Tech Stack

### Core Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Core language | 3.13+ |
| **Docker** | Containerization | 20.10+ |
| **kurigram** | Telegram bot framework | Latest |
| **FastAPI** | Web API framework | Latest |
| **Redis** | Caching & queue management | Latest |
| **MongoDB** | Database | Latest |

### Download Clients

- **Aria2** - Multi-protocol download engine
- **qBittorrent** - Feature-rich torrent client
- **SABnzbd** - Professional Usenet client
- **yt-dlp** - Universal media downloader

### Key Libraries

| Library | Purpose |
|---------|---------|
| **aiohttp** | Async HTTP client |
| **aiofiles** | Async file operations |
| **google-api-python-client** | Google Drive API |
| **feedparser** | RSS feed parsing |
| **celery** | Task queue |
| **prometheus-client** | Metrics collection |
| **gunicorn** | WSGI server |
| **uvicorn** | ASGI server |
| **apscheduler** | Job scheduling |
| **psutil** | System monitoring |

### Cloud & Storage

- **Google Drive API** - Cloud storage
- **Rclone** - Multi-cloud support
- **Telegraph** - Anonymous file sharing
- **MyJDownloader** - Remote download management

### Monitoring & Operations

- **Prometheus** - Metrics collection
- **Grafana** - Visualization (optional)
- **Docker Compose** - Service orchestration
- **Healthcheck scripts** - Service monitoring

---

## 🚀 Quick Start

Get started in 5 minutes with Docker:

```bash
# Clone the repository
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Copy and configure environment
cp config/.env.example config/.env.production
nano config/.env.production

# Start services
docker compose up -d

# Verify health
./scripts/quick_health_check.sh
```

**Required Environment Variables:**
- `BOT_TOKEN` - Get from [@BotFather](https://t.me/BotFather)
- `OWNER_ID` - Your Telegram user ID from [@userinfobot](https://t.me/userinfobot)
- `AUTHORIZED_CHATS` - Comma-separated chat IDs

---

## 📥 Installation

### Prerequisites

- **Operating System:** Linux (Ubuntu 20.04+, Debian 10+)
- **RAM:** 2GB minimum (4GB recommended)
- **Disk Space:** 10GB minimum (20GB+ for downloads)
- **Docker:** Version 20.10 or higher
- **Docker Compose:** Version 2.0 or higher

### Detailed Installation

#### 1. Install Docker

**Ubuntu/Debian:**
```bash
# Update packages
sudo apt-get update

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
```

#### 2. Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 3. Clone and Configure

```bash
# Clone repository
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Setup configuration
cp config/.env.example config/.env.production

# Edit configuration
nano config/.env.production
```

#### 4. Start Services

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f app

# Check status
docker compose ps
```

For detailed installation instructions, see [Installation Guide](docs/INSTALLATION.md).

---

## ⚙️ Configuration

### Essential Configuration

Edit `config/.env.production`:

```env
# Bot Configuration
BOT_TOKEN=your_bot_token_here
OWNER_ID=your_telegram_id
AUTHORIZED_CHATS=chat_id1,chat_id2

# Download Paths
DOWNLOAD_DIR=/app/downloads
UPLOAD_BASE_DIR=/app/uploads

# Cloud Storage (Optional)
GDRIVE_FOLDER_ID=your_folder_id
RCLONE_REMOTE=myremote
```

### Advanced Configuration

Edit `config/main_config.py` for advanced settings:

- Download limits and quotas
- Client preferences and priorities
- Automation and scheduling
- Notification preferences
- Security settings

For complete configuration guide, see [Configuration Guide](docs/CONFIGURATION.md).

---

## 📋 Commands

### Download Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/mirror` | Download to cloud storage | `/mirror <url>` |
| `/leech` | Download to Telegram | `/leech <torrent_file>` |
| `/clone` | Clone Google Drive files | `/clone <gdrive_link>` |
| `/ytdl` | Download from YouTube/other sites | `/ytdl <url>` |
| `/nzb` | Download NZB files | `/nzb <nzb_url>` |

### Management Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/status` | View active downloads | `/status` |
| `/queue` | View download queue | `/queue` |
| `/cancel` | Cancel a download | `/cancel <gid>` |
| `/pause` | Pause a download | `/pause <gid>` |
| `/resume` | Resume a download | `/resume <gid>` |

### Search Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/search` | Search torrents | `/search Breaking Bad` |
| `/nzbsearch` | Search NZB files | `/nzbsearch Linux ISO` |
| `/gdsearch` | Search Google Drive | `/gdsearch Movies` |

### Advanced Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/quick` | Quick actions menu | `/quick` |
| `/assistant` | Smart download assistant | `/assistant` |
| `/track` | Track TV series | `/track <series_name>` |
| `/myshows` | View tracked shows | `/myshows` |
| `/scheduler` | Schedule downloads | `/scheduler` |
| `/rss` | Manage RSS feeds | `/rss add <url>` |

### Utility Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show help menu | `/help` |
| `/stats` | View statistics | `/stats` |
| `/speedtest` | Test internet speed | `/speedtest` |
| `/settings` | User settings | `/settings` |
| `/mediainfo` | Get file info | `/mediainfo <file>` |

For complete command reference, see [Command Documentation](docs/API_REFERENCE.md).

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot Interface                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Bot Core Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Command    │  │   Queue      │  │   Client     │     │
│  │   Handler    │  │   Manager    │  │   Selector   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Download Clients Layer                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Aria2   │  │ qBitTor  │  │ SABnzbd  │  │  yt-dlp  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Cloud Storage Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Google Drive │  │    Rclone    │  │   Telegraph  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **Bot Core** - Command processing, user management, authorization
- **Download Engine** - Multi-client download orchestration
- **Queue Manager** - Task scheduling and prioritization
- **Client Selector** - Intelligent routing based on link type
- **Auto Recovery** - Health monitoring and automatic restart
- **Web Server** - Dashboard, API, and metrics endpoints
- **Storage Manager** - Cloud upload and file management

### Service Architecture

| Service | Port | Purpose |
|---------|------|---------|
| **Bot App** | - | Main bot application |
| **Web Dashboard** | 8060 | Web interface |
| **Prometheus** | 9090 | Metrics endpoint |
| **Redis** | 6379 | Cache & queue |
| **Aria2** | 6800 | RPC interface |
| **qBittorrent** | 8090 | WebUI |

---

## 🖥️ Web Dashboard

Access the web dashboard at `http://your-server:8060`

### Features

- **Real-time Monitoring** - Live download status and progress
- **Task Management** - Start, pause, cancel downloads
- **Statistics** - Usage stats and analytics
- **API Endpoints** - RESTful API for integrations
- **Metrics** - Prometheus metrics on port 9090

### API Endpoints

```
GET  /api/status          - Current downloads
GET  /api/queue           - Download queue
POST /api/download        - Start download
POST /api/cancel/:id      - Cancel download
GET  /api/stats           - Statistics
GET  /metrics             - Prometheus metrics
```

For API documentation, see [API Reference](docs/API_REFERENCE.md).

---

## 📚 Documentation

### User Guides

- **[Installation Guide](docs/INSTALLATION.md)** - Complete installation instructions
- **[Configuration Guide](docs/CONFIGURATION.md)** - Detailed configuration options
- **[Deployment Checklist](docs/DEPLOYMENT_CHECKLIST.md)** - Production deployment guide
- **[Automation Features](docs/AUTOMATION_FEATURES.md)** - Advanced automation capabilities

### Advanced Topics

- **[API Reference](docs/API_REFERENCE.md)** - API documentation
- **[Advanced UX Features](docs/ux/ADVANCED_UX_FEATURES.md)** - User experience enhancements
- **[Security Hardening](docs/PHASE3_SECURITY_HARDENING.md)** - Security best practices
- **[Observability](docs/PHASE2_OBSERVABILITY.md)** - Monitoring and logging

### Development

- **[Refactoring Roadmap](docs/roadmap/REFACTORING_ROADMAP.md)** - Future improvements
- **[Implementation Reports](docs/reports/)** - Technical implementation details

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

- 🐛 Report bugs and issues
- 💡 Suggest new features
- 📝 Improve documentation
- 🔧 Submit pull requests
- ⭐ Star the project

### Development Setup

```bash
# Clone repository
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linters
pre-commit run --all-files
```

### Code Standards

- Follow PEP 8 style guide
- Write comprehensive tests
- Document new features
- Use type hints
- Keep commits atomic

---

## 💬 Support

### Get Help

- **📖 Documentation** - Check our [docs](docs/) folder
- **🐛 Issues** - [GitHub Issues](https://github.com/adirane45/mirror-leech-telegram-bot/issues)
- **💡 Discussions** - [GitHub Discussions](https://github.com/adirane45/mirror-leech-telegram-bot/discussions)
- **📧 Email** - Contact repository owner

### Reporting Issues

When reporting issues, please include:

1. Bot version and deployment method
2. Steps to reproduce
3. Expected vs actual behavior
4. Relevant logs from `docker compose logs -f app`
5. Configuration (sanitized, no tokens)

### Community

- Star ⭐ the project to show support
- Share with others who might find it useful
- Contribute improvements back to the project

---

## 🌟 Credits

### Created By

**[adirane45](https://github.com/adirane45)**

### Acknowledgments

- **[anasty17](https://github.com/anasty17)** - Original MLTB base image
- **Telegram Bot API** - Bot framework
- **kurigram** - Python Telegram library
- **Aria2** - Download engine
- **qBittorrent** - Torrent client
- **yt-dlp** - Media downloader

### Built With

This project leverages amazing open-source technologies:

- Python ecosystem (asyncio, aiohttp, FastAPI)
- Docker and containerization
- Telegram Bot API
- Google APIs
- Prometheus monitoring
- And many more listed in [Tech Stack](#-tech-stack)

### Special Thanks

To all contributors and users who have helped improve this project through feedback, bug reports, and contributions.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](docs/LICENSE) file for details.

```
Copyright (c) 2024-2026 adirane45

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<div align="center">

### ⭐ Star this repository if you find it helpful!

**Made with ❤️ by [adirane45](https://github.com/adirane45)**

[⬆ Back to Top](#-mirror-leech-telegram-bot)

</div>
