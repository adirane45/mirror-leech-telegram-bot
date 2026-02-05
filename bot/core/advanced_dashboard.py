"""
Advanced Monitoring Dashboard - Real-time Metrics and Insights
Provides web interface for Phase 1-3 monitoring and control
Safe Innovation Path - Phase 3

Enhanced by: justadi
Date: February 5, 2026
"""

from fastapi import APIRouter, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from bot.core.logger_manager import logger_manager
from bot.core.alert_manager import alert_manager
from bot.core.backup_manager import backup_manager
from bot.core.profiler import profiler
from bot.core.recovery_manager import recovery_manager
from bot.core.plugin_manager import plugin_manager
from bot.core import LOGGER

# Create router
router = APIRouter(prefix="/api/v3", tags=["phase3"])


# ============ LiveData WebSocket Endpoint ============

active_connections: List[WebSocket] = []


@router.websocket("/ws/live-metrics")
async def websocket_live_metrics(websocket: WebSocket):
    """WebSocket endpoint for live metrics streaming"""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            # Collect current metrics
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "logger": logger_manager.get_log_stats(),
                "alerts": alert_manager.get_alert_summary(),
                "backups": backup_manager.get_backup_stats(),
                "profiler": profiler.get_stats(),
                "recovery": recovery_manager.get_recovery_status(),
            }

            await websocket.send_json(metrics)

            # Send every 5 seconds
            import asyncio
            await asyncio.sleep(5)

    except Exception as e:
        LOGGER.error(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)


# ============ Logger Endpoints ============

@router.get("/logger/stats")
async def get_logger_stats():
    """Get logger statistics"""
    stats = logger_manager.get_log_stats()
    return {
        "status": "success" if stats.get("enabled") else "disabled",
        "data": stats
    }


@router.get("/logger/recent-logs")
async def get_recent_logs(limit: int = 100):
    """Get recent log entries"""
    try:
        from pathlib import Path
        
        log_files = list(Path("logs").glob("*.json.log"))
        
        if not log_files:
            return {"status": "success", "logs": []}
        
        # Read latest log file
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        
        logs = []
        with open(latest_log, 'r') as f:
            for line in f.readlines()[-limit:]:
                try:
                    logs.append(json.loads(line))
                except:
                    pass
        
        return {"status": "success", "logs": logs}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============ Alert Endpoints ============

@router.get("/alerts/recent")
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


@router.get("/alerts/summary")
async def get_alerts_summary():
    """Get alert summary"""
    summary = alert_manager.get_alert_summary()
    return {
        "status": "success",
        "data": summary
    }


@router.post("/alerts/trigger")
async def trigger_alert(alert_type: str, severity: str, message: str):
    """Manually trigger an alert"""
    try:
        from bot.core.alert_manager import AlertType, AlertSeverity
        
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


# ============ Backup Endpoints ============

@router.get("/backups/list")
async def list_backups():
    """List all backups"""
    backups = backup_manager.list_backups()
    return {
        "status": "success",
        "count": len(backups),
        "backups": backups
    }


@router.post("/backups/create")
async def create_backup(description: Optional[str] = None):
    """Create a new backup"""
    try:
        result = await backup_manager.create_backup(
            source_paths=["config.py", "bot/"],
            description=description
        )
        
        return {
            "status": "success",
            "backup": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/backups/restore")
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


@router.get("/backups/stats")
async def get_backup_stats():
    """Get backup statistics"""
    stats = backup_manager.get_backup_stats()
    return {
        "status": "success",
        "data": stats
    }


# ============ Profiler Endpoints ============

@router.get("/profiler/stats")
async def get_profiler_stats(operation: Optional[str] = None):
    """Get profiler statistics"""
    stats = profiler.get_stats(operation) if operation else profiler.get_stats()
    return {
        "status": "success",
        "data": stats
    }


@router.get("/profiler/slow-operations")
async def get_slow_operations(threshold: float = 1.0, limit: int = 10):
    """Get slow operations"""
    slow_ops = profiler.get_slow_operations(threshold=threshold, limit=limit)
    return {
        "status": "success",
        "count": len(slow_ops),
        "operations": slow_ops
    }


# ============ Recovery Endpoints ============

@router.post("/recovery/verify-integrity")
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


@router.get("/recovery/status")
async def get_recovery_status():
    """Get recovery manager status"""
    status = recovery_manager.get_recovery_status()
    return {
        "status": "success",
        "data": status
    }


@router.get("/recovery/history")
async def get_recovery_history(limit: int = 50):
    """Get integrity check history"""
    history = recovery_manager.get_integrity_history(limit=limit)
    return {
        "status": "success",
        "count": len(history),
        "history": history
    }


# ============ Plugin Endpoints (Phase 3) ============

@router.get("/plugins/list")
async def list_plugins():
    """List all loaded plugins"""
    plugins_list = plugin_manager.list_plugins()
    return {
        "status": "success",
        "count": len(plugins_list),
        "plugins": plugins_list
    }


@router.post("/plugins/enable")
async def enable_plugin(plugin_name: str):
    """Enable a plugin"""
    result = plugin_manager.enable_plugin(plugin_name)
    return {
        "status": "success" if result else "error",
        "message": "Plugin enabled" if result else "Plugin not found"
    }


@router.post("/plugins/disable")
async def disable_plugin(plugin_name: str):
    """Disable a plugin"""
    result = plugin_manager.disable_plugin(plugin_name)
    return {
        "status": "success" if result else "error",
        "message": "Plugin disabled" if result else "Plugin not found"
    }


@router.post("/plugins/execute")
async def execute_plugin(plugin_name: str, data: Optional[Dict] = None):
    """Execute a plugin"""
    try:
        result = await plugin_manager.execute_plugin(plugin_name, **(data or {}))
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ Dashboard HTML ============

@router.get("/dashboard")
async def dashboard():
    """Serve monitoring dashboard HTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mirror Leech Bot - Advanced Monitor</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #0f1419;
                color: #e0e0e0;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .header h1 {
                font-size: 2.5em;
                color: #00d4ff;
                margin-bottom: 10px;
            }
            .header p {
                color: #888;
                font-size: 1.1em;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            .card {
                background: #1a1f2e;
                border: 1px solid #2a2f3e;
                border-radius: 8px;
                padding: 20px;
                transition: all 0.3s ease;
            }
            .card:hover {
                border-color: #00d4ff;
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
            }
            .card h3 {
                color: #00d4ff;
                margin-bottom: 15px;
                font-size: 1.2em;
            }
            .stat {
                margin-bottom: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .stat-label {
                color: #888;
            }
            .stat-value {
                color: #00ff00;
                font-weight: bold;
                font-size: 1.1em;
            }
            .status-badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 0.9em;
                font-weight: bold;
            }
            .status-enabled {
                background: rgba(0, 255, 0, 0.2);
                color: #00ff00;
            }
            .status-disabled {
                background: rgba(255, 0, 0, 0.2);
                color: #ff4444;
            }
            .live-feed {
                background: #1a1f2e;
                border: 1px solid #2a2f3e;
                border-radius: 8px;
                padding: 20px;
                margin-top: 30px;
            }
            .log-entry {
                background: #151a27;
                padding: 10px;
                margin-bottom: 10px;
                border-left: 3px solid #00d4ff;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                color: #00ff00;
            }
            button {
                background: #00d4ff;
                color: #000;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: bold;
                margin-top: 10px;
                transition: all 0.3s ease;
            }
            button:hover {
                background: #00ffff;
                transform: translate(0, -2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Mirror Leech Bot - Advanced Monitor</h1>
                <p>Real-time Monitoring & Control Dashboard</p>
            </div>

            <div class="grid" id="stats-grid">
                <!-- Stats will be loaded here -->
            </div>

            <div class="live-feed">
                <h3>📊 Live Metrics Stream</h3>
                <div id="live-feed"></div>
            </div>
        </div>

        <script>
            const apiBase = '/api/v3';
            const liveFeed = document.getElementById('live-feed');
            const statsGrid = document.getElementById('stats-grid');

            // Function to format bytes
            function formatBytes(bytes) {
                if (bytes === 0) return '0 B';
                const k = 1024;
                const sizes = ['B', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
            }

            // Connect to WebSocket for live metrics
            function connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws = new WebSocket(`${protocol}//${window.location.host}/api/v3/ws/live-metrics`);

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                };

                ws.onerror = () => {
                    setTimeout(connectWebSocket, 3000);
                };
            }

            function updateDashboard(data) {
                let html = '';

                // Logger Stats
                const logger = data.logger;
                if (logger) {
                    html += `
                        <div class="card">
                            <h3>📝 Logger</h3>
                            <div class="stat">
                                <span class="stat-label">Status</span>
                                <span class="status-badge ${logger.enabled ? 'status-enabled' : 'status-disabled'}">
                                    ${logger.enabled ? 'ENABLED' : 'DISABLED'}
                                </span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Log Files</span>
                                <span class="stat-value">${logger.log_file_count}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Total Size</span>
                                <span class="stat-value">${formatBytes(logger.total_size_bytes)}</span>
                            </div>
                        </div>
                    `;
                }

                // Alert Stats
                const alerts = data.alerts;
                if (alerts) {
                    html += `
                        <div class="card">
                            <h3>🚨 Alerts</h3>
                            <div class="stat">
                                <span class="stat-label">Total</span>
                                <span class="stat-value">${alerts.total_alerts}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Critical</span>
                                <span class="stat-value" style="color: #ff4444;">${alerts.critical_count}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">High</span>
                                <span class="stat-value" style="color: #ffaa00;">${alerts.high_count}</span>
                            </div>
                        </div>
                    `;
                }

                // Backup Stats
                const backups = data.backups;
                if (backups) {
                    html += `
                        <div class="card">
                            <h3>💾 Backups</h3>
                            <div class="stat">
                                <span class="stat-label">Total Backups</span>
                                <span class="stat-value">${backups.total_backups}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Total Size</span>
                                <span class="stat-value">${formatBytes(backups.total_size)}</span>
                            </div>
                        </div>
                    `;
                }

                // Recovery Stats
                const recovery = data.recovery;
                if (recovery) {
                    html += `
                        <div class="card">
                            <h3>🔧 Recovery</h3>
                            <div class="stat">
                                <span class="stat-label">Total Checks</span>
                                <span class="stat-value">${recovery.total_checks}</span>
                            </div>
                            <div class="stat">
                                <span class="stat-label">Success Rate</span>
                                <span class="stat-value">${recovery.success_rate.toFixed(1)}%</span>
                            </div>
                        </div>
                    `;
                }

                statsGrid.innerHTML = html;
            }

            // Start WebSocket connection
            connectWebSocket();

            // Fetch initial data
            async function fetchInitialData() {
                try {
                    const [logger, alerts, backups, recovery] = await Promise.all([
                        fetch(`${apiBase}/logger/stats`).then(r => r.json()),
                        fetch(`${apiBase}/alerts/summary`).then(r => r.json()),
                        fetch(`${apiBase}/backups/stats`).then(r => r.json()),
                        fetch(`${apiBase}/recovery/status`).then(r => r.json()),
                    ]);

                    updateDashboard({
                        logger: logger.data,
                        alerts: alerts.data,
                        backups: backups.data,
                        recovery: recovery.data,
                    });
                } catch (error) {
                    console.error('Error fetching data:', error);
                }
            }

            fetchInitialData();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
