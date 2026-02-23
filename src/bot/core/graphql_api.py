"""
GraphQL API Layer - Type Definitions and Query/Mutation Resolvers
Provides GraphQL interface for bot operations and data queries
Safe Innovation Path - Phase 3

Enhanced by: justadi
Date: February 5, 2026
"""

import graphene
from typing import Optional, List, Dict, Any
from datetime import datetime, UTC

from bot.core.logger_manager import logger_manager
from bot.core.alert_manager import alert_manager, AlertType, AlertSeverity
from bot.core.backup_manager import backup_manager
from bot.core.profiler import profiler
from bot.core.recovery_manager import recovery_manager


# ============ GraphQL Type Definitions ============

class LoggerStatsType(graphene.ObjectType):
    """Logger statistics type"""
    enabled = graphene.Boolean()
    log_directory = graphene.String()
    total_size_bytes = graphene.Int()
    log_file_count = graphene.Int()


class AlertType(graphene.ObjectType):
    """Alert type"""
    id = graphene.String()
    alert_type = graphene.String()
    severity = graphene.String()
    title = graphene.String()
    message = graphene.String()
    task_id = graphene.String()
    timestamp = graphene.String()


class AlertSummaryType(graphene.ObjectType):
    """Alert summary type"""
    enabled = graphene.Boolean()
    total_alerts = graphene.Int()
    critical_count = graphene.Int()
    high_count = graphene.Int()
    medium_count = graphene.Int()
    low_count = graphene.Int()


class BackupType(graphene.ObjectType):
    """Backup information type"""
    name = graphene.String()
    created_at = graphene.String()
    size = graphene.Int()
    items_count = graphene.Int()
    description = graphene.String()


class BackupStatsType(graphene.ObjectType):
    """Backup statistics type"""
    enabled = graphene.Boolean()
    backup_directory = graphene.String()
    total_backups = graphene.Int()
    total_size = graphene.Int()


class OperationStatsType(graphene.ObjectType):
    """Operation statistics type"""
    operation = graphene.String()
    call_count = graphene.Int()
    total_duration = graphene.Float()
    average_duration = graphene.Float()
    median_duration = graphene.Float()
    min_duration = graphene.Float()
    max_duration = graphene.Float()


class IntegrityCheckType(graphene.ObjectType):
    """Integrity check result type"""
    path = graphene.String()
    is_valid = graphene.Boolean()
    timestamp = graphene.String()


class SystemStatusType(graphene.ObjectType):
    """Overall system status type"""
    timestamp = graphene.String()
    logger_enabled = graphene.Boolean()
    alerts_enabled = graphene.Boolean()
    backups_enabled = graphene.Boolean()
    profiler_enabled = graphene.Boolean()
    recovery_enabled = graphene.Boolean()
    phase1_services = graphene.Int()
    phase2_services = graphene.Int()


# ============ GraphQL Queries ============

class Query(graphene.ObjectType):
    """GraphQL Query root type"""

    # Logger queries
    logger_stats = graphene.Field(LoggerStatsType)
    
    def resolve_logger_stats(self, info):
        """Get logger statistics"""
        stats = logger_manager.get_log_stats()
        return LoggerStatsType(**stats)

    # Alert queries
    alerts = graphene.List(
        AlertType,
        limit=graphene.Int(default_value=10),
        severity=graphene.String()
    )
    alert_summary = graphene.Field(AlertSummaryType)

    def resolve_alerts(self, info, limit=10, severity=None):
        """Get recent alerts"""
        alerts_data = alert_manager.get_alerts(limit=limit)
        return [AlertType(**alert) for alert in alerts_data]

    def resolve_alert_summary(self, info):
        """Get alert summary"""
        summary = alert_manager.get_alert_summary()
        summary_data = {
            "enabled": summary.get("enabled", False),
            "total_alerts": summary.get("total_alerts", 0),
            "critical_count": summary.get("by_severity", {}).get("critical", 0),
            "high_count": summary.get("by_severity", {}).get("high", 0),
            "medium_count": summary.get("by_severity", {}).get("medium", 0),
            "low_count": summary.get("by_severity", {}).get("low", 0),
        }
        return AlertSummaryType(**summary_data)

    # Backup queries
    backups = graphene.List(BackupType)
    backup_stats = graphene.Field(BackupStatsType)

    def resolve_backups(self, info):
        """Get all backups"""
        backups_list = backup_manager.list_backups()
        return [BackupType(**backup) for backup in backups_list]

    def resolve_backup_stats(self, info):
        """Get backup statistics"""
        stats = backup_manager.get_backup_stats()
        return BackupStatsType(**stats)

    # Profiler queries
    operation_stats = graphene.Field(
        OperationStatsType,
        operation=graphene.String(required=True)
    )
    slow_operations = graphene.List(OperationStatsType, limit=graphene.Int(default_value=10))

    def resolve_operation_stats(self, info, operation):
        """Get statistics for specific operation"""
        stats = profiler.get_stats(operation)
        if "operation" in stats:
            return OperationStatsType(**stats["operation"])
        return None

    def resolve_slow_operations(self, info, limit=10):
        """Get slow operations"""
        slow_ops = profiler.get_slow_operations(limit=limit)
        return [OperationStatsType(**op) for op in slow_ops]

    # Recovery queries
    recovery_status = graphene.Field(IntegrityCheckType)

    def resolve_recovery_status(self, info):
        """Get recovery status"""
        status = recovery_manager.get_recovery_status()
        return IntegrityCheckType(
            path="system",
            is_valid=status.get("success_rate", 0) > 90,
            timestamp=datetime.now(UTC).isoformat()
        )

    # System status
    system_status = graphene.Field(SystemStatusType)

    def resolve_system_status(self, info):
        """Get overall system status"""
        return SystemStatusType(
            timestamp=datetime.now(UTC).isoformat(),
            logger_enabled=logger_manager.is_enabled,
            alerts_enabled=alert_manager.is_enabled,
            backups_enabled=backup_manager.is_enabled,
            profiler_enabled=profiler.is_enabled,
            recovery_enabled=recovery_manager.is_enabled,
            phase1_services=5,  # Redis, Celery, Metrics, API, Enhanced startup
            phase2_services=5,  # Logger, Alert, Backup, Profiler, Recovery
        )


# ============ GraphQL Mutations ============

class CreateBackup(graphene.Mutation):
    """Create a backup"""
    class Arguments:
        description = graphene.String()
        backup_name = graphene.String()

    success = graphene.Boolean()
    backup_name = graphene.String()
    message = graphene.String()

    async def mutate(self, info, description=None, backup_name=None):
        """Create a backup"""
        try:
            result = await backup_manager.create_backup(
                source_paths=getattr(backup_manager, "_backup_paths", ["config.py"]),
                backup_name=backup_name,
                description=description
            )
            return CreateBackup(
                success=result is not None,
                backup_name=result.get("backup_name") if result else None,
                message="Backup created successfully" if result else "Backup failed"
            )
        except Exception as e:
            return CreateBackup(
                success=False,
                backup_name=None,
                message=f"Error: {str(e)}"
            )


class RestoreBackup(graphene.Mutation):
    """Restore from a backup"""
    class Arguments:
        backup_name = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    async def mutate(self, info, backup_name):
        """Restore a backup"""
        try:
            result = await backup_manager.restore_backup(backup_name)
            return RestoreBackup(
                success=result,
                message="Backup restored successfully" if result else "Restore failed"
            )
        except Exception as e:
            return RestoreBackup(
                success=False,
                message=f"Error: {str(e)}"
            )


class TriggerAlert(graphene.Mutation):
    """Trigger a manual alert"""
    class Arguments:
        alert_type = graphene.String(required=True)
        severity = graphene.String(required=True)
        message = graphene.String(required=True)

    success = graphene.Boolean()
    alert_id = graphene.String()
    message = graphene.String()

    async def mutate(self, info, alert_type, severity, message):
        """Trigger an alert"""
        try:
            alert = await alert_manager.trigger_alert(
                alert_type=AlertType[alert_type.upper()],
                severity=AlertSeverity[severity.upper()],
                title=alert_type,
                message=message
            )
            return TriggerAlert(
                success=alert is not None,
                alert_id=alert.id if alert else None,
                message="Alert triggered successfully"
            )
        except Exception as e:
            return TriggerAlert(
                success=False,
                alert_id=None,
                message=f"Error: {str(e)}"
            )


class VerifyIntegrity(graphene.Mutation):
    """Verify data integrity"""
    class Arguments:
        path = graphene.String(required=True)

    success = graphene.Boolean()
    is_valid = graphene.Boolean()
    message = graphene.String()

    async def mutate(self, info, path):
        """Verify integrity of a path"""
        try:
            is_valid, details = await recovery_manager.verify_integrity(path)
            return VerifyIntegrity(
                success=True,
                is_valid=is_valid,
                message="Integrity check completed"
            )
        except Exception as e:
            return VerifyIntegrity(
                success=False,
                is_valid=False,
                message=f"Error: {str(e)}"
            )


class Mutation(graphene.ObjectType):
    """GraphQL Mutation root type"""
    create_backup = CreateBackup.Field()
    restore_backup = RestoreBackup.Field()
    trigger_alert = TriggerAlert.Field()
    verify_integrity = VerifyIntegrity.Field()


# ============ GraphQL Schema ============

schema = graphene.Schema(query=Query, mutation=Mutation)
