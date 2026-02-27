#!/bin/bash
# Setup Cron Jobs for Bot Monitoring
# Usage: sudo ./scripts/setup_cron.sh

BOT_DIR="/home/kali/mirror-leech-telegram-bot"

echo "🔧 Setting up automated monitoring cron jobs..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script should be run with sudo for system-wide cron"
    echo "   Continuing with user crontab..."
    echo
fi

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null
echo "✅ Backed up existing crontab to /tmp/"

# Create new cron entries
CRON_ENTRIES="
# Bot Health Monitoring - Check every 15 minutes
*/15 * * * * ${BOT_DIR}/scripts/quick_check.sh >> /tmp/bot_health.log 2>&1

# Bot State Backup - Every 6 hours
0 */6 * * * ${BOT_DIR}/scripts/backup_current_state.sh >> /tmp/bot_backup.log 2>&1

# Cleanup Old Downloads - Daily at midnight
0 0 * * * find ${BOT_DIR}/data/downloads -type f -mtime +7 -delete 2>/dev/null

# Cleanup Old Logs - Weekly on Sunday at 2 AM
0 2 * * 0 find ${BOT_DIR}/data/logs -name '*.log' -mtime +30 -delete 2>/dev/null

# Cleanup Old Backups - Keep only last 10, check daily
0 3 * * * cd ${BOT_DIR}/data/backups && ls -t mltb_*.tar.gz | tail -n +11 | xargs -r rm 2>/dev/null
"

# Get existing crontab and append new entries
(crontab -l 2>/dev/null | grep -v "Bot Health Monitoring" | grep -v "Bot State Backup" | grep -v "Cleanup Old Downloads" | grep -v "Cleanup Old Logs" | grep -v "Cleanup Old Backups"; echo "$CRON_ENTRIES") | crontab -

echo
echo "✅ Cron jobs installed successfully!"
echo
echo "📋 Installed Jobs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
crontab -l | grep -A1 "Bot"
echo
echo "📝 Log Files:"
echo "   Health checks: /tmp/bot_health.log"
echo "   Backups: /tmp/bot_backup.log"
echo
echo "🔍 To view scheduled jobs: crontab -l"
echo "✏️  To edit jobs: crontab -e"
echo "🗑️  To remove all: crontab -r"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Automated monitoring setup complete!"
