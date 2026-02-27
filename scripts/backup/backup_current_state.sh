#!/bin/bash
# Backup Current Bot State
# Usage: ./scripts/backup_current_state.sh

BACKUP_DIR="/home/kali/mirror-leech-telegram-bot/data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="mltb_working_state_${TIMESTAMP}.tar.gz"

echo "📦 Creating backup of current working state..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Files to backup
echo "📋 Backing up configuration files..."
cd /home/kali/mirror-leech-telegram-bot

tar -czf "${BACKUP_DIR}/${BACKUP_NAME}" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='data/downloads/*' \
    --exclude='data/logs/*.txt' \
    --exclude='data/sessions/*.session' \
    src/bot/core/category_b_integration.py \
    src/bot/core/handlers.py \
    src/bot/__main__.py \
    config/ \
    scripts/*.sh \
    docker-compose*.yml \
    requirements*.txt \
    MONITORING.md \
    2>/dev/null

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}" | cut -f1)
    echo
    echo "✅ Backup created successfully!"
    echo "   📁 Location: ${BACKUP_DIR}/${BACKUP_NAME}"
    echo "   📊 Size: ${BACKUP_SIZE}"
    echo
    echo "💡 To restore:"
    echo "   tar -xzf ${BACKUP_DIR}/${BACKUP_NAME} -C /"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Keep only last 5 backups
echo "🧹 Cleaning old backups (keeping last 5)..."
cd "$BACKUP_DIR"
ls -t mltb_*.tar.gz | tail -n +6 | xargs -r rm -v

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Backup completed!"
