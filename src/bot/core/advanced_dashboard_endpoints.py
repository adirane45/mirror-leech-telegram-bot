"""
Advanced Dashboard Endpoints - REST API for monitoring data

Provides endpoints for:
- Logger statistics and logs
- Alert management
- Backup operations
- Profiler statistics
- Recovery status
- Plugin management

Modified by: AI Refactoring
Date: February 8, 2026
"""

import logging
from pathlib import Path
from typing import Dict, Optional
from fastapi import HTTPException

from bot.core.logger_manager import logger_manager
from bot.core.alert_manager import alert_manager, AlertType, AlertSeverity
from bot.core.backup_manager import backup_manager
from bot.core.profiler import profiler
from bot.core.recovery_manager import recovery_manager
from bot.core.plugin_manager import plugin_manager

LOGGER = logging.getLogger(__name__)


class AdvancedDashboardEndpoints:
    """
    REST API endpoints for advanced monitoring dashboard
    
    Provides routes for:
    - GET /logger/stats - Logger statistics
    - GET /logger/recent-logs - Recent log entries
    - GET /alerts/recent - Recent alerts
    - GET /alerts/summary - Alert summary
    - POST /alerts/trigger - Manually trigger alert
    - GET /backups/list - List backups
    - POST /backups/create - Create backup
    - POST /backups/restore - Restore from backup
    - GET /backups/stats - Backup statistics
    - GET /profiler/stats - Profiler statistics
    - GET /profiler/slow-operations - Slow operations
    - POST /recovery/verify-integrity - Verify data integrity
    - GET /recovery/status - Recovery status
    - GET /recovery/history - Integrity check history
    - GET /plugins/list - List plugins
    - POST /plugins/enable - Enable plugin
    - POST /plugins/disable - Disable plugin
    - POST /plugins/execute - Execute plugin
    """
    
    # ========================================================================
    # Logger Endpoints
    # ========================================================================
    
    @staticmethod
    async def get_logger_stats():
        """Get logger statistics"""
        stats = logger_manager.get_log_stats()
        return {
            "status": "success" if stats.get("enabled") else "disabled",
            "data": stats
        }
    
    @staticmethod
    async def get_recent_logs(limit: int = 100):
        """Get recent log entries"""
        try:
            log_files = list(Path("logs").glob("*.json.log"))
            
            if not log_files:
                return {"status": "success", "logs": []}
            
            # Read latest log file
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            
            import json
            logs = []
            with open(latest_log, 'r') as f:
                for line in f.readlines()[-limit:]:
                    try:
                        logs.append(json.loads(line))
                    except (json.JSONDecodeError, ValueError):
                        pass
            
            return {"status": "success", "logs": logs}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ========================================================================
    # Alert Endpoints
    # ========================================================================
    
    @staticmethod
    async def get_recent_alerts(limit: int = 50, severity: Optional[str] = None):
        """Get recent alerts"""
        alerts = alert_manager.get_alerts(limit=limit)
        
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        
        return {
            "status": "success",
            "count": len(alerts),
            "alerts": alerts
        }
    
    @staticmethod
    async def get_alerts_summary():
        """Get alert summary"""
        summary = alert_manager.get_alert_summary()
        return {"status": "success", "data": summary}
    
    @staticmethod
    async def trigger_alert(alert_type: str, severity: str, message: str):
        """Manually trigger an alert"""
        try:
            alert = await alert_manager.trigger_alert(
                AlertType[alert_type.upper()],
                AlertSeverity[severity.upper()],
                alert_type,
                message
            )
            
            return {
                "status": "success",
                "alert_id": alert.id if alert else None
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    # ========================================================================
    # Backup Endpoints
    # ========================================================================
    
    @staticmethod
    async def list_backups():
        """List all backups"""
        backups = backup_manager.list_backups()
        return {
            "status": "success",
            "count": len(backups),
            "backups": backups
        }
    
    @staticmethod
    async def create_backup(description: Optional[str] = None):
        """Create a new backup"""
        try:
            result = await backup_manager.create_backup(
                source_paths=["config.py", "bot/"],
                description=description
            )
            
            return {"status": "success", "backup": result}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @staticmethod
    async def restore_backup(backup_name: str):
        """Restore from a backup"""
        try:
            result = await backup_manager.restore_backup(backup_name)
            
            return {
                "status": "success" if result else "error",
                "message": "Backup restored" if result else "Restore failed"
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @staticmethod
    async def get_backup_stats():
        """Get backup statistics"""
        stats = backup_manager.get_backup_stats()
        return {"status": "success", "data": stats}
    
    # ========================================================================
    # Profiler Endpoints
    # ========================================================================
    
    @staticmethod
    async def get_profiler_stats(operation: Optional[str] = None):
        """Get profiler statistics"""
        stats = profiler.get_stats(operation) if operation else profiler.get_stats()
        return {"status": "success", "data": stats}
    
    @staticmethod
    async def get_slow_operations(threshold: float = 1.0, limit: int = 10):
        """Get slow operations"""
        slow_ops = profiler.get_slow_operations(threshold=threshold, limit=limit)
        return {
            "status": "success",
            "count": len(slow_ops),
            "operations": slow_ops
        }
    
    # ========================================================================
    # Recovery Endpoints
    # ========================================================================
    
    @staticmethod
    async def verify_integrity(path: str):
        """Verify data integrity of a path"""
        try:
            is_valid, details = await recovery_manager.verify_integrity(path)
            return {
                "status": "success",
                "is_valid": is_valid,
                "details": details
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    @staticmethod
    async def get_recovery_status():
        """Get recovery manager status"""
        status = recovery_manager.get_recovery_status()
        return {"status": "success", "data": status}
    
    @staticmethod
    async def get_recovery_history(limit: int = 50):
        """Get integrity check history"""
        history = recovery_manager.get_integrity_history(limit=limit)
        return {
            "status": "success",
            "count": len(history),
            "history": history
        }
    
    # ========================================================================
    # Plugin Endpoints
    # ========================================================================
    
    @staticmethod
    async def list_plugins():
        """List all loaded plugins"""
        plugins_list = plugin_manager.list_plugins()
        return {
            "status": "success",
            "count": len(plugins_list),
            "plugins": plugins_list
        }
    
    @staticmethod
    async def enable_plugin(plugin_name: str):
        """Enable a plugin"""
        result = plugin_manager.enable_plugin(plugin_name)
        return {
            "status": "success" if result else "error",
            "message": "Plugin enabled" if result else "Plugin not found"
        }
    
    @staticmethod
    async def disable_plugin(plugin_name: str):
        """Disable a plugin"""
        result = plugin_manager.disable_plugin(plugin_name)
        return {
            "status": "success" if result else "error",
            "message": "Plugin disabled" if result else "Plugin not found"
        }
    
    @staticmethod
    async def execute_plugin(plugin_name: str, data: Optional[Dict] = None):
        """Execute a plugin"""
        try:
            result = await plugin_manager.execute_plugin(plugin_name, **(data or {}))
            return {"status": "success", "result": result}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
