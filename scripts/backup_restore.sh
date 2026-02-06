#!/bin/bash
# Automated Backup & Recovery System
# Phase 3 Disaster Recovery - Production Grade
# Date: February 6, 2026

set -e

BACKUP_DIR="./backups"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="mltb_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

echo "============================================"
echo "MLTB Automated Backup & Recovery System"
echo "============================================"
echo ""

# Function: Create backup
create_backup() {
    log_info "Starting backup: ${BACKUP_NAME}"
    mkdir -p "${BACKUP_PATH}"
    
    # 1. Backup configuration files
    log_info "Backing up configuration files..."
    mkdir -p "${BACKUP_PATH}/config"
    cp config.py "${BACKUP_PATH}/config/" 2>/dev/null || log_warn "config.py not found"
    cp .env.production "${BACKUP_PATH}/config/" 2>/dev/null || log_warn ".env.production not found"
    cp docker-compose.yml "${BACKUP_PATH}/config/" 2>/dev/null || log_warn "docker-compose.yml not found"
    
    # 2. Backup critical application files
    log_info "Backing up critical application files..."
    mkdir -p "${BACKUP_PATH}/app"
    cp -r bot/core/*.py "${BACKUP_PATH}/app/" 2>/dev/null || log_warn "bot/core not fully backed up"
    
    # 3. Backup database - MongoDB
    log_info "Backing up MongoDB database..."
    mkdir -p "${BACKUP_PATH}/mongodb"
    docker exec mltb-mongodb mongodump --out /tmp/mongodump 2>/dev/null && \
      docker exec mltb-mongodb tar czf /tmp/mongodump.tar.gz -C /tmp mongodump && \
      docker cp mltb-mongodb:/tmp/mongodump.tar.gz "${BACKUP_PATH}/mongodb/" && \
      log_info "MongoDB backup completed" || log_warn "MongoDB backup failed"
    
    # 4. Backup Redis database
    log_info "Backing up Redis database..."
    mkdir -p "${BACKUP_PATH}/redis"
    docker exec mltb-redis redis-cli BGSAVE 2>/dev/null || true
    sleep 2
    docker cp mltb-redis:/data/dump.rdb "${BACKUP_PATH}/redis/" 2>/dev/null || log_warn "Redis backup failed"
    
    # 5. Backup logs
    log_info "Backing up logs..."
    mkdir -p "${BACKUP_PATH}/logs"
    cp -r logs/* "${BACKUP_PATH}/logs/" 2>/dev/null || log_warn "No logs to backup"
    
    # 6. Create backup metadata
    cat > "${BACKUP_PATH}/BACKUP_MANIFEST.txt" << EOF
MLTB Backup Information
=======================
Backup Name: ${BACKUP_NAME}
Backup Date: $(date)
Backup Size: $(du -sh ${BACKUP_PATH} | cut -f1)
System Version: Phase 3
Includes:
  - Configuration files
  - Application core files
  - MongoDB database dump
  - Redis database snapshot
  - Application logs
  
Recovery Instructions:
1. Ensure MLTB services are stopped: docker compose down
2. Extract backup: tar xzf ${BACKUP_NAME}.tar.gz
3. Restore configuration: cp backup/config/* to root directory
4. Restore MongoDB: mongorestore --drop < backup/mongodb/mongodump.tar.gz
5. Restore Redis: docker cp backup/redis/dump.rdb mltb-redis:/data/
6. Restart services: docker compose up -d
7. Verify: ./scripts/health_check.sh
EOF

    # 7. Compress backup
    log_info "Compressing backup..."
    cd "${BACKUP_DIR}"
    tar czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}/"
    rm -rf "${BACKUP_NAME}"
    log_info "Backup completed: ${BACKUP_NAME}.tar.gz"
    
    # 8. List backup
    ls -lh "${BACKUP_NAME}.tar.gz"
}

# Function: Cleanup old backups
cleanup_old_backups() {
    log_info "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."
    find "${BACKUP_DIR}" -name "mltb_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
    log_info "Cleanup completed. Current backups:"
    ls -lh "${BACKUP_DIR}"/*.tar.gz 2>/dev/null || log_warn "No backups found"
}

# Function: Verify backup integrity
verify_backup() {
    local backup_file="$1"
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi
    
    log_info "Verifying backup integrity: ${backup_file}"
    if tar tzf "${backup_file}" > /dev/null; then
        log_info "✅ Backup integrity verified"
        return 0
    else
        log_error "❌ Backup integrity check failed"
        return 1
    fi
}

# Function: List all backups
list_backups() {
    log_info "Available backups:"
    echo ""
    ls -lh "${BACKUP_DIR}"/*.tar.gz 2>/dev/null | awk '{print $9 " (" $5 ")"}'
    echo ""
}

# Function: Restore from backup
restore_backup() {
    local backup_file="$1"
    
    if [ -z "${backup_file}" ]; then
        log_error "Usage: restore_backup backup_filename"
        return 1
    fi
    
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi
    
    log_info "⚠️  WARNING: This will restore your system from backup"
    log_info "Backup file: ${backup_file}"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warn "Restore cancelled"
        return 1
    fi
    
    log_info "Stopping MLTB services..."
    docker compose down || true
    
    log_info "Extracting backup..."
    tar xzf "${backup_file}"
    
    log_warn "Backup restored. Please verify before restarting services."
    log_info "To restart: docker compose up -d"
}

# Main execution
case "${1:-create}" in
    create)
        create_backup
        cleanup_old_backups
        ;;
    cleanup)
        cleanup_old_backups
        ;;
    verify)
        if [ -z "${2}" ]; then
            # Verify latest backup
            latest=$(ls -t "${BACKUP_DIR}"/*.tar.gz 2>/dev/null | head -1)
            verify_backup "${latest}"
        else
            verify_backup "${2}"
        fi
        ;;
    list)
        list_backups
        ;;
    restore)
        restore_backup "${2}"
        ;;
    *)
        echo "Usage: $0 {create|cleanup|verify|list|restore} [backup_file]"
        echo ""
        echo "Examples:"
        echo "  $0 create              # Create and compress backup"
        echo "  $0 list                # List all available backups"
        echo "  $0 verify              # Verify latest backup integrity"
        echo "  $0 restore backup.tar.gz  # Restore from backup"
        exit 1
        ;;
esac

echo ""
log_info "Backup operation completed"
