"""
Dashboard HTML Template

Provides the dashboard frontend as an HTML string with embedded CSS and JavaScript.

Features:
- Responsive design for desktop and mobile
- Real-time WebSocket updates
- Task progress visualization
- Interactive controls (pause/resume/cancel)
- Bootstrap 5 styling
- Chart.js for visualizations

Modified by: AI Refactoring
Date: February 8, 2026
"""


def get_dashboard_html() -> str:
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
