"""
Advanced Dashboard HTML Template

Provides the dashboard frontend with embedded HTML, CSS, and JavaScript.

Features:
- Real-time metrics visualization
- Dark theme with cyan accents
- Live WebSocket updates
- System statistics cards
- Log stream monitoring

Modified by: AI Refactoring
Date: February 8, 2026
"""


def get_advanced_dashboard_html() -> str:
    """
    Generate advanced dashboard HTML
    
    Returns:
        HTML string with dashboard interface
    """
    return """
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
