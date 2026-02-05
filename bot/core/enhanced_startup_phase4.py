"""
Phase 4 Startup and Initialization

Safely initializes all Performance & Optimization services:
- Query Optimizer
- Cache Manager
- Connection Pool Manager
- Rate Limiter
- Batch Processor
- Load Balancer

All services are optional and disabled by default. Enable only what you need.
"""

import asyncio
from typing import Dict, Any, Optional

# Service imports (will be imported conditionally)
phase4_services = {}


async def initialize_phase4_services() -> Dict[str, Any]:
    """
    Initialize Phase 4 services safely
    
    Returns:
        Dictionary with initialization status of each service
    """
    status = {
        'phase': 4,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
        'services': {},
        'errors': [],
        'success': True
    }
    
    try:
        # Import config
        from config_enhancements_phase4 import (
            ENABLE_QUERY_OPTIMIZER,
            ENABLE_CACHE_MANAGER,
            ENABLE_CONNECTION_POOLING,
            ENABLE_RATE_LIMITER,
            ENABLE_BATCH_PROCESSOR,
            ENABLE_LOAD_BALANCER,
            BATCH_MAX_SIZE,
            BATCH_TIMEOUT,
            BATCH_MAX_CONCURRENT,
            LOAD_BALANCING_STRATEGY,
            LOAD_BALANCER_INSTANCES,
        )
        
        # Initialize Query Optimizer (optional)
        if ENABLE_QUERY_OPTIMIZER:
            try:
                from bot.core.query_optimizer import QueryOptimizer
                optimizer = QueryOptimizer.get_instance()
                enabled = await optimizer.enable()
                status['services']['query_optimizer'] = {
                    'enabled': enabled,
                    'status': 'running' if enabled else 'failed'
                }
                if enabled:
                    phase4_services['query_optimizer'] = optimizer
            except Exception as e:
                status['services']['query_optimizer'] = {
                    'enabled': False,
                    'status': 'error',
                    'error': str(e)
                }
                status['errors'].append(f"Query Optimizer: {e}")
        else:
            status['services']['query_optimizer'] = {'enabled': False, 'status': 'disabled'}
        
        # Initialize Cache Manager (optional)
        if ENABLE_CACHE_MANAGER:
            try:
                from bot.core.cache_manager import CacheManager
                cache_mgr = CacheManager.get_instance()
                enabled = await cache_mgr.enable()
                status['services']['cache_manager'] = {
                    'enabled': enabled,
                    'status': 'running' if enabled else 'failed'
                }
                if enabled:
                    phase4_services['cache_manager'] = cache_mgr
            except Exception as e:
                status['services']['cache_manager'] = {
                    'enabled': False,
                    'status': 'error',
                    'error': str(e)
                }
                status['errors'].append(f"Cache Manager: {e}")
        else:
            status['services']['cache_manager'] = {'enabled': False, 'status': 'disabled'}
        
        # Initialize Connection Pool Manager (optional)
        if ENABLE_CONNECTION_POOLING:
            try:
                from bot.core.connection_pool_manager import ConnectionPoolManager
                pool_mgr = ConnectionPoolManager.get_instance()
                enabled = await pool_mgr.enable()
                status['services']['connection_pool_manager'] = {
                    'enabled': enabled,
                    'status': 'running' if enabled else 'failed'
                }
                if enabled:
                    phase4_services['connection_pool_manager'] = pool_mgr
            except Exception as e:
                status['services']['connection_pool_manager'] = {
                    'enabled': False,
                    'status': 'error',
                    'error': str(e)
                }
                status['errors'].append(f"Connection Pool Manager: {e}")
        else:
            status['services']['connection_pool_manager'] = {'enabled': False, 'status': 'disabled'}
        
        # Initialize Rate Limiter (optional)
        if ENABLE_RATE_LIMITER:
            try:
                from bot.core.rate_limiter import RateLimiter
                limiter = RateLimiter.get_instance()
                enabled = await limiter.enable()
                status['services']['rate_limiter'] = {
                    'enabled': enabled,
                    'status': 'running' if enabled else 'failed'
                }
                if enabled:
                    phase4_services['rate_limiter'] = limiter
            except Exception as e:
                status['services']['rate_limiter'] = {
                    'enabled': False,
                    'status': 'error',
                    'error': str(e)
                }
                status['errors'].append(f"Rate Limiter: {e}")
        else:
            status['services']['rate_limiter'] = {'enabled': False, 'status': 'disabled'}
        
        # Initialize Batch Processor (optional)
        if ENABLE_BATCH_PROCESSOR:
            try:
                from bot.core.batch_processor import BatchProcessor
                
                # Define batch handler
                async def default_batch_handler(items):
                    """Default batch handler - process items"""
                    results = {}
                    for item in items:
                        results[item.item_id] = f"processed_{item.item_id}"
                    return results
                
                processor = BatchProcessor.get_instance()
                enabled = await processor.enable(default_batch_handler)
                status['services']['batch_processor'] = {
                    'enabled': enabled,
                    'status': 'running' if enabled else 'failed',
                    'batch_size': BATCH_MAX_SIZE,
                    'timeout': BATCH_TIMEOUT
                }
                if enabled:
                    phase4_services['batch_processor'] = processor
            except Exception as e:
                status['services']['batch_processor'] = {
                    'enabled': False,
                    'status': 'error',
                    'error': str(e)
                }
                status['errors'].append(f"Batch Processor: {e}")
        else:
            status['services']['batch_processor'] = {'enabled': False, 'status': 'disabled'}
        
        # Initialize Load Balancer (optional)
        if ENABLE_LOAD_BALANCER:
            try:
                from bot.core.load_balancer import LoadBalancer, LoadBalancingStrategy
                
                # Define request handler
                async def default_request_handler(instance, data):
                    """Default request handler"""
                    return f"processed_by_{instance.instance_id}"
                
                lb = LoadBalancer.get_instance()
                lb.request_handler = default_request_handler
                
                # Get strategy
                strategy_name = LOAD_BALANCING_STRATEGY.upper().replace('-', '_')
                strategy = LoadBalancingStrategy[strategy_name] if hasattr(LoadBalancingStrategy, strategy_name) else LoadBalancingStrategy.ROUND_ROBIN
                
                enabled = await lb.enable(strategy)
                
                # Add instances
                if LOAD_BALANCER_INSTANCES:
                    for inst in LOAD_BALANCER_INSTANCES:
                        await lb.add_instance(
                            inst['id'],
                            inst['address'],
                            inst['port'],
                            inst.get('weight', 1.0)
                        )
                
                status['services']['load_balancer'] = {
                    'enabled': enabled,
                    'status': 'running' if enabled else 'failed',
                    'strategy': LOAD_BALANCING_STRATEGY,
                    'instances': len(LOAD_BALANCER_INSTANCES)
                }
                if enabled:
                    phase4_services['load_balancer'] = lb
            except Exception as e:
                status['services']['load_balancer'] = {
                    'enabled': False,
                    'status': 'error',
                    'error': str(e)
                }
                status['errors'].append(f"Load Balancer: {e}")
        else:
            status['services']['load_balancer'] = {'enabled': False, 'status': 'disabled'}
        
        # Determine overall success
        enabled_services = sum(1 for s in status['services'].values() if s.get('status') in ['running', 'disabled'])
        total_services = len(status['services'])
        
        status['success'] = (status['errors'] == [])
        status['summary'] = f"{enabled_services}/{total_services} services ready"
        
        return status
    
    except Exception as e:
        status['success'] = False
        status['errors'].append(f"Initialization error: {e}")
        return status


async def shutdown_phase4_services() -> Dict[str, Any]:
    """
    Safely shutdown all Phase 4 services
    
    Returns:
        Dictionary with shutdown status
    """
    status = {
        'phase': 4,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
        'services_shutdown': [],
        'errors': [],
        'success': True
    }
    
    try:
        # Shutdown Query Optimizer
        if 'query_optimizer' in phase4_services:
            try:
                optimizer = phase4_services['query_optimizer']
                await optimizer.disable()
                status['services_shutdown'].append('query_optimizer')
            except Exception as e:
                status['errors'].append(f"Query Optimizer shutdown: {e}")
        
        # Shutdown Cache Manager
        if 'cache_manager' in phase4_services:
            try:
                cache_mgr = phase4_services['cache_manager']
                await cache_mgr.disable()
                await cache_mgr.clear_all()
                status['services_shutdown'].append('cache_manager')
            except Exception as e:
                status['errors'].append(f"Cache Manager shutdown: {e}")
        
        # Shutdown Connection Pool Manager
        if 'connection_pool_manager' in phase4_services:
            try:
                pool_mgr = phase4_services['connection_pool_manager']
                await pool_mgr.disable()
                status['services_shutdown'].append('connection_pool_manager')
            except Exception as e:
                status['errors'].append(f"Connection Pool Manager shutdown: {e}")
        
        # Shutdown Rate Limiter
        if 'rate_limiter' in phase4_services:
            try:
                limiter = phase4_services['rate_limiter']
                await limiter.disable()
                status['services_shutdown'].append('rate_limiter')
            except Exception as e:
                status['errors'].append(f"Rate Limiter shutdown: {e}")
        
        # Shutdown Batch Processor
        if 'batch_processor' in phase4_services:
            try:
                processor = phase4_services['batch_processor']
                await processor.disable()
                status['services_shutdown'].append('batch_processor')
            except Exception as e:
                status['errors'].append(f"Batch Processor shutdown: {e}")
        
        # Shutdown Load Balancer
        if 'load_balancer' in phase4_services:
            try:
                lb = phase4_services['load_balancer']
                await lb.disable()
                status['services_shutdown'].append('load_balancer')
            except Exception as e:
                status['errors'].append(f"Load Balancer shutdown: {e}")
        
        # Clean up
        phase4_services.clear()
        
        status['success'] = (status['errors'] == [])
        status['summary'] = f"Shutdown {len(status['services_shutdown'])} services"
        
        return status
    
    except Exception as e:
        status['success'] = False
        status['errors'].append(f"Shutdown error: {e}")
        return status


async def get_phase4_status() -> Dict[str, Any]:
    """Get status of all Phase 4 services"""
    try:
        status = {'timestamp': __import__('datetime').datetime.utcnow().isoformat()}
        
        # Query Optimizer status
        if 'query_optimizer' in phase4_services:
            try:
                stats = await phase4_services['query_optimizer'].get_statistics()
                status['query_optimizer'] = stats
            except Exception:
                pass
        
        # Cache Manager status
        if 'cache_manager' in phase4_services:
            try:
                stats = await phase4_services['cache_manager'].get_statistics()
                status['cache_manager'] = stats
            except Exception:
                pass
        
        # Connection Pool Manager status
        if 'connection_pool_manager' in phase4_services:
            try:
                stats = await phase4_services['connection_pool_manager'].get_all_statistics()
                status['connection_pools'] = stats
            except Exception:
                pass
        
        # Rate Limiter status
        if 'rate_limiter' in phase4_services:
            try:
                stats = await phase4_services['rate_limiter'].get_statistics()
                status['rate_limiter'] = stats
            except Exception:
                pass
        
        # Batch Processor status
        if 'batch_processor' in phase4_services:
            try:
                stats = await phase4_services['batch_processor'].get_statistics()
                status['batch_processor'] = stats
            except Exception:
                pass
        
        # Load Balancer status
        if 'load_balancer' in phase4_services:
            try:
                stats = await phase4_services['load_balancer'].get_statistics()
                status['load_balancer'] = stats
            except Exception:
                pass
        
        return status
    
    except Exception as e:
        return {'error': str(e)}
