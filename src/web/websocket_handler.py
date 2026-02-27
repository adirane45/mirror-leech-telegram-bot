"""
WebSocket handler for real-time admin dashboard updates

Provides real-time updates for:
- Download progress
- System statistics
- Task status changes
- Live notifications
"""

import asyncio
import json
from typing import Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from logging import getLogger

LOGGER = getLogger(__name__)

# Store active WebSocket connections
active_connections: Set[WebSocket] = set()

# Broadcast queue for messages
broadcast_queue: asyncio.Queue = asyncio.Queue()


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        LOGGER.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        LOGGER.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Send a message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            LOGGER.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                LOGGER.error(f"Error broadcasting to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_download_update(self, download_id: str, data: Dict[str, Any]):
        """Broadcast download progress update"""
        message = {
            "type": "download_update",
            "download_id": download_id,
            "data": data
        }
        await self.broadcast(message)
    
    async def broadcast_system_stats(self, stats: Dict[str, Any]):
        """Broadcast system statistics update"""
        message = {
            "type": "system_stats",
            "data": stats
        }
        await self.broadcast(message)
    
    async def broadcast_notification(self, title: str, message: str, level: str = "info"):
        """Broadcast a notification to all clients"""
        notification = {
            "type": "notification",
            "title": title,
            "message": message,
            "level": level,  # info, success, warning, error
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.broadcast(notification)


# Global connection manager instance
manager = ConnectionManager()


async def handle_websocket_client(websocket: WebSocket):
    """Handle a WebSocket connection lifecycle"""
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connected",
            "message": "WebSocket connection established"
        }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (e.g., ping/pong, commands)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time()
                    }, websocket)
                
                elif message.get("type") == "subscribe":
                    # Client can subscribe to specific channels
                    channel = message.get("channel")
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "channel": channel
                    }, websocket)
                
            except asyncio.TimeoutError:
                # Send keepalive ping
                await manager.send_personal_message({
                    "type": "keepalive"
                }, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        LOGGER.info("Client disconnected normally")
    except Exception as e:
        LOGGER.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Utility functions for broadcasting from other modules

def broadcast_download_progress(download_id: str, progress: float, speed: int, status: str, **kwargs):
    """Broadcast download progress update (can be called from download handlers)"""
    asyncio.create_task(manager.broadcast_download_update(download_id, {
        "progress": progress,
        "speed": speed,
        "status": status,
        **kwargs
    }))


def broadcast_system_update(cpu: float, memory: float, disk: float, **kwargs):
    """Broadcast system statistics update"""
    asyncio.create_task(manager.broadcast_system_stats({
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        **kwargs
    }))


def broadcast_notification(title: str, message: str, level: str = "info"):
    """Broadcast a notification to all connected clients
    
    Args:
        title: Notification title
        message: Notification message
        level: One of: info, success, warning, error
    """
    asyncio.create_task(manager.broadcast_notification(title, message, level))
