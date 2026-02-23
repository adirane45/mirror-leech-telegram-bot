"""
Zombie Process Reaper for Phase 9 Enterprise Features

Automatic detection and cleanup of orphaned/zombie processes.

Features:
- Process monitoring
- Zombie detection
- Orphan process cleanup
- Resource recovery
- Scheduled reaping
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Set, Any
from enum import Enum
import os
import signal

logger = logging.getLogger(__name__)


class ProcessState(str, Enum):
    """Process states"""
    RUNNING = "running"
    SLEEPING = "sleeping"
    ZOMBIE = "zombie"
    STOPPED = "stopped"
    DEAD = "dead"


@dataclass
class ProcessInfo:
    """Process information"""
    pid: int
    name: str
    state: ProcessState
    ppid: int  # Parent process ID
    cpu_percent: float
    memory_mb: float
    created_time: datetime
    cmdline: List[str]
    is_zombie: bool = False
    is_orphan: bool = False


@dataclass
class ReapStats:
    """Reaping statistics"""
    zombies_found: int
    zombies_reaped: int
    orphans_found: int
    orphans_cleaned: int
    resources_freed_mb: float
    duration_seconds: float


class ProcessMonitor:
    """
    Process monitoring and analysis.
    
    Features:
    - Process enumeration
    - State detection
    - Parent-child tracking
    - Resource usage monitoring
    """
    
    def __init__(self):
        """Initialize process monitor"""
        self.monitored_pids: Set[int] = set()
        self.process_cache: Dict[int, ProcessInfo] = {}
        
        logger.info("ProcessMonitor initialized")
    
    async def scan_processes(self) -> List[ProcessInfo]:
        """
        Scan all processes on system.
        
        Returns:
            List of ProcessInfo
        """
        processes = []
        
        # Mock process scanning (would use psutil in production)
        mock_processes = self._generate_mock_processes()
        
        for proc in mock_processes:
            processes.append(proc)
            self.process_cache[proc.pid] = proc
        
        logger.info(f"Scanned {len(processes)} processes")
        
        return processes
    
    def _generate_mock_processes(self) -> List[ProcessInfo]:
        """Generate mock process list"""
        import random
        
        processes = []
        base_time = datetime.now()
        
        # Normal processes
        for i in range(5):
            processes.append(ProcessInfo(
                pid=1000 + i,
                name=f"worker_{i}",
                state=ProcessState.RUNNING,
                ppid=1,
                cpu_percent=random.uniform(0, 50),
                memory_mb=random.uniform(10, 500),
                created_time=base_time - timedelta(hours=random.randint(1, 24)),
                cmdline=[f"python", f"worker_{i}.py"]
            ))
        
        # Zombie processes (2-3)
        for i in range(2):
            processes.append(ProcessInfo(
                pid=2000 + i,
                name=f"<defunct>",
                state=ProcessState.ZOMBIE,
                ppid=1,
                cpu_percent=0,
                memory_mb=0,
                created_time=base_time - timedelta(hours=random.randint(5, 48)),
                cmdline=[],
                is_zombie=True
            ))
        
        # Orphan processes (1-2)
        for i in range(1):
            processes.append(ProcessInfo(
                pid=3000 + i,
                name=f"orphan_{i}",
                state=ProcessState.SLEEPING,
                ppid=9999,  # Non-existent parent
                cpu_percent=0,
                memory_mb=random.uniform(5, 50),
                created_time=base_time - timedelta(days=random.randint(1, 7)),
                cmdline=[f"orphan_{i}"],
                is_orphan=True
            ))
        
        return processes
    
    async def get_process_tree(self, pid: int) -> Dict[int, List[int]]:
        """
        Get process tree (parent-child relationships).
        
        Args:
            pid: Root process ID
            
        Returns:
            Dict mapping PIDs to child PIDs
        """
        tree: Dict[int, List[int]] = {}
        
        processes = await self.scan_processes()
        
        for proc in processes:
            if proc.ppid not in tree:
                tree[proc.ppid] = []
            tree[proc.ppid].append(proc.pid)
        
        return tree
    
    async def find_zombies(self) -> List[ProcessInfo]:
        """
        Find all zombie processes.
        
        Returns:
            List of zombie ProcessInfo
        """
        processes = await self.scan_processes()
        
        zombies = [
            proc for proc in processes
            if proc.state == ProcessState.ZOMBIE or proc.is_zombie
        ]
        
        logger.info(f"Found {len(zombies)} zombie processes")
        
        return zombies
    
    async def find_orphans(self) -> List[ProcessInfo]:
        """
        Find orphaned processes (parent doesn't exist).
        
        Returns:
            List of orphan ProcessInfo
        """
        processes = await self.scan_processes()
        
        # Get all valid PIDs
        valid_pids = {proc.pid for proc in processes}
        
        orphans = [
            proc for proc in processes
            if proc.ppid not in valid_pids and proc.ppid != 0 and proc.ppid != 1
        ]
        
        # Mark as orphans
        for proc in orphans:
            proc.is_orphan = True
        
        logger.info(f"Found {len(orphans)} orphan processes")
        
        return orphans


class ZombieReaper:
    """
    Automatic zombie process reaper.
    
    Features:
    - Scheduled reaping
    - Safe termination
    - Parent notification
    - Cleanup verification
    """
    
    def __init__(self, monitor: ProcessMonitor):
        """
        Initialize zombie reaper.
        
        Args:
            monitor: ProcessMonitor instance
        """
        self.monitor = monitor
        self.reap_interval = 60  # Reap every 60 seconds
        self.running = False
        
        self.stats = {
            "total_reaps": 0,
            "zombies_reaped": 0,
            "orphans_cleaned": 0,
            "memory_freed_mb": 0.0
        }
        
        logger.info("ZombieReaper initialized")
    
    async def reap_zombies(self) -> ReapStats:
        """
        Reap all zombie processes.
        
        Returns:
            ReapStats
        """
        import time
        start_time = time.perf_counter()
        
        zombies = await self.monitor.find_zombies()
        zombies_found = len(zombies)
        zombies_reaped = 0
        memory_freed = 0.0
        
        for zombie in zombies:
            if await self._reap_process(zombie):
                zombies_reaped += 1
                memory_freed += zombie.memory_mb
                self.stats["zombies_reaped"] += 1
        
        duration = time.perf_counter() - start_time
        
        self.stats["total_reaps"] += 1
        self.stats["memory_freed_mb"] += memory_freed
        
        logger.info(
            f"Reap cycle complete: {zombies_reaped}/{zombies_found} zombies "
            f"({memory_freed:.2f} MB freed)"
        )
        
        return ReapStats(
            zombies_found=zombies_found,
            zombies_reaped=zombies_reaped,
            orphans_found=0,
            orphans_cleaned=0,
            resources_freed_mb=memory_freed,
            duration_seconds=duration
        )
    
    async def _reap_process(self, proc: ProcessInfo) -> bool:
        """
        Reap a single zombie process.
        
        Args:
            proc: ProcessInfo of zombie
            
        Returns:
            True if successfully reaped
        """
        try:
            # Mock reaping (would use os.waitpid in production)
            await asyncio.sleep(0.01)
            
            logger.debug(f"Reaped zombie process: PID {proc.pid} ({proc.name})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reap PID {proc.pid}: {e}")
            return False
    
    async def clean_orphans(self) -> ReapStats:
        """
        Clean up orphaned processes.
        
        Returns:
            ReapStats
        """
        import time
        start_time = time.perf_counter()
        
        orphans = await self.monitor.find_orphans()
        orphans_found = len(orphans)
        orphans_cleaned = 0
        memory_freed = 0.0
        
        for orphan in orphans:
            if await self._terminate_orphan(orphan):
                orphans_cleaned += 1
                memory_freed += orphan.memory_mb
                self.stats["orphans_cleaned"] += 1
        
        duration = time.perf_counter() - start_time
        
        self.stats["memory_freed_mb"] += memory_freed
        
        logger.info(
            f"Orphan cleanup: {orphans_cleaned}/{orphans_found} terminated "
            f"({memory_freed:.2f} MB freed)"
        )
        
        return ReapStats(
            zombies_found=0,
            zombies_reaped=0,
            orphans_found=orphans_found,
            orphans_cleaned=orphans_cleaned,
            resources_freed_mb=memory_freed,
            duration_seconds=duration
        )
    
    async def _terminate_orphan(self, proc: ProcessInfo) -> bool:
        """
        Terminate an orphaned process.
        
        Args:
            proc: ProcessInfo of orphan
            
        Returns:
            True if successfully terminated
        """
        try:
            # Mock termination (would use os.kill in production)
            await asyncio.sleep(0.01)
            
            logger.debug(f"Terminated orphan: PID {proc.pid} ({proc.name})")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to terminate PID {proc.pid}: {e}")
            return False
    
    async def start_auto_reap(self):
        """Start automatic reaping loop"""
        self.running = True
        
        logger.info(f"Auto-reap started (interval: {self.reap_interval}s)")
        
        while self.running:
            try:
                # Reap zombies
                await self.reap_zombies()
                
                # Clean orphans (less frequently)
                if self.stats["total_reaps"] % 5 == 0:
                    await self.clean_orphans()
                
            except Exception as e:
                logger.error(f"Reap cycle error: {e}")
            
            await asyncio.sleep(self.reap_interval)
    
    def stop_auto_reap(self):
        """Stop automatic reaping"""
        self.running = False
        logger.info("Auto-reap stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reaper statistics"""
        return {
            "total_reaps": self.stats["total_reaps"],
            "zombies_reaped": self.stats["zombies_reaped"],
            "orphans_cleaned": self.stats["orphans_cleaned"],
            "memory_freed_mb": self.stats["memory_freed_mb"],
            "running": self.running
        }


class ResourceRecovery:
    """
    Resource recovery from terminated processes.
    
    Features:
    - Memory cleanup
    - File handle closure
    - Socket cleanup
    - Temp file removal
    """
    
    def __init__(self):
        """Initialize resource recovery"""
        self.recovered_resources = {
            "memory_mb": 0.0,
            "file_handles": 0,
            "sockets": 0,
            "temp_files": 0
        }
        
        logger.info("ResourceRecovery initialized")
    
    async def recover_from_process(self, proc: ProcessInfo) -> Dict[str, int]:
        """
        Recover resources from terminated process.
        
        Args:
            proc: ProcessInfo of terminated process
            
        Returns:
            Dict of recovered resources
        """
        recovered = {
            "memory_mb": proc.memory_mb,
            "file_handles": 0,
            "sockets": 0,
            "temp_files": 0
        }
        
        # Mock resource recovery
        await asyncio.sleep(0.05)
        
        # Clean up file handles
        recovered["file_handles"] = await self._close_file_handles(proc.pid)
        
        # Clean up sockets
        recovered["sockets"] = await self._cleanup_sockets(proc.pid)
        
        # Remove temp files
        recovered["temp_files"] = await self._cleanup_temp_files(proc.pid)
        
        # Update totals
        for key, value in recovered.items():
            self.recovered_resources[key] += value
        
        logger.info(
            f"Recovered resources from PID {proc.pid}: "
            f"{recovered['memory_mb']:.2f} MB, "
            f"{recovered['file_handles']} FDs, "
            f"{recovered['sockets']} sockets"
        )
        
        return recovered
    
    async def _close_file_handles(self, pid: int) -> int:
        """Close open file handles"""
        # Mock: close 5-10 file handles
        import random
        await asyncio.sleep(0.01)
        return random.randint(5, 10)
    
    async def _cleanup_sockets(self, pid: int) -> int:
        """Clean up open sockets"""
        # Mock: close 1-3 sockets
        import random
        await asyncio.sleep(0.01)
        return random.randint(1, 3)
    
    async def _cleanup_temp_files(self, pid: int) -> int:
        """Remove temporary files"""
        # Mock: remove 0-5 temp files
        import random
        await asyncio.sleep(0.01)
        return random.randint(0, 5)
    
    def get_recovery_stats(self) -> Dict[str, float]:
        """Get resource recovery statistics"""
        return self.recovered_resources.copy()


class ProcessGuard:
    """
    Process guard for monitored applications.
    
    Features:
    - Process health checks
    - Automatic restart on failure
    - Crash detection
    - Graceful shutdown
    """
    
    def __init__(self, monitor: ProcessMonitor):
        """
        Initialize process guard.
        
        Args:
            monitor: ProcessMonitor instance
        """
        self.monitor = monitor
        self.guarded_pids: Dict[int, str] = {}  # PID -> name mapping
        
        logger.info("ProcessGuard initialized")
    
    async def guard_process(self, pid: int, name: str):
        """
        Add process to guarded list.
        
        Args:
            pid: Process ID
            name: Process name
        """
        self.guarded_pids[pid] = name
        logger.info(f"Guarding process: {name} (PID {pid})")
    
    async def check_health(self) -> List[int]:
        """
        Check health of guarded processes.
        
        Returns:
            List of unhealthy PIDs
        """
        processes = await self.monitor.scan_processes()
        process_pids = {proc.pid for proc in processes}
        
        unhealthy = []
        
        for pid, name in self.guarded_pids.items():
            if pid not in process_pids:
                logger.warning(f"Guarded process dead: {name} (PID {pid})")
                unhealthy.append(pid)
        
        return unhealthy
    
    async def restart_dead_processes(self) -> int:
        """
        Restart dead guarded processes.
        
        Returns:
            Number of processes restarted
        """
        unhealthy = await self.check_health()
        restarted = 0
        
        for pid in unhealthy:
            name = self.guarded_pids.pop(pid, "unknown")
            
            # Mock restart
            await asyncio.sleep(0.1)
            new_pid = pid + 10000  # Mock new PID
            
            self.guarded_pids[new_pid] = name
            restarted += 1
            
            logger.info(f"Restarted {name}: old PID {pid} -> new PID {new_pid}")
        
        return restarted


# Convenience functions
async def reap_all_zombies() -> ReapStats:
    """Quick zombie reaping"""
    monitor = ProcessMonitor()
    reaper = ZombieReaper(monitor)
    return await reaper.reap_zombies()


async def clean_all_orphans() -> ReapStats:
    """Quick orphan cleanup"""
    monitor = ProcessMonitor()
    reaper = ZombieReaper(monitor)
    return await reaper.clean_orphans()


async def start_reaper_daemon(interval: int = 60):
    """
    Start zombie reaper daemon.
    
    Args:
        interval: Reaping interval in seconds
    """
    monitor = ProcessMonitor()
    reaper = ZombieReaper(monitor)
    reaper.reap_interval = interval
    
    await reaper.start_auto_reap()
