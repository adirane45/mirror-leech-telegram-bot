"""
Memory Pool Manager
Efficient memory allocation and resource management

Phase 4: Performance Optimization
Created by: justadi
Date: February 8, 2026
"""

import logging
import psutil
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time
import gc

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_mb: float
    available_mb: float
    used_mb: float
    percent: float
    process_rss_mb: float
    process_vms_mb: float
    timestamp: float


class MemoryPoolManager:
    """
    Memory pool manager for efficient resource management
    
    Features:
    - Memory usage monitoring
    - Memory limits enforcement
    - Automatic garbage collection
    - Memory leak detection
    - Resource cleanup
    """
    
    def __init__(
        self,
        memory_limit_mb: Optional[float] = None,
        gc_threshold_percent: float = 80.0,
        enable_auto_gc: bool = True
    ):
        self.memory_limit_mb = memory_limit_mb
        self.gc_threshold_percent = gc_threshold_percent
        self.enable_auto_gc = enable_auto_gc
        
        self.process = psutil.Process()
        self.gc_count = 0
        self.memory_warnings = 0
        
        # Memory tracking
        self.memory_history: List[MemoryStats] = []
        self.max_history_size = 100
        
        logger.info(
            f"MemoryPoolManager initialized (limit={memory_limit_mb}MB, "
            f"gc_threshold={gc_threshold_percent}%, auto_gc={enable_auto_gc})"
        )
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory statistics"""
        vm = psutil.virtual_memory()
        process_mem = self.process.memory_info()
        
        stats = MemoryStats(
            total_mb=vm.total / 1024 / 1024,
            available_mb=vm.available / 1024 / 1024,
            used_mb=vm.used / 1024 / 1024,
            percent=vm.percent,
            process_rss_mb=process_mem.rss / 1024 / 1024,
            process_vms_mb=process_mem.vms / 1024 / 1024,
            timestamp=time.time()
        )
        
        # Store in history
        self.memory_history.append(stats)
        if len(self.memory_history) > self.max_history_size:
            self.memory_history.pop(0)
        
        return stats
    
    def check_memory_limit(self) -> bool:
        """Check if memory usage is within limits"""
        stats = self.get_memory_stats()
        
        # Check system memory
        if stats.percent > self.gc_threshold_percent:
            logger.warning(
                f"System memory usage high: {stats.percent:.1f}% "
                f"(threshold: {self.gc_threshold_percent}%)"
            )
            self.memory_warnings += 1
            
            if self.enable_auto_gc:
                self.force_gc()
            
            return False
        
        # Check process memory limit
        if self.memory_limit_mb and stats.process_rss_mb > self.memory_limit_mb:
            logger.warning(
                f"Process memory limit exceeded: {stats.process_rss_mb:.1f}MB "
                f"(limit: {self.memory_limit_mb}MB)"
            )
            self.memory_warnings += 1
            
            if self.enable_auto_gc:
                self.force_gc()
            
            return False
        
        return True
    
    def force_gc(self) -> Dict[str, int]:
        """Force garbage collection"""
        logger.info("Forcing garbage collection...")
        
        before_stats = self.get_memory_stats()
        
        # Run garbage collection
        collected = {
            "gen0": gc.collect(0),
            "gen1": gc.collect(1),
            "gen2": gc.collect(2)
        }
        
        after_stats = self.get_memory_stats()
        freed_mb = before_stats.process_rss_mb - after_stats.process_rss_mb
        
        self.gc_count += 1
        
        logger.info(
            f"Garbage collection complete: freed {freed_mb:.2f}MB, "
            f"collected={collected}"
        )
        
        return {
            **collected,
            "freed_mb": round(freed_mb, 2),
            "before_mb": round(before_stats.process_rss_mb, 2),
            "after_mb": round(after_stats.process_rss_mb, 2)
        }
    
    def get_memory_trend(self) -> Dict[str, Any]:
        """Analyze memory usage trend"""
        if len(self.memory_history) < 2:
            return {"status": "insufficient_data"}
        
        first = self.memory_history[0]
        last = self.memory_history[-1]
        
        time_span_seconds = last.timestamp - first.timestamp
        memory_growth_mb = last.process_rss_mb - first.process_rss_mb
        growth_rate_mb_per_min = (memory_growth_mb / time_span_seconds * 60) if time_span_seconds > 0 else 0
        
        # Detect potential memory leak
        is_leak = growth_rate_mb_per_min > 1.0 and memory_growth_mb > 10
        
        return {
            "status": "leak_detected" if is_leak else "normal",
            "time_span_seconds": round(time_span_seconds, 2),
            "memory_growth_mb": round(memory_growth_mb, 2),
            "growth_rate_mb_per_min": round(growth_rate_mb_per_min, 2),
            "current_mb": round(last.process_rss_mb, 2),
            "samples": len(self.memory_history)
        }
    
    def optimize_memory(self) -> Dict[str, Any]:
        """Perform memory optimization"""
        logger.info("Starting memory optimization...")
        
        before_stats = self.get_memory_stats()
        actions = []
        
        # 1. Run garbage collection
        gc_result = self.force_gc()
        actions.append({"action": "garbage_collection", "result": gc_result})
        
        # 2. Clear caches if available
        try:
            from .advanced_cache import get_cache
            cache = get_cache()
            cache.l1_cache.clear()
            actions.append({"action": "cache_clear", "result": "success"})
        except Exception as e:
            logger.warning(f"Cache clear failed: {e}")
        
        # 3. Compact memory (Python-specific)
        try:
            import ctypes
            if hasattr(ctypes, 'windll'):
                ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
                actions.append({"action": "compact_memory", "result": "success"})
        except Exception:
            pass
        
        after_stats = self.get_memory_stats()
        total_freed_mb = before_stats.process_rss_mb - after_stats.process_rss_mb
        
        logger.info(f"Memory optimization complete: freed {total_freed_mb:.2f}MB")
        
        return {
            "before_mb": round(before_stats.process_rss_mb, 2),
            "after_mb": round(after_stats.process_rss_mb, 2),
            "freed_mb": round(total_freed_mb, 2),
            "actions": actions
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get memory manager status"""
        stats = self.get_memory_stats()
        trend = self.get_memory_trend()
        
        return {
            "memory": {
                "system_percent": round(stats.percent, 2),
                "system_used_mb": round(stats.used_mb, 2),
                "system_available_mb": round(stats.available_mb, 2),
                "process_rss_mb": round(stats.process_rss_mb, 2),
                "process_vms_mb": round(stats.process_vms_mb, 2)
            },
            "limits": {
                "memory_limit_mb": self.memory_limit_mb,
                "gc_threshold_percent": self.gc_threshold_percent
            },
            "stats": {
                "gc_count": self.gc_count,
                "memory_warnings": self.memory_warnings
            },
            "trend": trend
        }


# Singleton instance
_memory_manager_instance: Optional[MemoryPoolManager] = None


def get_memory_manager(
    memory_limit_mb: Optional[float] = None,
    gc_threshold_percent: float = 80.0,
    enable_auto_gc: bool = True
) -> MemoryPoolManager:
    """Get singleton memory manager instance"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryPoolManager(
            memory_limit_mb=memory_limit_mb,
            gc_threshold_percent=gc_threshold_percent,
            enable_auto_gc=enable_auto_gc
        )
    return _memory_manager_instance
