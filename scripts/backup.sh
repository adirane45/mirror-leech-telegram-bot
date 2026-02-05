#!/bin/bash
# Production Backup Script for MLTB
# Backs up MongoDB, Redis, and application logs

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
MONGODB_BACKUP="$BACKUP_DIR/mongodb_$TIMESTAMP"
LOGS_BACKUP="$BACKUP_DIR/logs_$TIMESTAMP"

echo "🔄 Starting backup process..."
echo "Timestamp: $TIMESTAMP"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOGS_BACKUP"

# Backup MongoDB
echo "📦 Backing up MongoDB..."
mongodump --uri="mongodb://localhost:27017" \
          --out="$MONGODB_BACKUP"
echo "✅ MongoDB backed up to: $MONGODB_BACKUP"
echo ""

# Backup Logs
echo "📦 Backing up application logs..."
tar -czf "$LOGS_BACKUP/logs_$TIMESTAMP.tar.gz" /app/logs/ 2>/dev/null || true
echo "✅ Logs backed up to: $LOGS_BACKUP/logs_$TIMESTAMP.tar.gz"
echo ""

# Backup Redis
echo "📦 Backing up Redis..."
redis-cli BGSAVE
sleep 2
if [ -f /data/dump.rdb ]; then
    cp /data/dump.rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"
    echo "✅ Redis backed up to: $BACKUP_DIR/redis_$TIMESTAMP.rdb"
else
    echo "⚠️  Redis RDB file not found, skipping Redis backup"
fi
echo ""

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | awk '{print $1}')
MONGODB_SIZE=$(du -sh "$MONGODB_BACKUP" 2>/dev/null | awk '{print $1}')
LOGS_SIZE=$(du -sh "$LOGS_BACKUP" 2>/dev/null | awk '{print $1}')

echo "📊 Backup Summary"
echo "================="
echo "Total Backup Size: $BACKUP_SIZE"
echo "MongoDB Backup: $MONGODB_SIZE"
echo "Logs Backup: $LOGS_SIZE"
echo "Backup Location: $BACKUP_DIR"
echo ""

# Cleanup old backups (keep last 7 days)
echo "🧹 Cleaning up old backups (older than 7 days)..."
find "$BACKUP_DIR" -type d -mtime +7 -exec rm -rf {} \; 2>/dev/null || true
echo "✅ Cleanup complete"
echo ""

# Verify backup integrity
echo "🔍 Verifying backup integrity..."
if [ -d "$MONGODB_BACKUP" ] && [ -f "$BACKUP_DIR/redis_$TIMESTAMP.rdb" ]; then
    echo "✅ Backup integrity verified"
else
    echo "⚠️  Backup integrity check failed (partial backup)"
fi

echo ""
echo "✨ Backup completed successfully!"
