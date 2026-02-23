"""
Advanced Dashboard WebSocket Handler - Live streaming of metrics

Responsibilities:
- WebSocket connection lifecycle management
- Real-time metrics collection and broadcasting
- Connection pool management

Modified by: AI Refactoring
Date: February 8, 2026
"""

import asyncio
import logging
from datetime import datetime, UTC
from typing import List
from fastapi import WebSocket

from bot.core.logger_manager import logger_manager
from bot.core.alert_manager import alert_manager
from bot.core.backup_manager import backup_manager
from bot.core.profiler import profiler
from bot.core.recovery_manager import recovery_manager

LOGGER = logging.getLogger(__name__)


class AdvancedDashboardWebSocketHandler:
    """
    Manages WebSocket connections for live metrics streaming
    
    Features:
    - Live metrics collection from multiple managers
    - Periodic broadcasting to all connected clients
    - Auto-reconnection support
    """
    
    def __init__(self, broadcast_interval: float = 5.0):
        """
        Initialize WebSocket handler
        
        Args:
            broadcast_interval: Seconds between metrics broadcasts
        """
        self.active_connections: List[WebSocket] = []
        self.broadcast_interval = broadcast_interval
    
    async def handle_connection(self, websocket: WebSocket):
        """
        Handle new WebSocket connection
        
        Args:
            websocket: WebSocket connection object
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        LOGGER.info(f"WebSocket connected. Total: {len(self.active_connections)}")
        
        try:
            while True:
                # Send metrics every broadcast_interval seconds
                metrics = await self._collect_metrics()
                await websocket.send_json(metrics)
                await asyncio.sleep(self.broadcast_interval)
        except Exception as e:
            LOGGER.error(f"WebSocket error: {e}")
        finally:
            self.active_connections.remove(websocket)
            LOGGER.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def _collect_metrics(self) -> dict:
        """
        Collect current metrics from all managers
        
        Returns:
            Dictionary with all system metrics
        """
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "logger": logger_manager.get_log_stats(),
            "alerts": alert_manager.get_alert_summary(),
            "backups": backup_manager.get_backup_stats(),
            "profiler": profiler.get_stats(),
            "recovery": recovery_manager.get_recovery_status(),
        }
