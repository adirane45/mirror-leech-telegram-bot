"""
FastAPI Endpoints for Enhanced Services
Metrics endpoint, health checks, and API status
Safe Innovation Path - Phase 1

Enhanced by: justadi  
Date: February 5, 2026
"""

from fastapi import FastAPI, Response, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
import time
import sys

from .. import LOGGER
from .config_manager import Config


# This will be integrated with the existing FastAPI app in web_dashboard.py
def add_enhanced_endpoints(app: FastAPI):
    """
    Add enhanced endpoints to existing FastAPI application
    Non-breaking - adds new routes only
    """
    
    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics_endpoint():
        """
        Prometheus metrics endpoint
        Returns metrics in Prometheus text format
        """
        try:
            from .metrics import metrics
            
            if not metrics.is_enabled():
                raise HTTPException(
                    status_code=503,
                    detail="Metrics collection is disabled"
                )
            
            metrics_data = metrics.generate_metrics()
            return Response(
                content=metrics_data,
                media_type=metrics.get_content_type()
            )
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="Metrics module not available"
            )
        except Exception as e:
            LOGGER.error(f"Error generating metrics: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate metrics"
            )
    
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint for monitoring
        Returns overall application health status
        """
        try:
            import psutil
            from .redis_manager import redis_client
            
            # Basic health info
            health_status = {
                "status": "healthy",
                "timestamp": time.time(),
                "version": "3.1.0",
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            }
            
            # System resources
            health_status["resources"] = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
            }
            
            # Service status
            health_status["services"] = {
                "redis": redis_client.is_enabled,
                "celery": getattr(Config, 'ENABLE_CELERY', False),
                "metrics": getattr(Config, 'ENABLE_METRICS', False),
            }
            
            # Determine overall health
            if (health_status["resources"]["cpu_percent"] > 95 or
                health_status["resources"]["memory_percent"] > 95 or
                health_status["resources"]["disk_percent"] > 95):
                health_status["status"] = "degraded"
            
            return JSONResponse(content=health_status)
            
        except Exception as e:
            LOGGER.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": time.time()
                }
            )
    
    @app.get("/api/v1/status")
    async def api_status():
        """
        API status endpoint - returns service versions and capabilities
        """
        try:
            from .redis_manager import redis_client
            
            status = {
                "api_version": "1.0",
                "bot_version": "3.1.0",
                "status": "operational",
                "features": {
                    "redis_caching": redis_client.is_enabled,
                    "celery_tasks": getattr(Config, 'ENABLE_CELERY', False),
                    "metrics": getattr(Config, 'ENABLE_METRICS', False),
                    "graphql": False,  # Phase 3
                    "plugins": False,  # Phase 3
                },
                "limits": {
                    "max_concurrent_downloads": getattr(Config, 'MAX_CONCURRENT_DOWNLOADS', 5),
                    "max_concurrent_uploads": getattr(Config, 'MAX_CONCURRENT_UPLOADS', 3),
                },
                "timestamp": time.time()
            }
            
            # Add Redis stats if enabled
            if redis_client.is_enabled:
                redis_stats = await redis_client.get_stats()
                status["redis"] = redis_stats
            
            return JSONResponse(content=status)
            
        except Exception as e:
            LOGGER.error(f"API status error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v1/services/redis/stats")
    async def redis_stats():
        """Get detailed Redis statistics"""
        try:
            from .redis_manager import redis_client
            
            if not redis_client.is_enabled:
                raise HTTPException(
                    status_code=503,
                    detail="Redis is not enabled"
                )
            
            stats = await redis_client.get_stats()
            return JSONResponse(content=stats)
            
        except HTTPException:
            raise
        except Exception as e:
            LOGGER.error(f"Redis stats error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    LOGGER.info("✅ Enhanced API endpoints added: /metrics, /health, /api/v1/status")
