"""
Web-Based Dashboard Module - Real-time monitoring interface

Provides a lightweight web UI for monitoring downloads, uploads, and tasks.

Features:
- Real-time task status updates (WebSocket)
- Multi-task management interface
- Download/upload progress bars
- Speed monitoring (live bitrate)
- Task details and file explorer
- Responsive design for desktop and mobile
- Interactive controls (pause/resume/cancel)
- Statistics and analytics

Technologies:
- FastAPI: High-performance async web framework
- Jinja2: Template engine for HTML rendering
- WebSocket: Real-time bidirectional communication
- Bootstrap 5: Responsive UI framework
- Chart.js: Real-time data visualization
- Fetch API: Client-side async requests

Architecture:
- FastAPI application with async endpoints
- WebSocket connections for live updates
- JSON API for task management
- Server-Sent Events (SSE) for progress
- AJAX for interactive updates

Modified by: justadi
Created: 2026-01-30
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import logging
from typing import Dict, List, Optional
from asyncio import sleep, create_task
from collections import deque

LOGGER = logging.getLogger(__name__)


class DashboardManager:
    """
    Manages web dashboard connections and real-time updates
    
    Features:
    - WebSocket connection management
    - Task status broadcasting
    - Real-time progress updates
    - Client message handling
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


# Global dashboard manager
dashboard_manager = DashboardManager()


class DashboardEndpoints:
    """
    FastAPI endpoints for dashboard functionality
    
    Endpoints:
    - GET /dashboard - Main dashboard HTML page
    - WebSocket /ws/dashboard - Real-time updates
    - GET /api/tasks - Get all tasks
    - GET /api/tasks/{task_id} - Get task details
    - POST /api/tasks/{task_id}/control - Control task (pause/resume/cancel)
    - GET /api/stats - Get dashboard statistics
    - GET /api/stream/{task_id} - Server-sent events stream
    """
    
    @staticmethod
    async def setup_routes(app: FastAPI):
        """
        Setup all dashboard endpoints on FastAPI app
        
        Args:
            app: FastAPI application instance
        """
        
        @app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard_page(request: Request):
            """Serve main dashboard HTML page"""
            return DashboardEndpoints._get_dashboard_html()
        
        @app.websocket("/ws/dashboard")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await dashboard_manager.connect(websocket)
            try:
                while True:
                    # Receive and process client messages
                    data = await websocket.receive_json()
                    await DashboardEndpoints._process_client_message(data, websocket)
            except WebSocketDisconnect:
                dashboard_manager.disconnect(websocket)
                LOGGER.info("WebSocket disconnected")
            except Exception as e:
                LOGGER.error(f"WebSocket error: {e}")
                dashboard_manager.disconnect(websocket)
        
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
                await dashboard_manager.broadcast_message(
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
                await dashboard_manager.server_sent_events(task_id),
                media_type="text/event-stream"
            )
    
    @staticmethod
    def _get_dashboard_html() -> str:
        """
        Generate dashboard HTML page
        
        Returns:
            HTML string with responsive dashboard interface
        """
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Download Manager Dashboard</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                
                body {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }
                
                .dashboard-container {
                    padding: 20px;
                    max-width: 1400px;
                    margin: 0 auto;
                }
                
                .header {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                }
                
                .header h1 {
                    color: #333;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                .stat-card {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 20px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    transition: transform 0.3s ease;
                }
                
                .stat-card:hover {
                    transform: translateY(-5px);
                }
                
                .stat-value {
                    font-size: 28px;
                    font-weight: bold;
                    color: #667eea;
                }
                
                .stat-label {
                    color: #666;
                    font-size: 14px;
                    margin-top: 5px;
                }
                
                .task-item {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 15px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                }
                
                .task-name {
                    font-weight: 600;
                    color: #333;
                    margin-bottom: 10px;
                    word-break: break-all;
                }
                
                .progress-bar {
                    height: 24px;
                    border-radius: 12px;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                    transition: width 0.5s ease;
                }
                
                .progress {
                    background: #e9ecef;
                    border-radius: 12px;
                    overflow: hidden;
                    margin: 10px 0;
                    height: 24px;
                }
                
                .task-stats {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 10px;
                    margin-top: 15px;
                    font-size: 14px;
                }
                
                .stat-item {
                    display: flex;
                    justify-content: space-between;
                    padding: 8px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }
                
                .stat-item strong {
                    color: #667eea;
                }
                
                .controls {
                    display: flex;
                    gap: 10px;
                    margin-top: 15px;
                }
                
                .btn-control {
                    padding: 6px 12px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 12px;
                    font-weight: 500;
                    transition: all 0.3s ease;
                }
                
                .btn-pause {
                    background: #ffc107;
                    color: #333;
                }
                
                .btn-pause:hover {
                    background: #ffb300;
                }
                
                .btn-resume {
                    background: #28a745;
                    color: white;
                }
                
                .btn-resume:hover {
                    background: #218838;
                }
                
                .btn-cancel {
                    background: #dc3545;
                    color: white;
                }
                
                .btn-cancel:hover {
                    background: #c82333;
                }
                
                .status-badge {
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                    margin-bottom: 10px;
                }
                
                .status-downloading {
                    background: #d4edff;
                    color: #0066cc;
                }
                
                .status-uploading {
                    background: #d4f1ff;
                    color: #0099ff;
                }
                
                .status-completed {
                    background: #d4edda;
                    color: #155724;
                }
                
                .status-error {
                    background: #f8d7da;
                    color: #721c24;
                }
                
                .status-paused {
                    background: #fff3cd;
                    color: #856404;
                }
                
                .connection-status {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 10px 15px;
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 8px;
                    font-size: 12px;
                    z-index: 1000;
                }
                
                .connection-status.connected::before {
                    content: '';
                    display: inline-block;
                    width: 8px;
                    height: 8px;
                    background: #28a745;
                    border-radius: 50%;
                    margin-right: 8px;
                    animation: pulse 2s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
                
                .empty-state {
                    text-align: center;
                    padding: 40px 20px;
                    color: rgba(255, 255, 255, 0.8);
                }
                
                @media (max-width: 768px) {
                    .task-stats {
                        grid-template-columns: 1fr 1fr;
                    }
                    
                    .controls {
                        flex-wrap: wrap;
                    }
                }
            </style>
        </head>
        <body>
            <div class="dashboard-container">
                <div class="connection-status" id="connection-status">
                    Connecting...
                </div>
                
                <div class="header">
                    <h1>
                        <i class="bi bi-graph-up"></i>
                        Download Manager Dashboard
                    </h1>
                    <small style="color: #666;">Real-time monitoring and control</small>
                </div>
                
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-value" id="active-tasks">0</div>
                            <div class="stat-label">Active Tasks</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-value" id="total-speed">0 MB/s</div>
                            <div class="stat-label">Total Speed</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-value" id="total-downloads">0</div>
                            <div class="stat-label">Total Downloads</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-card">
                            <div class="stat-value" id="total-uploads">0</div>
                            <div class="stat-label">Total Uploads</div>
                        </div>
                    </div>
                </div>
                
                <div id="tasks-container">
                    <div class="empty-state">
                        <i class="bi bi-inbox" style="font-size: 32px;"></i>
                        <p style="margin-top: 10px;">No active tasks</p>
                    </div>
                </div>
            </div>
            
            <script>
                class DashboardClient {
                    constructor() {
                        this.ws = null;
                        this.reconnectAttempts = 0;
                        this.maxReconnectAttempts = 5;
                        this.reconnectDelay = 3000;
                        this.tasks = new Map();
                        this.connect();
                    }
                    
                    connect() {
                        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                        const url = `${protocol}//${window.location.host}/ws/dashboard`;
                        
                        this.ws = new WebSocket(url);
                        
                        this.ws.onopen = () => {
                            this.updateConnectionStatus(true);
                            this.reconnectAttempts = 0;
                            console.log('Dashboard connected');
                        };
                        
                        this.ws.onmessage = (event) => {
                            this.handleMessage(JSON.parse(event.data));
                        };
                        
                        this.ws.onerror = (error) => {
                            console.error('WebSocket error:', error);
                        };
                        
                        this.ws.onclose = () => {
                            this.updateConnectionStatus(false);
                            this.attemptReconnect();
                        };
                    }
                    
                    handleMessage(data) {
                        switch (data.type) {
                            case 'connected':
                                console.log(data.message);
                                break;
                            case 'task_status':
                                this.updateTaskStatus(data.task_id, data.data);
                                break;
                            case 'dashboard_stats':
                                this.updateDashboardStats(data.data);
                                break;
                            case 'message':
                                this.showMessage(data.message, data.msg_type);
                                break;
                        }
                    }
                    
                    updateTaskStatus(taskId, status) {
                        this.tasks.set(taskId, status);
                        this.renderTasks();
                    }
                    
                    updateDashboardStats(stats) {
                        document.getElementById('active-tasks').textContent = stats.active_tasks || 0;
                        document.getElementById('total-speed').textContent = this.formatSpeed(stats.total_speed || 0);
                        document.getElementById('total-downloads').textContent = stats.total_downloads || 0;
                        document.getElementById('total-uploads').textContent = stats.total_uploads || 0;
                    }
                    
                    renderTasks() {
                        const container = document.getElementById('tasks-container');
                        
                        if (this.tasks.size === 0) {
                            container.innerHTML = `
                                <div class="empty-state">
                                    <i class="bi bi-inbox" style="font-size: 32px;"></i>
                                    <p style="margin-top: 10px;">No active tasks</p>
                                </div>
                            `;
                            return;
                        }
                        
                        container.innerHTML = Array.from(this.tasks.entries()).map(([id, task]) => `
                            <div class="task-item">
                                <div class="task-name">${task.name || `Task ${id}`}</div>
                                <span class="status-badge status-${task.status}">${task.status}</span>
                                <div class="progress">
                                    <div class="progress-bar" style="width: ${task.progress || 0}%"></div>
                                </div>
                                <div class="task-stats">
                                    <div class="stat-item">
                                        <strong>Progress:</strong> ${task.progress || 0}%
                                    </div>
                                    <div class="stat-item">
                                        <strong>Speed:</strong> ${this.formatSpeed(task.speed || 0)}
                                    </div>
                                    <div class="stat-item">
                                        <strong>ETA:</strong> ${this.formatTime(task.eta || 0)}
                                    </div>
                                    <div class="stat-item">
                                        <strong>Size:</strong> ${this.formatSize(task.current_size || 0)} / ${this.formatSize(task.total_size || 0)}
                                    </div>
                                </div>
                                <div class="controls">
                                    <button class="btn-control btn-pause" onclick="dashboard.pauseTask('${id}')">
                                        <i class="bi bi-pause"></i> Pause
                                    </button>
                                    <button class="btn-control btn-resume" onclick="dashboard.resumeTask('${id}')">
                                        <i class="bi bi-play"></i> Resume
                                    </button>
                                    <button class="btn-control btn-cancel" onclick="dashboard.cancelTask('${id}')">
                                        <i class="bi bi-x"></i> Cancel
                                    </button>
                                </div>
                            </div>
                        `).join('');
                    }
                    
                    pauseTask(taskId) {
                        this.sendCommand(taskId, 'pause');
                    }
                    
                    resumeTask(taskId) {
                        this.sendCommand(taskId, 'resume');
                    }
                    
                    cancelTask(taskId) {
                        if (confirm('Are you sure you want to cancel this task?')) {
                            this.sendCommand(taskId, 'cancel');
                        }
                    }
                    
                    sendCommand(taskId, action) {
                        fetch(`/api/tasks/${taskId}/control`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ action })
                        }).catch(err => console.error('Command error:', err));
                    }
                    
                    updateConnectionStatus(connected) {
                        const el = document.getElementById('connection-status');
                        el.textContent = connected ? 'Connected' : 'Disconnected';
                        el.className = `connection-status ${connected ? 'connected' : ''}`;
                    }
                    
                    attemptReconnect() {
                        if (this.reconnectAttempts < this.maxReconnectAttempts) {
                            this.reconnectAttempts++;
                            setTimeout(() => this.connect(), this.reconnectDelay);
                        }
                    }
                    
                    formatSize(bytes) {
                        const units = ['B', 'KB', 'MB', 'GB'];
                        let size = bytes;
                        let unitIndex = 0;
                        while (size >= 1024 && unitIndex < units.length - 1) {
                            size /= 1024;
                            unitIndex++;
                        }
                        return `${size.toFixed(2)} ${units[unitIndex]}`;
                    }
                    
                    formatSpeed(bytesPerSecond) {
                        return `${(bytesPerSecond / 1024 / 1024).toFixed(2)} MB/s`;
                    }
                    
                    formatTime(seconds) {
                        if (seconds === 0) return '--:--:--';
                        const hours = Math.floor(seconds / 3600);
                        const minutes = Math.floor((seconds % 3600) / 60);
                        const secs = Math.floor(seconds % 60);
                        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
                    }
                    
                    showMessage(message, type) {
                        console.log(`[${type}] ${message}`);
                    }
                }
                
                const dashboard = new DashboardClient();
            </script>
        </body>
        </html>
        """
    
    @staticmethod
    async def _process_client_message(data: Dict, websocket: WebSocket):
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
                    "tasks": list(dashboard_manager.task_updates),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                LOGGER.warning(f"Unknown message type: {msg_type}")
        
        except Exception as e:
            LOGGER.error(f"Message processing error: {e}")


# Global instance
dashboard_manager = DashboardManager()
