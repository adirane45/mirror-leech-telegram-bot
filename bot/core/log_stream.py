"""
WebSocket Log Streaming for Real-Time Admin Dashboard

Implements:
- WebSocket server for log streaming
- ANSI color code parsing
- Log filtering and searching
- Connection management
"""

import asyncio
import re
from datetime import datetime, timezone
from typing import Optional, Set, Callable

from fastapi import WebSocket
import aiofiles
import aiofiles.os

from .. import LOGGER
from .config_manager import Config


class LogStreamManager:
    """Manage real-time log streaming via WebSocket"""
    
    def __init__(self) -> None:
        self.enabled = bool(getattr(Config, "ENABLE_LOG_STREAMING", True))
        self.log_file_path = getattr(Config, "LOG_FILE_PATH", "data/logs/log.txt")
        self.max_connections = int(getattr(Config, "MAX_LOG_STREAM_CONNECTIONS", 5))
        self.buffer_size = int(getattr(Config, "LOG_STREAM_BUFFER_SIZE", 10000))  # lines
        self.poll_interval = float(getattr(Config, "LOG_STREAM_POLL_INTERVAL", 0.5))
        
        self.active_connections: Set[WebSocket] = set()
        self.tail_position: int = 0
        self.log_buffer: list = []
        self.last_read_time: Optional[float] = None
    
    async def start(self) -> bool:
        """Start log streaming service"""
        if not self.enabled:
            LOGGER.warning("Log streaming is disabled")
            return False
        
        # Check if log file exists
        try:
            exists = await aiofiles.os.path.exists(self.log_file_path)
            if not exists:
                # Create empty log file
                async with aiofiles.open(self.log_file_path, 'w') as f:
                    await f.write("")
                LOGGER.info(f"Created log file: {self.log_file_path}")
        except Exception as e:
            LOGGER.error(f"Failed to initialize log file: {e}")
            return False
        
        LOGGER.info("Log streaming service started")
        return True
    
    async def stop(self) -> bool:
        """Stop log streaming service"""
        # Close all connections
        for connection in list(self.active_connections):
            try:
                await connection.close()
            except Exception:
                pass
        
        self.active_connections.clear()
        LOGGER.info("Log streaming service stopped")
        return True
    
    async def add_connection(self, websocket: WebSocket) -> bool:
        """Add a new WebSocket connection"""
        if not self.enabled:
            return False
        
        if len(self.active_connections) >= self.max_connections:
            LOGGER.warning(f"Max log stream connections reached ({self.max_connections})")
            return False
        
        try:
            await websocket.accept()
            self.active_connections.add(websocket)
            LOGGER.info(f"Log stream connection added. Active: {len(self.active_connections)}")
            return True
        except Exception as e:
            LOGGER.error(f"Failed to accept WebSocket: {e}")
            return False
    
    async def remove_connection(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            LOGGER.info(f"Log stream connection removed. Active: {len(self.active_connections)}")
        
        try:
            await websocket.close()
        except Exception:
            pass
    
    async def read_logs(self, lines: Optional[int] = None) -> list:
        """Read logs from file"""
        try:
            if not await aiofiles.os.path.exists(self.log_file_path):
                return []
            
            async with aiofiles.open(self.log_file_path, 'r') as f:
                if lines:
                    # Read last N lines
                    all_lines = await f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
                else:
                    # Read all
                    return await f.readlines()
        except Exception as e:
            LOGGER.error(f"Failed to read logs: {e}")
            return []
    
    def _ansi_to_html(self, text: str) -> str:
        """Convert ANSI color codes to HTML"""
        # ANSI to HTML color mapping
        ansi_colors = {
            '30': '#000000',  # Black
            '31': '#FF0000',  # Red
            '32': '#00FF00',  # Green
            '33': '#FFFF00',  # Yellow
            '34': '#0000FF',  # Blue
            '35': '#FF00FF',  # Magenta
            '36': '#00FFFF',  # Cyan
            '37': '#FFFFFF',  # White
        }
        
        # Replace ANSI color codes with HTML spans
        def replace_ansi(match):
            code = match.group(1)
            if code in ansi_colors:
                return f'<span style="color: {ansi_colors[code]}">'
            elif code == '0':
                return '</span>'
            return ''
        
        # Remove ANSI codes and convert colors
        text = re.sub(r'\x1b\[([0-9;]+)m', replace_ansi, text)
        text = re.sub(r'\x1b\[0m', '</span>', text)
        
        return text
    
    def _filter_logs(self, logs: list, level: Optional[str] = None) -> list:
        """Filter logs by level (ERROR, WARNING, DEBUG, INFO)"""
        if not level:
            return logs
        
        level = level.upper()
        filtered = [log for log in logs if level in log.upper()]
        return filtered
    
    async def stream_logs(
        self,
        websocket: WebSocket,
        level: Optional[str] = None,
        search: Optional[str] = None,
    ) -> None:
        """Stream logs to WebSocket"""
        try:
            # Send initial buffer
            logs = await self.read_logs(lines=100)
            if level:
                logs = self._filter_logs(logs, level)
            if search:
                logs = [log for log in logs if search.lower() in log.lower()]
            
            for log in logs:
                html_log = self._ansi_to_html(log.strip())
                await websocket.send_text(f"[INITIAL] {html_log}\n")
            
            # Stream new logs
            last_position = 0
            while websocket in self.active_connections:
                try:
                    # Read new logs
                    logs = await self.read_logs()
                    new_logs = logs[last_position:]
                    
                    for log in new_logs:
                        if level and level.upper() not in log.upper():
                            continue
                        if search and search.lower() not in log.lower():
                            continue
                        
                        html_log = self._ansi_to_html(log.strip())
                        await websocket.send_text(f"[STREAM] {html_log}\n")
                    
                    last_position = len(logs)
                    await asyncio.sleep(self.poll_interval)
                    
                except Exception as e:
                    LOGGER.error(f"Error streaming logs: {e}")
                    await websocket.send_text(f"[ERROR] Log streaming interrupted: {e}\n")
                    break
        
        except Exception as e:
            LOGGER.error(f"WebSocket error: {e}")
        
        finally:
            await self.remove_connection(websocket)


# Global instance
log_stream_manager = LogStreamManager()
