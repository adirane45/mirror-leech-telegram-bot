"""
Metrics HTTP Server - Serves Prometheus metrics
Using prometheus_client's built-in start_http_server
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

from prometheus_client import start_http_server

from .config_manager import Config
from .. import LOGGER


class MetricsServer:
    """
    Standalone HTTP server for serving Prometheus metrics
    Uses prometheus_client's built-in threaded HTTP server
    """
    
    def __init__(self):
        self._enabled = False
        self._port = None
    
    def start(self):
        """Start metrics HTTP server using prometheus_client"""
        try:
            from .metrics import metrics
            
            port = getattr(Config, 'METRICS_PORT', 9090)
            self._port = port
            
            # Use prometheus_client's built-in HTTP server with custom registry
            # This automatically starts in a daemon thread
            start_http_server(port=port, addr='0.0.0.0', registry=metrics._registry)
            
            self._enabled = True
            LOGGER.info(f"✅ Metrics HTTP server started on port {port}")
            LOGGER.info(f"   Access metrics at http://localhost:{port}/metrics")
            
        except OSError as e:
            if "Address already in use" in str(e):
                LOGGER.warning(f"Port {port} already in use")
            else:
                LOGGER.error(f"Failed to start metrics server: {e}")
            self._enabled = False
        except Exception as e:
            LOGGER.error(f"Metrics server error: {e}", exc_info=True)
            self._enabled = False
    
    def is_running(self) -> bool:
        """Check if server is running"""
        return self._enabled


# Global instance
metrics_server = MetricsServer()
