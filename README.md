# Mirror Leech Telegram Bot

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Ready-brightgreen.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()

**A powerful Telegram bot for mirroring, leeching, and managing downloads with enterprise-grade reliability**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Production Setup](#-production-deployment)

</div>

---

## 📋 Overview

Mirror Leech Telegram Bot is a production-ready bot that enables efficient file downloading, uploading, and management through Telegram. Built with reliability and scalability in mind, it features advanced queue management, intelligent retry mechanisms, and comprehensive monitoring.

### ✨ Key Highlights

- **🚀 Category B Features** - Advanced reliability with circuit breakers, smart retry, and priority queues
- **📦 Docker Deployment** - Containerized for easy deployment and scaling
- **🔄 Auto-Healing** - Self-monitoring with automated health checks and recovery
- **📊 Monitoring** - Built-in metrics, logging, and alerting capabilities
- **🔒 Secure** - Production-grade security with authentication and rate limiting

---

## 🎯 Features

### Core Capabilities
- **Multi-Protocol Downloads** - HTTP, FTP, Torrent, Mega, Google Drive
- **Cloud Integration** - Upload to Google Drive, Telegram, and more
- **Format Support** - Videos, Archives, Documents with automatic extraction
- **Queue Management** - Priority-based task scheduling with VIP support
- **Progress Tracking** - Real-time download/upload progress with ETA

### Advanced Features (Category B)
- **Circuit Breakers** - Prevent cascading failures across services
- **Smart Retry Engine** - Exponential backoff with checkpoint recovery
- **Parallel Downloads** - Multi-chunk downloads for faster speeds
- **Health Monitoring** - Component-level health checks and diagnostics
- **Metrics & Analytics** - Prometheus-compatible metrics export

### Operations
- **Automated Backups** - Scheduled configuration and data backups
- **Auto-Cleanup** - Intelligent storage management
- **Log Rotation** - Automatic log management and archival
- **Cron Integration** - Scheduled maintenance tasks

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Telegram Bot Token ([Get one from @BotFather](https://t.me/botfather))
- MongoDB & Redis (included in Docker setup)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mirror-leech-telegram-bot.git
   cd mirror-leech-telegram-bot
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   nano .env
   ```

3. **Start with Docker**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   ./scripts/quick_check.sh
   ```

### First Run

1. Send `/start` to your bot on Telegram
2. Test with a small download: `/mirror https://speed.hetzner.de/10MB.bin`
3. Check queue status: `/qstatus` (admin only)

---

## 📚 Documentation

### User Guides
- **[Installation Guide](docs/guides/INSTALLATION.md)** - Detailed setup instructions
- **[Commands Reference](docs/guides/COMMANDS.md)** - All available bot commands
- **[Configuration Guide](docs/guides/CONFIGURATION.md)** - Configuration options explained
- **[Setup Complete Guide](docs/guides/SETUP_COMPLETE.md)** - Post-installation steps

### Operations
- **[Monitoring Guide](docs/operations/MONITORING.md)** - Health checks and monitoring tools
- **[Production Deployment](docs/operations/PRODUCTION_DEPLOYMENT_GUIDE.md)** - Enterprise deployment guide
- **[Configuration Tuning](docs/operations/CONFIGURATION_TUNING.md)** - Performance optimization
- **[Deployment Checklist](docs/operations/DEPLOYMENT_CHECKLIST.md)** - Pre-production checklist

### API & Development
- **[API Reference](docs/api/API_REFERENCE.md)** - API documentation
- **[Contributing Guide](CONTRIBUTING.md)** - Development and contribution guidelines

### Complete Index
See **[Documentation Index](docs/README.md)** for all available documentation.

---

## 🏭 Production Deployment

### Automated Setup

```bash
# Run production deployment script
./scripts/deploy/deploy_bot.sh

# Enable monitoring and backups
./scripts/setup_cron.sh

# Start auto-cleanup
./scripts/start_auto_cleanup.sh
```

### Manual Setup

1. **Deploy with Docker Compose**
   ```bash
   docker-compose -f docker-compose.secure.yml up -d
   ```

2. **Configure monitoring**
   ```bash
   # Run cron setup
   ./scripts/setup_cron.sh
   ```

3. **Enable alerts**
   ```bash
   ./scripts/start_alerts.sh <your_telegram_chat_id>
   ```

---

## 🔧 Management

### Health Monitoring

```bash
# Quick status check
./scripts/health/quick_check.sh

# Full health dashboard
./scripts/health/monitor_bot.sh

# Watch in real-time
./scripts/health/monitor_bot.sh watch

# View logs
./scripts/health/view_logs.sh 100
```

### Backup & Recovery

```bash
# Manual backup
./scripts/backup/backup_current_state.sh

# List backups
ls -lh data/backups/

# Restore from backup
./scripts/backup/backup_restore.sh
```

---

## 🏗️ Project Structure

```
mirror-leech-telegram-bot/
├── src/bot/                    # Bot core application
│   ├── core/                   # Core functionality
│   │   ├── category_b_integration.py
│   │   ├── circuit_breaker.py
│   │   ├── smart_retry.py
│   │   └── priority_queue.py
│   ├── modules/                # Command modules
│   └── helper/                 # Utility functions
├── config/                     # Configuration files
├── scripts/                    # Management scripts
├── docs/                       # Documentation
│   ├── guides/                 # User guides
│   ├── operations/             # Operational docs
│   ├── api/                    # API documentation
│   └── development/            # Development docs
├── data/                       # Runtime data
│   ├── downloads/              # Download storage
│   ├── logs/                   # Application logs
│   └── backups/                # Backup storage
└── deployment/                 # Deployment configs
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

---

## 📊 Status

- **Version:** 3.1.0
- **Status:** Production Ready ✅
- **Python:** 3.11.14
- **Category B:** Enabled
- **Last Updated:** 2026-02-28

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for the community**

Star ⭐ this repository if you find it helpful!

[Documentation](docs/) • [Issues](https://github.com/yourusername/mirror-leech-telegram-bot/issues) • [Discussions](https://github.com/yourusername/mirror-leech-telegram-bot/discussions)

</div>
