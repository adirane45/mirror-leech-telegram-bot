"""
Integration Module for Category B Features
Connects Smart Retry, Parallel Downloads, Priority Queue, and Health Monitor
"""

import asyncio
from typing import Optional, Callable, Dict, Any
from logging import getLogger
from pathlib import Path

# Import Category B modules
from .smart_retry import (
    SmartRetryEngine,
    DeadLetterQueue,
    FailureContext,
    FailureType,
    CheckpointManager,
    FailureAnalyzer,
)
from .parallel_downloads import (
    ParallelDownloadManager,
    ChunkInfo,
    ChunkState,
    ChunkAssembler,
)
from .priority_queue import (
    DynamicQueueManager,
    QueuedTask,
    TaskPriority,
    UserTier,
    QueueName,
    queue_manager,
    initialize_queue_system,
)

# Import existing modules
from .circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerException
from .health_monitor import HealthMonitor

LOGGER = getLogger(__name__)


class CategoryBIntegration:
    """Integrates all Category B advanced features"""
    
    def __init__(self):
        self.retry_engine = SmartRetryEngine()
        self.queue_manager = queue_manager
        self._initialized = False
        
        # Circuit breakers for external APIs
        self.telegram_breaker = CircuitBreaker(
            name="telegram_api",
            failure_threshold=5,
            timeout=60,
        )
        
        self.gdrive_breaker = CircuitBreaker(
            name="google_drive_api",
            failure_threshold=3,
            timeout=120,
        )
        
        self.aria2_breaker = CircuitBreaker(
            name="aria2_client",
            failure_threshold=5,
            timeout=30,
        )
    
    async def initialize(self):
        """Initialize Category B systems"""
        if self._initialized:
            return
        
        LOGGER.info("🚀 Initializing Category B Features...")
        
        # Initialize queue system
        await initialize_queue_system()
        
        # Register health checks
        await self._register_health_checks()
        
        # Start retry processor
        asyncio.create_task(self._start_retry_processor())
        
        # Start queue dispatchers
        await self._start_queue_dispatchers()
        
        self._initialized = True
        LOGGER.info("✅ Category B Features initialized successfully")
    
    async def _register_health_checks(self):
        """Register health checks for Category B components"""
        try:
            health_monitor = HealthMonitor.get_instance()
            from .health_models import ComponentType
            
            # DLQ health check
            async def dlq_health_check():
                count = await self.retry_engine.dlq.count()
                return {
                    "status": "healthy" if count < 100 else "degraded",
                    "dlq_count": count,
                }
            
            health_monitor.register_health_check("dead_letter_queue", dlq_health_check)
            
            # Queue health check
            async def queue_health_check():
                stats = await self.queue_manager.get_all_stats()
                total_pending = sum(s.queued_tasks for s in stats.values())
                return {
                    "status": "healthy" if total_pending < 50 else "degraded",
                    "total_pending": total_pending,
                }
            
            health_monitor.register_health_check("task_queue", queue_health_check)
            
            LOGGER.info("✅ Health checks registered for Category B features")
        except Exception as e:
            LOGGER.warning(f"Could not register health checks: {e}")
    
    async def _start_retry_processor(self):
        """Start retry processor loop"""
        
        async def retry_callback(task_id: str, failure: FailureContext, checkpoint: Optional[Dict]):
            """Callback to retry failed task"""
            try:
                # Re-queue task based on operation
                if failure.operation == "download":
                    await self._retry_download(task_id, failure, checkpoint)
                elif failure.operation == "upload":
                    await self._retry_upload(task_id, failure, checkpoint)
                else:
                    LOGGER.warning(f"Unknown operation: {failure.operation}")
            except Exception as e:
                raise Exception(f"Retry failed: {e}")
        
        # Start retry loop
        asyncio.create_task(self.retry_engine.processor_loop(retry_callback))
        LOGGER.info("🔄 Smart Retry processor started")
    
    async def _start_queue_dispatchers(self):
        """Start queue dispatcher loops"""
        
        async def default_executor(task: QueuedTask):
            """Execute queued task"""
            if task.execute_callback:
                if asyncio.iscoroutinefunction(task.execute_callback):
                    await task.execute_callback(task)
                else:
                    task.execute_callback(task)
        
        # Set executors for all queues
        for queue_name in [QueueName.DEFAULT.value, QueueName.VIP.value, 
                           QueueName.EMERGENCY.value, QueueName.BATCH.value]:
            await self.queue_manager.set_executor(queue_name, default_executor)
            await self.queue_manager.start_dispatcher(queue_name)
        
        LOGGER.info("⚡ Queue dispatchers started")
    
    async def _retry_download(self, task_id: str, failure: FailureContext, checkpoint: Optional[Dict]):
        """Retry download with checkpoint recovery"""
        LOGGER.info(f"Retrying download: {task_id}")
        # Implementation depends on your download system
        pass
    
    async def _retry_upload(self, task_id: str, failure: FailureContext, checkpoint: Optional[Dict]):
        """Retry upload with checkpoint recovery"""
        LOGGER.info(f"Retrying upload: {task_id}")
        # Implementation depends on your upload system
        pass
    
    async def download_with_parallel_chunks(
        self,
        url: str,
        file_size: int,
        output_path: Path,
        num_chunks: int = 4,
        user_id: int = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        user_tier: UserTier = UserTier.STANDARD,
    ) -> Optional[Path]:
        """
        Download file using parallel chunks
        
        Args:
            url: Download URL
            file_size: Total file size
            output_path: Where to save file
            num_chunks: Number of parallel chunks (3-5)
            user_id: User ID (for priority)
            priority: Task priority
            user_tier: User tier (for priority)
            
        Returns:
            Path to downloaded file or None if failed
        """
        task_id = f"download_{output_path.name}_{int(asyncio.get_event_loop().time())}"
        
        try:
            # Create parallel download manager
            manager = ParallelDownloadManager(
                file_size=file_size,
                output_path=output_path,
                num_chunks=num_chunks,
            )
            
            # Download callback (implement based on your download system)
            async def download_chunk(chunk_id: int, start: int, end: int, write_callback: Callable):
                """Download single chunk"""
                # This is a placeholder - integrate with Aria2/qBittorrent/requests
                LOGGER.info(f"Downloading chunk {chunk_id}: {start}-{end}")
                # Example using aiohttp:
                # async with aiohttp.ClientSession() as session:
                #     headers = {"Range": f"bytes={start}-{end}"}
                #     async with session.get(url, headers=headers) as resp:
                #         async for data in resp.content.iter_chunked(8192):
                #             await write_callback(data)
            
            # Progress callback
            async def progress_callback(progress: Dict[str, Any]):
                """Report download progress"""
                LOGGER.debug(
                    f"Download progress: {progress['percent']:.1f}% "
                    f"({progress['downloaded_bytes']}/{progress['total_bytes']})"
                )
            
            # Attempt download
            success = await manager.download(download_chunk, progress_callback)
            
            if success:
                LOGGER.info(f"✅ Download completed: {output_path}")
                return output_path
            else:
                # Handle failure - add to DLQ
                await self.retry_engine.handle_failure(
                    task_id=task_id,
                    operation="download",
                    error=Exception("Download failed"),
                    metadata={"url": url, "file_size": file_size},
                    checkpoint={
                        "chunks": [
                            {
                                "id": c.chunk_id,
                                "downloaded": c.downloaded_bytes,
                                "state": c.state.value,
                            }
                            for c in manager.chunks
                        ]
                    },
                )
                return None
                
        except Exception as e:
            LOGGER.error(f"Parallel download error: {e}", exc_info=True)
            
            # Add to DLQ
            await self.retry_engine.handle_failure(
                task_id=task_id,
                operation="download",
                error=e,
                metadata={"url": url, "file_size": file_size},
            )
            
            return None
    
    async def add_task_to_queue(
        self,
        task_id: str,
        user_id: int,
        operation: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        user_tier: UserTier = UserTier.STANDARD,
        queue_name: str = "default",
        file_name: Optional[str] = None,
        file_size: Optional[int] = None,
        execute_callback: Optional[Callable] = None,
    ) -> bool:
        """
        Add task to priority queue
        
        Args:
            task_id: Unique task ID
            user_id: User ID
            operation: Operation type (download, upload, etc.)
            priority: Task priority
            user_tier: User tier (affects priority)
            queue_name: Target queue
            file_name: File name
            file_size: File size
            execute_callback: Function to execute task
            
        Returns:
            True if task added successfully
        """
        return await self.queue_manager.add_task(
            task_id=task_id,
            user_id=user_id,
            operation=operation,
            priority=priority,
            user_tier=user_tier,
            queue_name=queue_name,
            file_name=file_name,
            file_size=file_size,
            execute_callback=execute_callback,
        )
    
    async def protected_api_call(self, breaker_name: str, api_call: Callable, *args, **kwargs):
        """
        Execute API call protected by circuit breaker
        
        Args:
            breaker_name: Circuit breaker to use (telegram, gdrive, aria2)
            api_call: Async function to call
            *args, **kwargs: Arguments to pass to api_call
            
        Returns:
            Result of api_call
            
        Raises:
            CircuitBreakerException: If circuit is open
        """
        breaker_map = {
            "telegram": self.telegram_breaker,
            "gdrive": self.gdrive_breaker,
            "aria2": self.aria2_breaker,
        }
        
        breaker = breaker_map.get(breaker_name)
        if not breaker:
            LOGGER.warning(f"Unknown breaker: {breaker_name}, calling directly")
            return await api_call(*args, **kwargs)
        
        return await breaker.call(api_call, *args, **kwargs)
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        return await self.queue_manager.get_all_stats()
    
    async def get_dlq_count(self) -> int:
        """Get DLQ count"""
        return await self.retry_engine.dlq.count()
    
    async def list_dlq_tasks(self) -> list:
        """List all tasks in DLQ"""
        tasks = await self.retry_engine.dlq.list_all()
        return [
            {
                "task_id": t.task_id,
                "operation": t.operation,
                "error_type": t.error_type.value,
                "error_message": t.error_message,
                "failure_count": t.failure_count,
                "recoverable": t.is_recoverable(),
            }
            for t in tasks
        ]


# Global instance
category_b = CategoryBIntegration()
