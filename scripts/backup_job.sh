#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="${BACKUP_LOG_FILE:-$PROJECT_ROOT/data/logs/backup.log}"

mkdir -p "$(dirname "$LOG_FILE")"

{
  echo "[backup_job] start=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd "$PROJECT_ROOT"
  ./scripts/backup_restore.sh create
  ./scripts/backup_restore.sh verify
  echo "[backup_job] end=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} >> "$LOG_FILE" 2>&1
