# Management Scripts Guide

Quick reference for all available management scripts.

---

## 📋 Quick Commands

### Health & Monitoring
```bash
./scripts/quick_check.sh           # Quick bot status (30 sec)
./scripts/monitor_bot.sh           # Full health dashboard
./scripts/monitor_bot.sh watch     # Watch health in real-time
./scripts/view_logs.sh 100         # View last 100 log lines
```

### Deployment & Setup
```bash
./scripts/deploy_bot.sh            # Full production deployment
./scripts/dev_setup.sh             # Development environment setup
./scripts/pre_deployment_checklist.sh  # Pre-deployment verification
```

### Backups & Restore
```bash
./scripts/backup_current_state.sh  # Manual backup
./scripts/backup_restore.sh        # Restore from backup
ls -lh data/backups/               # List available backups
```

### Maintenance
```bash
./scripts/setup_cron.sh            # Setup automated monitoring
./scripts/start_auto_cleanup.sh    # Start cleanup service
./scripts/start_alerts.sh <chat_id> # Enable Telegram alerts
./scripts/optimize_performance.sh  # Performance tuning
```

### Security & Configuration
```bash
./scripts/security_hardening.sh    # Security hardening
./scripts/security_setup.py        # Security configuration
./scripts/verify_config.py         # Verify configuration
```

---

## 🗂️ Script Organization

### 🏥 Health & Monitoring (`health/`)
| Script | Purpose |
|--------|---------|
| `quick_check.sh` | Quick status check (30 sec) |
| `health_check.sh` | Basic health check |
| `health_check_comprehensive.sh` | Comprehensive health check |
| `monitor_bot.sh` | Full health dashboard |
| `view_logs.sh` | Smart log viewer |

### 🎯 Deployment (`deploy/`)
| Script | Purpose |
|--------|---------|
| `deploy.sh` | Initial deployment |
| `deploy_bot.sh` | Bot deployment |
| `pre_deployment_checklist.sh` | Pre-deployment checks |

### 💾 Backup & Restore
| Script | Purpose |
|--------|---------|
| `backup.sh` | Database backup |
| `backup_current_state.sh` | State backup |
| `backup_job.sh` | Scheduled backup job |
| `backup_restore.sh` | Restore from backup |

### ⚙️ Database & Security
| Script | Purpose |
|--------|---------|
| `create_db_indexes.sh` | Create MongoDB indexes |
| `db_security_setup.sh` | Database security setup |
| `mongodb-init.js` | MongoDB initialization |
| `security_hardening.sh` | System hardening |
| `security_setup.py` | Security configuration |

### 🔧 Configuration & Setup
| Script | Purpose |
|--------|---------|
| `dev_setup.sh` | Development setup |
| `setup_cron.sh` | Cron job setup |
| `setup_performance_baseline.sh` | Performance baseline |
| `verify_config.py` | Configuration validation |
| `production_hardening.py` | Production hardening |

### 🚀 Automation & Services
| Script | Purpose |
|--------|---------|
| `start_alerts.sh` | Start alert system |
| `start_auto_cleanup.sh` | Start cleanup service |
| `optimize_performance.sh` | Performance optimization |
| `update.py` | Update management |
| `secrets.sh` | Secret management |

### 🧪 Testing (`test_scripts/`)
| Script | Purpose |
|--------|---------|
| `start_testing.sh` | Start test suite |

---

## 🎓 Common Usage Patterns

### Daily Operations
```bash
# Check bot status
./scripts/quick_check.sh

# View recent logs
./scripts/view_logs.sh 50

# Full health dashboard
./scripts/monitor_bot.sh
```

### Weekly Maintenance
```bash
# Verify configuration
python scripts/verify_config.py

# Check backups
ls -lh data/backups/

# Review logs
./scripts/view_logs.sh 500
```

### Monthly Tasks
```bash
# Full health check
./scripts/health_check_comprehensive.sh

# Performance optimization
./scripts/optimize_performance.sh

# Security verification
./scripts/security_hardening.sh
```

### Emergency
```bash
# Backup current state
./scripts/backup_current_state.sh

# Read backup list
ls -lh data/backups/

# Restore from backup
./scripts/backup_restore.sh
```

---

## 📊 Output Examples

### Quick Check
```
Bot Status: ✅ Running
Container: Healthy
Uptime: 2h 45min
Circuit Breakers: All CLOSED
```

### Monitor Dashboard
```
=== BOT STATUS ===
Status: Running ✅
Uptime: 2:45:30

=== CIRCUIT BREAKERS ===
Telegram API: CLOSED (0/5 failures)
Google Drive: CLOSED (0/3 failures)
Aria2: CLOSED (0/5 failures)

=== RESOURCES ===
CPU: 15.2%
Memory: 428MB
```

---

## 🔧 Script Development

### Adding New Scripts

1. Create script in appropriate directory
2. Add to this README with description
3. Make executable: `chmod +x script.sh`
4. Document usage in script comments
5. Update todo/changelog

### Script Template

```bash
#!/bin/bash

# Script: script_name.sh
# Purpose: Description
# Usage: ./scripts/script_name.sh [options]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Main function
main() {
    echo "Script started..."
    # Implementation
}

main "$@"
```

---

## 📞 Support

- **Help:** `./scripts/script_name.sh --help`
- **Error logs:** `./scripts/view_logs.sh 100`
- **Bot status:** `./scripts/quick_check.sh`
- **Full dashboard:** `./scripts/monitor_bot.sh`

---

**Last Updated:** 2024-02-28
