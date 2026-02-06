#!/usr/bin/env python3
"""
Enable Phase 4 Optimization Components
TIER 2 Task 2.2 - Enables Query Optimizer, Cache Manager, Connection Pool Manager
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def enable_optimization_components():
    """Enable all Phase 4 optimization components"""
    
    print("\n" + "="*70)
    print("  📊 TIER 2 Task 2.2 - Enabling Phase 4 Optimization Components")
    print("="*70 + "\n")
    
    try:
        # Import Phase 4 components
        print("🔧 Loading Phase 4 components...")
        from bot.core.query_optimizer import QueryOptimizer
        from bot.core.cache_manager import CacheManager
        from bot.core.connection_pool_manager import ConnectionPoolManager
        from bot.core.rate_limiter import RateLimiter
        print("   ✅ Components loaded successfully\n")
        
        # 1. Enable Query Optimizer
        print("📝 Enabling Query Optimizer...")
        optimizer = QueryOptimizer.get_instance()
        optimizer.enable()
        stats = optimizer.get_statistics()
        print(f"   ✅ Query Optimizer enabled")
        print(f"      Queries analyzed: {stats.get('total_queries', 0)}")
        print(f"      Cache hits: {stats.get('cache_hits', 0)}")
        print(f"      N+1 patterns detected: {stats.get('n_plus_one_patterns', 0)}\n")
        
        # 2. Enable Cache Manager
        print("💾 Enabling Cache Manager...")
        cache = CacheManager.get_instance()
        await cache.enable(max_size_mb=200)
        cache_stats = cache.statistics
        print(f"   ✅ Cache Manager enabled")
        print(f"      Cache size: {cache_stats.max_size_mb} MB")
        print(f"      Current items: {cache_stats.l1_current_items}")
        print(f"      Hit rate: {cache_stats.hit_rate:.1%}\n")
        
        # 3. Enable Connection Pool Manager
        print("🔌 Enabling Connection Pool Manager...")
        pool_mgr = ConnectionPoolManager.get_instance()
        await pool_mgr.enable()
        pool_stats = pool_mgr.get_statistics()
        print(f"   ✅ Connection Pool Manager enabled")
        print(f"      Pool size: {pool_stats.get('max_size', 'N/A')}")
        print(f"      Active connections: {pool_stats.get('active_connections', 'N/A')}")
        print(f"      Avg wait time: {pool_stats.get('avg_wait_ms', 'N/A')}ms\n")
        
        # 4. Enable Rate Limiter
        print("⚡ Enabling Rate Limiter...")
        rate_limiter = RateLimiter.get_instance()
        rate_limiter.enable()
        limiter_stats = rate_limiter.get_status()
        print(f"   ✅ Rate Limiter enabled")
        print(f"      Tokens/second: {limiter_stats.get('tokens_per_second', 'N/A')}")
        print(f"      Current tokens: {limiter_stats.get('current_tokens', 'N/A')}\n")
        
        print("="*70)
        print("  ✅ All Phase 4 Optimization Components Enabled")
        print("="*70 + "\n")
        
        print("📊 Optimization Status:")
        print("   ✅ Query Optimizer (N+1 detection, query caching)")
        print("   ✅ Cache Manager (200 MB L1 + L2 Redis capable)")
        print("   ✅ Connection Pool Manager (Reduces connection overhead)")
        print("   ✅ Rate Limiter (Prevents abuse)")
        print("\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Error enabling optimization components: {e}", exc_info=True)
        return False


async def main():
    """Main entry point"""
    success = await enable_optimization_components()
    
    if success:
        print("🎯 Next steps:")
        print("   1. Run Phase 4 tests to verify optimizations")
        print("   2. Monitor baseline metrics for performance improvement")
        print("   3. Review operational runbook (Task 3)")
        print("")
        return 0
    else:
        print("❌ Failed to enable optimization components")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
