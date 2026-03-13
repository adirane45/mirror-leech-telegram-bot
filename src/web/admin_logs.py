"""
Admin Web Interface with Log Streaming

Endpoints:
- GET /admin/logs - Generate auth token and return access URL
- GET /admin/logs/viewer - HTML viewer page
- WebSocket /ws/logs - Real-time log streaming
"""

from logging import getLogger

from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from bot.core.admin_auth import admin_auth_manager
from bot.core.config_manager import Config
from bot.core.log_stream import log_stream_manager

router = APIRouter()
LOGGER = getLogger(__name__)


@router.get("/admin/logs")
async def get_logs_url(admin_id: str = Query(...), client_id: str = Query(None)):
    """
    Generate admin token and log streaming URL

    Query Parameters:
    - admin_id: Admin user ID
    - client_id: Optional client identifier for tracking

    Returns:
    {
        "status": "success",
        "token": "generated_token",
        "url": "https://bot.example.com/admin/logs/viewer?token=...",
        "expires_in_seconds": 600,
        "qr_code": "base64_encoded_qr"
    }
    """
    if not admin_id:
        LOGGER.warning("Log URL request missing admin_id")
        raise HTTPException(status_code=400, detail="admin_id required")

    # Create token
    token = await admin_auth_manager.create_token(admin_id)
    if not token:
        LOGGER.error(f"Failed to create admin token for {admin_id}")
        raise HTTPException(status_code=500, detail="Token creation failed")

    # Build URL
    base_url = getattr(Config, "BASE_URL", "") or "http://localhost"
    base_url = base_url.rstrip("/")
    port = getattr(Config, "BASE_URL_PORT", 8060)
    if "://" in base_url and ":" not in base_url.split("//", 1)[1]:
        base_url = f"{base_url}:{port}"

    viewer_url = f"{base_url}/admin/logs/viewer?token={token}&admin_id={admin_id}"

    LOGGER.info(f"Generated logs URL for admin {admin_id}: {viewer_url[:50]}...")

    return {
        "status": "success",
        "token": token,
        "url": viewer_url,
        "expires_in_seconds": admin_auth_manager.token_ttl_seconds,
        "admin_id": admin_id,
        "message": "Share this URL to view live logs"
    }


@router.get("/admin/logs/viewer", response_class=HTMLResponse)
async def logs_viewer(token: str = Query(...), admin_id: str = Query(...)):
    """
    HTML viewer for real-time log streaming

    Query Parameters:
    - token: Admin authentication token
    - admin_id: Admin user ID
    - level: Optional log level filter (ERROR, WARNING, INFO, DEBUG)
    - search: Optional search term
    """
    # Validate token
    is_valid = await admin_auth_manager.validate_token(admin_id, token)
    if not is_valid:
        LOGGER.warning(f"Invalid token for admin {admin_id}")
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    LOGGER.info(f"Admin {admin_id} accessing logs viewer")

    # Return HTML viewer
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mirror-Leech Bot - Live Logs</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Monaco', 'Courier New', monospace;
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 20px;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #444;
            }}
            .header h1 {{
                font-size: 24px;
                color: #4ec9b0;
            }}
            .controls {{
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }}
            .controls select,
            .controls input {{
                padding: 8px 12px;
                background: #252526;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                font-family: inherit;
            }}
            .controls button {{
                padding: 8px 15px;
                background: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-family: inherit;
                transition: background 0.2s;
            }}
            .controls button:hover {{
                background: #1177bb;
            }}
            #terminal {{
                width: 100%;
                height: 600px;
                background: #1e1e1e;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 15px;
                overflow-y: auto;
                white-space: pre-wrap;
                word-break: break-all;
                font-size: 13px;
                line-height: 1.5;
            }}
            .status {{
                margin-top: 10px;
                padding: 10px;
                background: #252526;
                border-radius: 4px;
                font-size: 12px;
                color: #858585;
            }}
            .status.connected {{ color: #4ec9b0; }}
            .status.disconnected {{ color: #f44747; }}
            .error {{ color: #f44747; }}
            .warning {{ color: #dcdcaa; }}
            .info {{ color: #4ec9b0; }}
            .debug {{ color: #858585; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Mirror-Leech Bot - Live Logs</h1>
                <div>
                    <button onclick="copyInfo()">Copy Link</button>
                    <button onclick="clearLogs()">Clear</button>
                    <button onclick="downloadLogs()">Download</button>
                    <button onclick="exitViewer()">Exit</button>
                </div>
            </div>

            <div class="controls">
                <select id="levelFilter" onchange="updateFilter()">
                    <option value="">All Levels</option>
                    <option value="ERROR">ERROR</option>
                    <option value="WARNING">WARNING</option>
                    <option value="INFO">INFO</option>
                    <option value="DEBUG">DEBUG</option>
                </select>

                <input
                    type="text"
                    id="searchInput"
                    placeholder="Search logs..."
                    onkeyup="updateFilter()"
                >

                <button onclick="pauseResume()" id="pauseBtn">Pause</button>
                <button onclick="scrollBottom()">Scroll to Bottom</button>
            </div>

            <div id="terminal">
                <div style="color: #4ec9b0;">Connecting to log stream...</div>
            </div>

            <div class="status disconnected" id="status">
                ● Disconnected
            </div>
        </div>

        <script>
            const token = "{token}";
            const adminId = "{admin_id}";
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = protocol + '//' + window.location.host + '/ws/logs?token=' + token + '&admin_id=' + adminId;

            let ws = null;
            let isPaused = false;
            let allLogs = [];
            let filteredLogs = [];

            function connectWebSocket() {{
                ws = new WebSocket(wsUrl);

                ws.onopen = function() {{
                    console.log('Connected to log stream');
                    document.getElementById('status').textContent = '● Connected';
                    document.getElementById('status').classList.remove('disconnected');
                    document.getElementById('status').classList.add('connected');
                }};

                ws.onmessage = function(event) {{
                    if (isPaused) return;

                    const line = event.data;
                    allLogs.push(line);

                    if (shouldShowLog(line)) {{
                        filteredLogs.push(line);
                        const terminal = document.getElementById('terminal');
                        if (filteredLogs.length === 1) {{
                            terminal.innerHTML = '';
                        }}
                        terminal.innerHTML += line + '<br>';
                        terminal.scrollTop = terminal.scrollHeight;
                    }}

                    if (allLogs.length > 10000) {{
                        allLogs = allLogs.slice(-5000);
                    }}
                }};

                ws.onerror = function(error) {{
                    console.error('WebSocket error:', error);
                    const terminal = document.getElementById('terminal');
                    terminal.innerHTML += '<div class="error">❌ WebSocket Error: ' + error + '</div><br>';
                }};

                ws.onclose = function() {{
                    console.log('Disconnected from log stream');
                    document.getElementById('status').textContent = '● Disconnected (Reconnecting in 3s)';
                    document.getElementById('status').classList.add('disconnected');
                    document.getElementById('status').classList.remove('connected');
                    setTimeout(connectWebSocket, 3000);
                }};
            }}

            function shouldShowLog(line) {{
                const level = document.getElementById('levelFilter').value;
                const search = document.getElementById('searchInput').value.toLowerCase();

                line = line.toLowerCase();

                if (level && !line.includes(level.toLowerCase())) {{
                    return false;
                }}
                if (search && !line.includes(search)) {{
                    return false;
                }}
                return true;
            }}

            function updateFilter() {{
                const terminal = document.getElementById('terminal');
                terminal.innerHTML = '';
                filteredLogs = [];

                allLogs.forEach(line => {{
                    if (shouldShowLog(line)) {{
                        filteredLogs.push(line);
                        terminal.innerHTML += line + '<br>';
                    }}
                }});

                terminal.scrollTop = terminal.scrollHeight;
            }}

            function pauseResume() {{
                isPaused = !isPaused;
                document.getElementById('pauseBtn').textContent = isPaused ? 'Resume' : 'Pause';
            }}

            function scrollBottom() {{
                document.getElementById('terminal').scrollTop = document.getElementById('terminal').scrollHeight;
            }}

            function clearLogs() {{
                allLogs = [];
                filteredLogs = [];
                document.getElementById('terminal').innerHTML = '<div style="color: #858585;">Logs cleared. Waiting for new entries...</div><br>';
            }}

            function downloadLogs() {{
                const logsText = allLogs.join('\\n');
                const element = document.createElement('a');
                element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(logsText));
                element.setAttribute('download', 'bot-logs-' + new Date().toISOString().slice(0, 10) + '.txt');
                element.style.display = 'none';
                document.body.appendChild(element);
                element.click();
                document.body.removeChild(element);
            }}

            function copyInfo() {{
                const text = window.location.href;
                navigator.clipboard.writeText(text).then(() => {{
                    alert('Link copied to clipboard!');
                }});
            }}

            function exitViewer() {{
                if (confirm('Close log viewer?')) {{
                    window.close();
                }}
            }}

            // Start
            connectWebSocket();
        </script>
    </body>
    </html>
    """

    return html_content


@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket, token: str = Query(...), admin_id: str = Query(...)):
    """
    WebSocket endpoint for real-time log streaming

    Query Parameters:
    - token: Admin authentication token
    - admin_id: Admin user ID
    """
    # Validate token
    is_valid = await admin_auth_manager.validate_token(admin_id, token)
    if not is_valid:
        LOGGER.warning(f"Invalid WebSocket token for admin {admin_id}")
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    # Add connection
    success = await log_stream_manager.add_connection(websocket)
    if not success:
        LOGGER.warning("Failed to add log stream connection")
        await websocket.close(code=1008, reason="Server at capacity")
        return

    LOGGER.info(f"WebSocket connected for admin {admin_id}")

    try:
        # Get filter parameters from first message
        level = None
        search = None

        # Stream logs
        await log_stream_manager.stream_logs(websocket, level=level, search=search)

    except WebSocketDisconnect:
        LOGGER.info(f"WebSocket disconnected for admin {admin_id}")
        await log_stream_manager.remove_connection(websocket)

    except Exception as e:
        LOGGER.error(f"WebSocket error for admin {admin_id}: {e}")
        await log_stream_manager.remove_connection(websocket)


def add_admin_routes(app):
    """Add admin routes to FastAPI app"""
    app.include_router(router)
