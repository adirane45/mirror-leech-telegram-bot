"""
Dashboard Routes - FastAPI endpoints for dashboard functionality

Provides RESTful API and WebSocket endpoints:
- GET /dashboard - Main dashboard HTML page
- WebSocket /ws/dashboard - Real-time updates
- GET /api/tasks - Get all tasks
- GET /api/tasks/{task_id} - Get task details
- POST /api/tasks/{task_id}/control - Control task
- GET /api/stats - Get dashboard statistics
- GET /api/stream/{task_id} - Server-sent events stream

Modified by: AI Refactoring
Date: February 8, 2026
"""

import json
import logging
from datetime import datetime
from typing import Dict
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from .dashboard_manager import DashboardManager
from .dashboard_html import get_dashboard_html

LOGGER = logging.getLogger(__name__)


class DashboardEndpoints:
    """
    FastAPI endpoints for dashboard functionality
    
    Endpoints:
    - GET /dashboard - Main dashboard HTML page
    - WebSocket /ws/dashboard - Real-time updates
    - GET /api/tasks - Get all tasks
    - GET /api/tasks/{task_id} - Get task details
    - POST /api/tasks/{task_id}/control - Control task
    - GET /api/stats - Get dashboard statistics
    - GET /api/stream/{task_id} - Server-sent events stream
    """
    
    def __init__(self, dashboard_manager: DashboardManager):
        """
        Initialize endpoints with dashboard manager
        
        Args:
            dashboard_manager: DashboardManager instance for broadcasts
        """
        self.dashboard_manager = dashboard_manager
    
    async def setup_routes(self, app: FastAPI):
        """
        Setup all dashboard endpoints on FastAPI app
        
        Args:
            app: FastAPI application instance
        """
        
        @app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard_page(request: Request):
            """Serve main dashboard HTML page"""
            return get_dashboard_html()
        
        @app.websocket("/ws/dashboard")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await self.dashboard_manager.connect(websocket)
            try:
                while True:
                    # Receive and process client messages
                    data = await websocket.receive_json()
                    await self._process_client_message(data, websocket)
            except WebSocketDisconnect:
                self.dashboard_manager.disconnect(websocket)
                LOGGER.info("WebSocket disconnected")
            except Exception as e:
                LOGGER.error(f"WebSocket error: {e}")
                self.dashboard_manager.disconnect(websocket)
        
        @app.get("/api/tasks")
        async def get_all_tasks(request: Request):
            """Get list of all active tasks"""
            # This would integrate with actual task manager
            return JSONResponse({
                "tasks": [],
                "total": 0,
                "timestamp": datetime.now().isoformat()
            })
        
        @app.get("/api/tasks/{task_id}")
        async def get_task_details(task_id: str, request: Request):
            """Get detailed information about a specific task"""
            # This would integrate with actual task manager
            return JSONResponse({
                "task_id": task_id,
                "status": "unknown",
                "error": "Task not found"
            }, status_code=404)
        
        @app.post("/api/tasks/{task_id}/control")
        async def control_task(task_id: str, request: Request):
            """
            Control a task (pause, resume, cancel)
            
            JSON Body:
            {
                "action": "pause|resume|cancel",
                "reason": "Optional reason message"
            }
            """
            try:
                body = await request.json()
                action = body.get("action", "").lower()
                
                if action not in ["pause", "resume", "cancel"]:
                    return JSONResponse(
                        {"error": "Invalid action"},
                        status_code=400
                    )
                
                # Process action (integrate with task manager)
                await self.dashboard_manager.broadcast_message(
                    f"Task {task_id}: {action} requested",
                    "info"
                )
                
                return JSONResponse({
                    "success": True,
                    "task_id": task_id,
                    "action": action,
                    "timestamp": datetime.now().isoformat()
                })
            
            except Exception as e:
                LOGGER.error(f"Control error: {e}")
                return JSONResponse(
                    {"error": str(e)},
                    status_code=500
                )
        
        @app.get("/api/stats")
        async def get_stats(request: Request):
            """Get dashboard statistics"""
            # This would gather system and task statistics
            return JSONResponse({
                "active_tasks": 0,
                "total_downloads": 0,
                "total_uploads": 0,
                "total_speed": 0,
                "cpu_usage": 0,
                "memory_usage": 0,
                "disk_usage": 0,
                "timestamp": datetime.now().isoformat()
            })
        
        @app.get("/api/stream/{task_id}")
        async def stream_task_progress(task_id: str):
            """Server-sent events stream for task progress"""
            return StreamingResponse(
                await self.dashboard_manager.server_sent_events(task_id),
                media_type="text/event-stream"
            )
    
    async def _process_client_message(self, data: Dict, websocket: WebSocket):
        """
        Process incoming client messages
        
        Args:
            data: JSON data from client
            websocket: WebSocket connection
        """
        try:
            msg_type = data.get("type", "")
            
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "get_tasks":
                # Send current task list
                await websocket.send_json({
                    "type": "tasks_list",
                    "tasks": list(self.dashboard_manager.task_updates),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                LOGGER.warning(f"Unknown message type: {msg_type}")
        
        except Exception as e:
            LOGGER.error(f"Message processing error: {e}")
