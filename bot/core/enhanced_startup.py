"""
Enhanced Startup Module - Integrates new services safely
Backward compatible with existing functionality
Safe Innovation Path - Phase 1

Enhanced by: justadi
Date: February 5, 2026
"""

from .. import LOGGER
from .config_manager import Config


async def initialize_enhanced_services():
    """
    Initialize all enhanced services (Redis, Celery, Metrics)
    All services are optional and gracefully degrade if unavailable
    """
    services_status = {
        "redis": False,
        "celery": False,
        "metrics": False,
    }
    
    # Initialize Redis
    if getattr(Config, 'ENABLE_REDIS_CACHE', False):
        try:
            from .redis_manager import redis_client
            success = await redis_client.initialize(
                host=getattr(Config, 'REDIS_HOST', 'redis'),
                port=getattr(Config, 'REDIS_PORT', 6379),
                db=getattr(Config, 'REDIS_DB', 0)
            )
            services_status["redis"] = success
            if success:
                LOGGER.info("✅ Redis caching enabled")
            else:
                LOGGER.info("⚠️ Redis disabled - using fallback mode")
        except Exception as e:
            LOGGER.warning(f"Redis initialization failed: {e}")
            LOGGER.info("Continuing without Redis caching")
    else:
        LOGGER.info("Redis caching is disabled in config")
    
    # Initialize Celery (if enabled)
    if getattr(Config, 'ENABLE_CELERY', False):
        try:
            from .celery_app import celery_app
            # Test Celery connection
            celery_app.control.ping(timeout=1)
            services_status["celery"] = True
            LOGGER.info("✅ Celery task queue enabled")
        except Exception as e:
            LOGGER.warning(f"Celery initialization failed: {e}")
            LOGGER.info("Continuing without Celery (synchronous mode)")
    else:
        LOGGER.info("Celery is disabled in config")
    
    # Initialize Metrics
    if getattr(Config, 'ENABLE_METRICS', False):
        try:
            from .metrics import metrics
            metrics.enable()
            services_status["metrics"] = metrics.is_enabled()
            if metrics.is_enabled():
                LOGGER.info("✅ Prometheus metrics enabled")
        except Exception as e:
            LOGGER.warning(f"Metrics initialization failed: {e}")
            LOGGER.info("Continuing without metrics")
    else:
        LOGGER.info("Metrics collection is disabled in config")
    
    # Print summary
    LOGGER.info("="*50)
    LOGGER.info("📊 Enhanced Services Status:")
    LOGGER.info(f"  • Redis Caching: {'✅ Enabled' if services_status['redis'] else '❌ Disabled'}")
    LOGGER.info(f"  • Celery Queue: {'✅ Enabled' if services_status['celery'] else '❌ Disabled'}")
    LOGGER.info(f"  • Metrics: {'✅ Enabled' if services_status['metrics'] else '❌ Disabled'}")
    LOGGER.info("="*50)
    
    return services_status


async def shutdown_enhanced_services():
    """
    Gracefully shutdown all enhanced services
    """
    LOGGER.info("Shutting down enhanced services...")
    
    # Shutdown Redis
    try:
        from .redis_manager import redis_client
        if redis_client.is_enabled:
            await redis_client.close()
            LOGGER.info("✅ Redis connection closed")
    except Exception as e:
        LOGGER.debug(f"Redis shutdown: {e}")
    
    # Celery cleanup is handled by the worker itself
    
    LOGGER.info("Enhanced services shutdown complete")
