"""
Dashboard Manager - WebSocket connection and broadcast management

Responsibilities:
- WebSocket connection lifecycle management
- Task status and message broadcasting
- Server-sent events stream generation
- Active connection tracking

Modified by: AI Refactoring
Date: February 8, 2026
"""

import json
import logging
from datetime import datetime
from typing import Dict, List
from asyncio import sleep
from collections import deque
from fastapi import WebSocket

LOGGER = logging.getLogger(__name__)


class DashboardManager:
    """
    Manages web dashboard WebSocket connections and real-time updates
    
    Features:
    - WebSocket connection management
    - Task status broadcasting
    - Real-time progress updates
    - Connection tracking and cleanup
    """
    
    def __init__(self):
        """Initialize dashboard manager"""
        self.active_connections: List[WebSocket] = []
        self.task_updates: deque = deque(maxlen=100)  # Store last 100 updates
        self.connected_clients = 0
    
    async def connect(self, websocket: WebSocket):
        """
        Accept WebSocket connection from client
        
        Args:
            websocket: WebSocket connection object
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connected_clients = len(self.active_connections)
        
        LOGGER.info(f"Client connected. Total clients: {self.connected_clients}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to dashboard",
            "timestamp": datetime.now().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect WebSocket client
        
        Args:
            websocket: WebSocket connection to remove
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        self.connected_clients = len(self.active_connections)
        LOGGER.info(f"Client disconnected. Total clients: {self.connected_clients}")
    
    async def broadcast_task_status(self, task_id: str, status: Dict):
        """
        Broadcast task status to all connected clients
        
        Args:
            task_id: Task identifier
            status: Task status dictionary
                - status: 'downloading' | 'uploading' | 'completed' | 'error' | 'paused'
                - progress: 0-100
                - speed: bytes per second
                - eta: seconds remaining
                - current_size: bytes downloaded
                - total_size: total bytes
                - name: task name
                
        Example:
            await dashboard.broadcast_task_status('task_123', {
                'status': 'downloading',
                'progress': 45,
                'speed': 5242880,  # 5 MB/s
                'eta': 120,
                'current_size': 524288000,
                'total_size': 1048576000
            })
        """
        update = {
            "type": "task_status",
            "task_id": task_id,
            "data": status,
            "timestamp": datetime.now().isoformat()
        }
        
        self.task_updates.append(update)
        
        # Send to all connected clients
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_json(update)
            except Exception as e:
                LOGGER.error(f"Error sending to client: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_message(self, message: str, msg_type: str = "info"):
        """
        Broadcast general message to all clients
        
        Args:
            message: Message text
            msg_type: 'info' | 'warning' | 'error' | 'success'
        """
        update = {
            "type": "message",
            "msg_type": msg_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(update)
            except Exception as e:
                LOGGER.error(f"Broadcast error: {e}")
    
    async def send_dashboard_stats(self, stats: Dict):
        """
        Send dashboard statistics to all clients
        
        Args:
            stats: Dictionary with:
                - active_tasks: number
                - total_downloads: number
                - total_uploads: number
                - total_speed: bytes per second
                - cpu_usage: percentage
                - memory_usage: percentage
                - disk_usage: percentage
                - uptime: seconds
        """
        update = {
            "type": "dashboard_stats",
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(update)
            except Exception as e:
                LOGGER.error(f"Stats broadcast error: {e}")
    
    async def server_sent_events(self, task_id: str):
        """
        Generate server-sent events stream for task progress
        
        Args:
            task_id: Task ID to monitor
            
        Yields:
            SSE formatted strings
            
        Example:
            # Frontend
            eventSource = new EventSource(`/api/stream/${taskId}`);
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateProgressBar(data);
            };
        """
        async def event_generator():
            last_update = None
            while True:
                # Find latest update for this task
                current_update = None
                for update in reversed(self.task_updates):
                    if update.get('task_id') == task_id:
                        current_update = update
                        break
                
                if current_update != last_update:
                    last_update = current_update
                    if current_update:
                        yield f"data: {json.dumps(current_update)}\n\n"
                
                await sleep(1)
        
        return event_generator()
