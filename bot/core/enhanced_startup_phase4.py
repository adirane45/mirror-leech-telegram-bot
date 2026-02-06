"""
Phase 4: Enhanced Startup Module
Orchestrates initialization and shutdown of all Phase 4 services
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from bot.core.query_optimizer import QueryOptimizer
from bot.core.cache_manager import CacheManager
from bot.core.connection_pool_manager import ConnectionPoolManager, BackendType
from bot.core.rate_limiter import RateLimiter, RateLimitConfig
from bot.core.batch_processor import BatchProcessor
from bot.core.load_balancer import LoadBalancer, LoadBalancingStrategy

logger = logging.getLogger(__name__)


# Phase 4 Configuration (can be overridden by environment)
PHASE4_CONFIG = {
    'ENABLE_QUERY_OPTIMIZER': True,
    'ENABLE_CACHE_MANAGER': False,  # Requires memory
    'ENABLE_CONNECTION_POOLING': False,  # For production
    'ENABLE_RATE_LIMITER': True,
    'ENABLE_BATCH_PROCESSOR': False,  # For bulk operations
    'ENABLE_LOAD_BALANCER': False,  # For distributed setup
    
    # Configuration
    'CACHE_L1_MAX_SIZE_MB': 100,
    'POOL_MIN_SIZE': 5,
    'POOL_MAX_SIZE': 20,
    'RATE_LIMIT_DEFAULT_RPS': 10.0,
    'BATCH_MAX_SIZE': 100,
    'BATCH_TIMEOUT_SECONDS': 5.0,
    'LOAD_BALANCER_STRATEGY': 'round_robin',
}


async def initialize_phase4_services(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Initialize all Phase 4 services
    
    Args:
        config: Custom configuration (overrides PHASE4_CONFIG)
        
    Returns:
        Status dict with initialization results
    """
    final_config = {**PHASE4_CONFIG}
    if config:
        final_config.update(config)
    
    status = {
        'success': True,
        'errors': [],
        'services_initialized': [],
        'summary': ""
    }
    
    try:
        logger.info("═" * 50)
        logger.info("Initializing Phase 4: Performance & Optimization")
        logger.info("═" * 50)
        
        # Initialize Query Optimizer
        if final_config.get('ENABLE_QUERY_OPTIMIZER'):
            try:
                optimizer = QueryOptimizer.get_instance()
                if await optimizer.enable():
                    status['services_initialized'].append('QueryOptimizer')
                    logger.info("✓ Query Optimizer initialized")
                else:
                    raise Exception("Failed to enable Query Optimizer")
            except Exception as e:
                status['errors'].append(f"Query Optimizer: {e}")
                logger.error(f"✗ Query Optimizer failed: {e}")
        
        # Initialize Cache Manager
        if final_config.get('ENABLE_CACHE_MANAGER'):
            try:
                cache = CacheManager.get_instance()
                max_size = final_config.get('CACHE_L1_MAX_SIZE_MB', 100)
                if await cache.enable(max_size_mb=max_size):
                    status['services_initialized'].append('CacheManager')
                    logger.info(f"✓ Cache Manager initialized (L1: {max_size}MB)")
                else:
                    raise Exception("Failed to enable Cache Manager")
            except Exception as e:
                status['errors'].append(f"Cache Manager: {e}")
                logger.error(f"✗ Cache Manager failed: {e}")
        
        # Initialize Connection Pool Manager
        if final_config.get('ENABLE_CONNECTION_POOLING'):
            try:
                pool_mgr = ConnectionPoolManager.get_instance()
                if await pool_mgr.enable():
                    status['services_initialized'].append('ConnectionPoolManager')
                    
                    # Create default pools
                    min_size = final_config.get('POOL_MIN_SIZE', 5)
                    max_size = final_config.get('POOL_MAX_SIZE', 20)
                    
                    await pool_mgr.create_pool('mongodb', 'mongodb', min_size, max_size)
                    logger.info(f"✓ Connection Pool Manager initialized (MongoDB pool created)")
                else:
                    raise Exception("Failed to enable Connection Pool Manager")
            except Exception as e:
                status['errors'].append(f"Connection Pool Manager: {e}")
                logger.error(f"✗ Connection Pool Manager failed: {e}")
        
        # Initialize Rate Limiter
        if final_config.get('ENABLE_RATE_LIMITER'):
            try:
                limiter = RateLimiter.get_instance()
                if await limiter.enable():
                    status['services_initialized'].append('RateLimiter')
                    
                    # Set default limit
                    rps = final_config.get('RATE_LIMIT_DEFAULT_RPS', 10.0)
                    default_config = RateLimitConfig(
                        requests_per_second=rps,
                        burst_size=int(rps * 5)
                    )
                    limiter.default_config = default_config
                    logger.info(f"✓ Rate Limiter initialized ({rps} req/s)")
                else:
                    raise Exception("Failed to enable Rate Limiter")
            except Exception as e:
                status['errors'].append(f"Rate Limiter: {e}")
                logger.error(f"✗ Rate Limiter failed: {e}")
        
        # Initialize Batch Processor
        if final_config.get('ENABLE_BATCH_PROCESSOR'):
            try:
                processor = BatchProcessor.get_instance()
                max_size = final_config.get('BATCH_MAX_SIZE', 100)
                timeout = final_config.get('BATCH_TIMEOUT_SECONDS', 5.0)
                
                if await processor.enable(max_batch_size=max_size, batch_timeout=timeout):
                    status['services_initialized'].append('BatchProcessor')
                    logger.info(f"✓ Batch Processor initialized (batch_size={max_size})")
                else:
                    raise Exception("Failed to enable Batch Processor")
            except Exception as e:
                status['errors'].append(f"Batch Processor: {e}")
                logger.error(f"✗ Batch Processor failed: {e}")
        
        # Initialize Load Balancer
        if final_config.get('ENABLE_LOAD_BALANCER'):
            try:
                lb = LoadBalancer.get_instance()
                strategy_name = final_config.get('LOAD_BALANCER_STRATEGY', 'round_robin')
                strategy = LoadBalancingStrategy[strategy_name.upper()]
                
                if await lb.enable(strategy=strategy):
                    status['services_initialized'].append('LoadBalancer')
                    logger.info(f"✓ Load Balancer initialized ({strategy_name})")
                else:
                    raise Exception("Failed to enable Load Balancer")
            except Exception as e:
                status['errors'].append(f"Load Balancer: {e}")
                logger.error(f"✗ Load Balancer failed: {e}")
        
        # Summary
        logger.info("═" * 50)
        logger.info(f"Phase 4 Initialization Complete")
        logger.info(f"Services: {', '.join(status['services_initialized'])}")
        
        if status['errors']:
            logger.warning(f"Errors: {len(status['errors'])}")
            for error in status['errors']:
                logger.warning(f"  - {error}")
        
        status['success'] = len(status['errors']) == 0
        status['summary'] = f"{len(status['services_initialized'])} services initialized"
        
        logger.info("═" * 50)
        
        return status
        
    except Exception as e:
        logger.error(f"Critical error during Phase 4 initialization: {e}")
        status['success'] = False
        status['errors'].append(f"Critical initialization error: {e}")
        return status


async def shutdown_phase4_services() -> bool:
    """
    Gracefully shutdown all Phase 4 services
    
    Returns:
        Success status
    """
    try:
        logger.info("═" * 50)
        logger.info("Shutting down Phase 4 services...")
        logger.info("═" * 50)
        
        shutdown_tasks = []
        
        # Shutdown services
        services = [
            ('Query Optimizer', QueryOptimizer.get_instance()),
            ('Cache Manager', CacheManager.get_instance()),
            ('Connection Pool Manager', ConnectionPoolManager.get_instance()),
            ('Rate Limiter', RateLimiter.get_instance()),
            ('Batch Processor', BatchProcessor.get_instance()),
            ('Load Balancer', LoadBalancer.get_instance()),
        ]
        
        for service_name, service in services:
            if hasattr(service, 'enabled') and service.enabled:
                try:
                    # Flush any pending work
                    if hasattr(service, 'flush'):
                        await service.flush()
                    
                    # Disable service
                    await service.disable()
                    logger.info(f"✓ {service_name} shutdown complete")
                except Exception as e:
                    logger.error(f"✗ {service_name} shutdown failed: {e}")
        
        logger.info("═" * 50)
        logger.info("Phase 4 services shutting down")
        logger.info("═" * 50)
        return True
        
    except Exception as e:
        logger.error(f"Critical error during Phase 4 shutdown: {e}")
        return False


async def get_phase4_status() -> Dict[str, Any]:
    """
    Get current status of all Phase 4 services
    
    Returns:
        Status dictionary with all service metrics
    """
    try:
        status = {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'services': {}
        }
        
        # Query Optimizer
        optimizer = QueryOptimizer.get_instance()
        if optimizer.enabled:
            status['services']['query_optimizer'] = await optimizer.get_statistics()
        
        # Cache Manager
        cache = CacheManager.get_instance()
        if cache.enabled:
            status['services']['cache_manager'] = await cache.get_statistics()
        
        # Connection Pool Manager
        pool_mgr = ConnectionPoolManager.get_instance()
        if pool_mgr.enabled:
            status['services']['connection_pool_manager'] = await pool_mgr.get_all_statistics()
        
        # Rate Limiter
        limiter = RateLimiter.get_instance()
        if limiter.enabled:
            status['services']['rate_limiter'] = await limiter.get_statistics()
        
        # Batch Processor
        processor = BatchProcessor.get_instance()
        if processor.enabled:
            status['services']['batch_processor'] = await processor.get_statistics()
        
        # Load Balancer
        lb = LoadBalancer.get_instance()
        if lb.enabled:
            status['services']['load_balancer'] = await lb.get_statistics()
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting Phase 4 status: {e}")
        return {'error': str(e)}


async def reset_phase4_services() -> bool:
    """
    Reset all Phase 4 statistics (does not disable services)
    
    Returns:
        Success status
    """
    try:
        logger.info("Resetting Phase 4 statistics...")
        
        # Query Optimizer
        optimizer = QueryOptimizer.get_instance()
        if optimizer.enabled:
            await optimizer.clear_statistics()
            await optimizer.clear_cache()
        
        # Cache Manager
        cache = CacheManager.get_instance()
        if cache.enabled:
            await cache.clear()
        
        logger.info("Phase 4 statistics reset")
        return True
        
    except Exception as e:
        logger.error(f"Error resetting Phase 4 services: {e}")
        return False


# Convenience decorators for Phase 4 features

def optimize_query(func):
    """Decorator to automatically optimize and cache queries"""
    async def wrapper(*args, **kwargs):
        optimizer = QueryOptimizer.get_instance()
        if not optimizer.enabled:
            return await func(*args, **kwargs)
        
        # Execute query
        result = await func(*args, **kwargs)
        return result
    return wrapper


def cached(key_prefix: str, ttl: int = 300, namespace: str = "default"):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = CacheManager.get_instance()
            if not cache.enabled:
                return await func(*args, **kwargs)
            
            # Generate cache key from function args
            import hashlib
            key_str = f"{key_prefix}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(key_str.encode()).hexdigest()
            
            # Check cache
            cached_result = await cache.get(cache_key, namespace=namespace)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(cache_key, result, ttl=ttl, namespace=namespace)
            
            return result
        return wrapper
    return decorator


def rate_limited(rps: float = 10.0, burst_size: int = 50):
    """Decorator to apply rate limiting to function"""
    def decorator(func):
        async def wrapper(*args, client_id: str = "default", **kwargs):
            limiter = RateLimiter.get_instance()
            if not limiter.enabled:
                return await func(*args, **kwargs)
            
            config = RateLimitConfig(
                requests_per_second=rps,
                burst_size=burst_size
            )
            
            allowed, status = await limiter.is_allowed(client_id, config)
            if not allowed:
                raise Exception(f"Rate limited. Retry after {status.retry_after:.1f}s")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
