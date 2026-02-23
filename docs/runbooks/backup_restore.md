# Runbook: Backup & Restore

## Scope
Automated backups and restore procedures.

## Health Signals
- Latest backup present in ./backups
- Backup job logs in data/logs/backup.log

## Common Issues
### Backup fails
- Check backup_job.sh log output
- Verify docker access to mongodb/redis containers

## Recovery Steps
1. Run backup: ./scripts/backup_job.sh
2. Verify backup: ./scripts/backup_restore.sh verify
3. Restore: ./scripts/backup_restore.sh restore <file>

## Escalation
- If backup integrity fails, check disk space and permissions.
