"""
JIT Optimization & Cython Compilation Engine for Phase 7

Implements:
- Performance hotspot detection
- Cython compilation suggestions
- PyPy/Numba integration recommendations
- CPU-bound function identification
- Automatic optimization hints
"""

import ast
import cProfile
import pstats
import io
import time
import inspect
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import psutil

from .. import LOGGER


class OptimizationLevel(str, Enum):
    """Optimization levels"""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"


class OptimizationType(str, Enum):
    """Types of optimizations"""
    CYTHON = "cython"
    NUMBA = "numba"
    PYPY = "pypy"
    VECTORIZATION = "vectorization"
    PARALLEL = "parallel"
    CACHING = "caching"


@dataclass
class FunctionProfile:
    """Profile data for a function"""
    function_name: str
    module: str
    call_count: int = 0
    total_time_seconds: float = 0.0
    cumulative_time_seconds: float = 0.0
    cpu_time_percent: float = 0.0
    is_cpu_bound: bool = False
    is_io_bound: bool = False
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class HotSpot:
    """Performance hotspot"""
    function_name: str
    module: str
    time_percent: float
    call_count: int
    avg_time_ms: float
    recommendations: List[str] = field(default_factory=list)


class CythonOptimizationEngine:
    """Detect and suggest Cython optimizations"""
    
    def __init__(self):
        self.candidates: Dict[str, FunctionProfile] = {}
        self.threshold_cpu_percent = 5.0  # Functions using >5% CPU time
        self.threshold_call_count = 100  # Functions called >100 times
    
    def analyze_function(self, func: Callable) -> List[str]:
        """Analyze function for Cython optimization opportunities"""
        suggestions = []
        
        try:
            source = inspect.getsource(func)
            tree = ast.parse(source)
            
            # Check for type hints
            has_type_hints = False
            for node in ast.walk(tree):
                if isinstance(node, ast.AnnAssign) or isinstance(node, ast.arg):
                    if hasattr(node, 'annotation') and node.annotation:
                        has_type_hints = True
                        break
            
            if has_type_hints:
                suggestions.append(
                    "⚡ Has type hints - Good Cython candidate. "
                    "Add cdef declarations for 2-5x speedup."
                )
            else:
                suggestions.append(
                    "💡 Add type hints for better Cython optimization"
                )
            
            # Check for loops
            loop_count = sum(
                1 for node in ast.walk(tree)
                if isinstance(node, (ast.For, ast.While))
            )
            
            if loop_count > 0:
                suggestions.append(
                    f"🔄 Contains {loop_count} loop(s). "
                    "Cython can optimize tight loops by 10-100x."
                )
            
            # Check for numerical operations
            has_math = any(
                isinstance(node, (ast.BinOp, ast.UnaryOp))
                for node in ast.walk(tree)
            )
            
            if has_math:
                suggestions.append(
                    "🔢 Contains numerical operations. "
                    "Consider Cython with NumPy integration or Numba JIT."
                )
            
            # Check for list comprehensions
            list_comps = sum(
                1 for node in ast.walk(tree)
                if isinstance(node, ast.ListComp)
            )
            
            if list_comps > 0:
                suggestions.append(
                    f"📋 Contains {list_comps} list comprehension(s). "
                    "Cython can optimize these significantly."
                )
        
        except Exception as e:
            suggestions.append(f"⚠️ Analysis error: {e}")
        
        return suggestions
    
    def generate_cython_stub(self, func_name: str, module: str) -> str:
        """Generate Cython .pyx stub"""
        stub = f"""# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

cdef class Optimized{func_name.title()}:
    \"\"\"Cython-optimized version of {module}.{func_name}\"\"\"
    
    cpdef process(self, data):
        # TODO: Port function logic here with cdef declarations
        # cdef int i
        # cdef double result = 0.0
        pass
"""
        return stub


class JITOptimizer:
    """Main JIT optimization engine"""
    
    def __init__(self):
        self.profiler = cProfile.Profile()
        self.cython_engine = CythonOptimizationEngine()
        self.hotspots: List[HotSpot] = []
        self.function_profiles: Dict[str, FunctionProfile] = {}
        self.is_profiling = False
    
    def start_profiling(self) -> None:
        """Start profiling"""
        self.profiler.enable()
        self.is_profiling = True
        LOGGER.info("JIT profiling started")
    
    def stop_profiling(self) -> None:
        """Stop profiling"""
        self.profiler.disable()
        self.is_profiling = False
        LOGGER.info("JIT profiling stopped")
    
    def analyze_profile(self) -> Dict[str, Any]:
        """Analyze profiling results"""
        if self.is_profiling:
            self.stop_profiling()
        
        # Get stats
        stream = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=stream)
        stats.strip_dirs()
        stats.sort_stats('cumulative')
        
        # Extract top functions
        self.hotspots.clear()
        self.function_profiles.clear()
        
        for func, (cc, nc, tt, ct, callers) in stats.stats.items():
            filename, line, func_name = func
            
            # Skip built-in functions
            if filename.startswith('<'):
                continue
            
            # Calculate percentages
            total_time = sum(
                stat[2] for stat in stats.stats.values()
            )
            time_percent = (tt / total_time * 100) if total_time > 0 else 0
            
            # Create profile
            profile = FunctionProfile(
                function_name=func_name,
                module=filename,
                call_count=cc,
                total_time_seconds=tt,
                cumulative_time_seconds=ct,
                cpu_time_percent=time_percent
            )
            
            # Determine if CPU-bound (high time, low I/O wait)
            if time_percent > 1.0:
                profile.is_cpu_bound = True
                
                # Add to hotspots
                hotspot = HotSpot(
                    function_name=func_name,
                    module=filename,
                    time_percent=time_percent,
                    call_count=cc,
                    avg_time_ms=(tt / cc * 1000) if cc > 0 else 0
                )
                
                # Generate recommendations
                if time_percent > 10:
                    hotspot.recommendations.append(
                        "🔥 CRITICAL HOTSPOT - Immediate optimization required"
                    )
                if cc > 1000:
                    hotspot.recommendations.append(
                        "⚡ High call frequency - Consider Cython compilation"
                    )
                if time_percent > 5 and cc > 100:
                    hotspot.recommendations.append(
                        "💡 Good Cython candidate - Expected 3-10x speedup"
                    )
                
                self.hotspots.append(hotspot)
            
            self.function_profiles[f"{filename}:{func_name}"] = profile
        
        # Sort hotspots by time
        self.hotspots.sort(key=lambda h: h.time_percent, reverse=True)
        
        return {
            "total_hotspots": len(self.hotspots),
            "top_hotspots": [
                {
                    "function": h.function_name,
                    "time_percent": h.time_percent,
                    "call_count": h.call_count,
                    "recommendations": h.recommendations
                }
                for h in self.hotspots[:10]
            ]
        }
    
    def get_optimization_report(self) -> str:
        """Generate comprehensive optimization report"""
        report = ["=" * 80]
        report.append("JIT OPTIMIZATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        if not self.hotspots:
            report.append("No profiling data available. Run start_profiling() first.")
            return "\n".join(report)
        
        report.append(f"Total Hotspots Detected: {len(self.hotspots)}")
        report.append("")
        
        report.append("TOP 10 PERFORMANCE HOTSPOTS:")
        report.append("-" * 80)
        
        for i, hotspot in enumerate(self.hotspots[:10], 1):
            report.append(f"\n{i}. {hotspot.function_name}")
            report.append(f"   Module: {hotspot.module}")
            report.append(f"   Time: {hotspot.time_percent:.2f}% | Calls: {hotspot.call_count}")
            report.append(f"   Avg Time: {hotspot.avg_time_ms:.3f}ms")
            
            if hotspot.recommendations:
                report.append("   Recommendations:")
                for rec in hotspot.recommendations:
                    report.append(f"     • {rec}")
        
        report.append("")
        report.append("=" * 80)
        report.append("OPTIMIZATION STRATEGIES:")
        report.append("=" * 80)
        
        report.append("\n1. CYTHON COMPILATION:")
        report.append("   Functions with >5% CPU time are prime candidates")
        report.append("   Expected speedup: 3-10x for pure Python, 10-100x for loops")
        
        report.append("\n2. NUMBA JIT:")
        report.append("   For numerical/array operations")
        report.append("   Add @numba.jit decorator for instant speedup")
        
        report.append("\n3. PYPY:")
        report.append("   Alternative interpreter with JIT compilation")
        report.append("   Expected speedup: 2-5x for long-running processes")
        
        report.append("")
        return "\n".join(report)
    
    def generate_cython_stubs(self) -> Dict[str, str]:
        """Generate Cython stubs for top hotspots"""
        stubs = {}
        
        for hotspot in self.hotspots[:5]:  # Top 5
            if hotspot.time_percent > 5.0:
                stub = self.cython_engine.generate_cython_stub(
                    hotspot.function_name,
                    hotspot.module
                )
                stubs[f"{hotspot.function_name}.pyx"] = stub
        
        return stubs


class PerformanceMonitor:
    """Real-time performance monitoring"""
    
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            "uptime_seconds": time.time() - self.start_time,
            "memory_mb": current_memory,
            "memory_delta_mb": current_memory - self.baseline_memory,
            "cpu_percent": self.process.cpu_percent(interval=0.1),
            "threads": self.process.num_threads(),
            "connections": len(self.process.net_connections())
        }


# Global instances
jit_optimizer = JITOptimizer()
performance_monitor = PerformanceMonitor()
