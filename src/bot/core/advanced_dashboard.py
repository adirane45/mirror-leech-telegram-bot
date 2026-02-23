"""
Advanced Monitoring Dashboard - Real-time Metrics and Insights (REFACTORED)

Provides web interface for Phase 1-3 monitoring and control.

Refactored structure:
- advanced_dashboard_websocket.py: WebSocket live metrics streaming
- advanced_dashboard_endpoints.py: REST API endpoints for all managers
- advanced_dashboard_html.py: Dashboard HTML template
- advanced_dashboard.py: Main router setup (this file)

Features:
- Real-time metrics streaming via WebSocket
- REST API for logger, alerts, backups, profiler, recovery, plugins
- Interactive web dashboard
- System statistics and monitoring

Modified by: AI Refactoring 
Date: February 8, 2026
"""

from fastapi import APIRouter, WebSocket
from fastapi.responses import HTMLResponse

from .advanced_dashboard_websocket import AdvancedDashboardWebSocketHandler
from .advanced_dashboard_endpoints import AdvancedDashboardEndpoints
from .advanced_dashboard_html import get_advanced_dashboard_html


# Create router with API v3 prefix
router = APIRouter(prefix="/api/v3", tags=["phase3"])

# Initialize WebSocket handler
ws_handler = AdvancedDashboardWebSocketHandler(broadcast_interval=5.0)


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws/live-metrics")
async def websocket_live_metrics(websocket: WebSocket):
    """WebSocket endpoint for live metrics streaming"""
    await ws_handler.handle_connection(websocket)


# ============================================================================
# Logger Endpoints
# ============================================================================

@router.get("/logger/stats")
async def get_logger_stats():
    """Get logger statistics"""
    return await AdvancedDashboardEndpoints.get_logger_stats()


@router.get("/logger/recent-logs")
async def get_recent_logs(limit: int = 100):
    """Get recent log entries"""
    return await AdvancedDashboardEndpoints.get_recent_logs(limit)


# ============================================================================
# Alert Endpoints
# ============================================================================

@router.get("/alerts/recent")
async def get_recent_alerts(limit: int = 50, severity: str = None):
    """Get recent alerts"""
    return await AdvancedDashboardEndpoints.get_recent_alerts(limit, severity)


@router.get("/alerts/summary")
async def get_alerts_summary():
    """Get alert summary"""
    return await AdvancedDashboardEndpoints.get_alerts_summary()


@router.post("/alerts/trigger")
async def trigger_alert(alert_type: str, severity: str, message: str):
    """Manually trigger an alert"""
    return await AdvancedDashboardEndpoints.trigger_alert(alert_type, severity, message)


# ============================================================================
# Backup Endpoints
# ============================================================================

@router.get("/backups/list")
async def list_backups():
    """List all backups"""
    return await AdvancedDashboardEndpoints.list_backups()


@router.post("/backups/create")
async def create_backup(description: str = None):
    """Create a new backup"""
    return await AdvancedDashboardEndpoints.create_backup(description)


@router.post("/backups/restore")
async def restore_backup(backup_name: str):
    """Restore from a backup"""
    return await AdvancedDashboardEndpoints.restore_backup(backup_name)


@router.get("/backups/stats")
async def get_backup_stats():
    """Get backup statistics"""
    return await AdvancedDashboardEndpoints.get_backup_stats()


# ============================================================================
# Profiler Endpoints
# ============================================================================

@router.get("/profiler/stats")
async def get_profiler_stats(operation: str = None):
    """Get profiler statistics"""
    return await AdvancedDashboardEndpoints.get_profiler_stats(operation)


@router.get("/profiler/slow-operations")
async def get_slow_operations(threshold: float = 1.0, limit: int = 10):
    """Get slow operations"""
    return await AdvancedDashboardEndpoints.get_slow_operations(threshold, limit)


# ============================================================================
# Recovery Endpoints
# ============================================================================

@router.post("/recovery/verify-integrity")
async def verify_integrity(path: str):
    """Verify data integrity of a path"""
    return await AdvancedDashboardEndpoints.verify_integrity(path)


@router.get("/recovery/status")
async def get_recovery_status():
    """Get recovery manager status"""
    return await AdvancedDashboardEndpoints.get_recovery_status()


@router.get("/recovery/history")
async def get_recovery_history(limit: int = 50):
    """Get integrity check history"""
    return await AdvancedDashboardEndpoints.get_recovery_history(limit)


# ============================================================================
# Plugin Endpoints (Phase 3)
# ============================================================================

@router.get("/plugins/list")
async def list_plugins():
    """List all loaded plugins"""
    return await AdvancedDashboardEndpoints.list_plugins()


@router.post("/plugins/enable")
async def enable_plugin(plugin_name: str):
    """Enable a plugin"""
    return await AdvancedDashboardEndpoints.enable_plugin(plugin_name)


@router.post("/plugins/disable")
async def disable_plugin(plugin_name: str):
    """Disable a plugin"""
    return await AdvancedDashboardEndpoints.disable_plugin(plugin_name)


@router.post("/plugins/execute")
async def execute_plugin(plugin_name: str, data: dict = None):
    """Execute a plugin"""
    return await AdvancedDashboardEndpoints.execute_plugin(plugin_name, data)


# ============================================================================
# Dashboard HTML
# ============================================================================

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve monitoring dashboard HTML"""
    return get_advanced_dashboard_html()
