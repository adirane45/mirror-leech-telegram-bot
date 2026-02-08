# Mirror-Leech Telegram Bot

Production-ready Telegram bot for multi-protocol downloads, cloud sync, and automated workflows. Built for Docker-based deployment with monitoring, security hardening, and extensible modules.

## Highlights
- Multi-protocol downloads: HTTP/HTTPS, torrents, magnets, NZB, and cloud sources
- Cloud sync: Google Drive, Rclone remotes, and MyJDownloader
- Web dashboard + API endpoints
- Metrics and health monitoring
- Modular architecture with automation features

## Quick Start (Docker)
```bash
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

cp config/.env.security.example config/.env.production
nano config/.env.production

docker compose up -d
./scripts/quick_health_check.sh
```

## Configuration
Primary config is in config/main_config.py. Environment values live in config/.env.production.

Minimum required values:
- BOT_TOKEN
- OWNER_ID
- AUTHORIZED_CHATS

## Core Commands
Common commands (CMD_SUFFIX supported):
- /mirror - download to cloud
- /leech - download to Telegram
- /status - active downloads
- /queue - queued downloads
- /cancel - cancel a task
- /help - command help
- /quick - quick actions menu
- /search - torrent search
- /track - track a TV series
- /myshows - view tracked series
- /mobile - mobile layouts
- /assistant - smart download assistant

## Telegram Menu
Use TELEGRAM_MENU_COMMANDS.txt with @BotFather /setcommands to populate the slash menu.

## Web UI and Ports
Default ports (docker-compose.yml):
- 8060: Web dashboard
- 9090: Metrics
- 8090: qBittorrent (if enabled)
- 6800: Aria2 RPC

## Operations
- Health checks: scripts/quick_health_check.sh, scripts/health_check.sh
- Logs: docker compose logs -f app
- Backup: scripts/backup.sh, scripts/backup_restore.sh

## Documentation
Guides:
- docs/INSTALLATION.md
- docs/CONFIGURATION.md
- docs/DEPLOYMENT_CHECKLIST.md
- docs/API_REFERENCE.md
- docs/AUTOMATION_FEATURES.md
- docs/PHASE1_QUALITY_GATES.md
- docs/PHASE2_OBSERVABILITY.md
- docs/PHASE3_SECURITY_HARDENING.md

Reports:
- docs/reports/IMPLEMENTATION_SUMMARY.md
- docs/reports/DEPLOYMENT_SUMMARY.md
- docs/reports/MERGE_SUMMARY.md
- docs/reports/PERFORMANCE_VALIDATION_REPORT.md

Roadmap:
- docs/roadmap/REFACTORING_ROADMAP.md

Changes:
- docs/changes/COMMAND_REDESIGN_SUMMARY.md
- docs/changes/FEB9_COMMAND_FIX_SUMMARY.md
- docs/changes/FEB9_BUTTON_FIX.md

UX:
- docs/ux/ADVANCED_UX_FEATURES.md
- docs/ux/UX_ENHANCEMENT_FEATURES.md

## License
See docs/LICENSE.
