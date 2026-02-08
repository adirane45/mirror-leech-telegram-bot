"""
Web-Based Dashboard Module - Real-time monitoring interface (REFACTORED)

Provides a lightweight web UI for monitoring downloads, uploads, and tasks.

Refactored structure:
- dashboard_manager.py: WebSocket connection and broadcast management
- dashboard_routes.py: FastAPI endpoints and route setup
- dashboard_html.py: HTML template with embedded CSS/JavaScript
- web_dashboard.py: Main orchestrator (this file)

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
- WebSocket: Real-time bidirectional communication
- Bootstrap 5: Responsive UI framework
- Chart.js: Real-time data visualization

Modified by: AI Refactoring
Date: February 8, 2026
"""

from fastapi import FastAPI
from .dashboard_manager import DashboardManager
from .dashboard_routes import DashboardEndpoints


# Global dashboard manager singleton
_dashboard_manager: DashboardManager = None


def get_dashboard_manager() -> DashboardManager:
    """
    Get the global dashboard manager instance
    
    Returns:
        DashboardManager singleton
    """
    global _dashboard_manager
    if _dashboard_manager is None:
        _dashboard_manager = DashboardManager()
    return _dashboard_manager


async def setup_dashboard(app: FastAPI) -> None:
    """
    Setup dashboard routes on FastAPI app
    
    Args:
        app: FastAPI application instance
        
    Example:
        from fastapi import FastAPI
        from bot.core.web_dashboard import setup_dashboard
        
        app = FastAPI()
        await setup_dashboard(app)
    """
    dashboard_manager = get_dashboard_manager()
    endpoints = DashboardEndpoints(dashboard_manager)
    await endpoints.setup_routes(app)


# Export public API
__all__ = [
    'get_dashboard_manager',
    'setup_dashboard',
    'DashboardManager',
    'DashboardEndpoints',
]
