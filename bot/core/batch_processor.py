"""
Batch Processor for Efficient Request Processing

Collects multiple requests and processes them in batches to reduce
overhead, improve throughput, and enable parallel processing.

Features:
- Request batching
- Batch size optimization
- Timeout-based flushing
- Parallel batch execution
- Processing statistics
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum


class BatchStatus(Enum):
    """Batch processing status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class BatchItem:
    """Single item in a batch"""
    item_id: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class BatchResult:
    """Result of batch processing"""
    batch_id: str
    status: BatchStatus
    item_count: int
    success_count: int
    error_count: int
    processing_time: float
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)


@dataclass
class BatchStatistics:
    """Batch processor statistics"""
    total_batches: int
    completed_batches: int
    failed_batches: int
    total_items: int
    processed_items: int
    failed_items: int
    avg_batch_size: float
    avg_processing_time: float
    throughput_items_per_sec: float


class Batch:
    """Single batch container"""
    
    def __init__(self, batch_id: str, max_size: int, timeout: int):
        self.batch_id = batch_id
        self.max_size = max_size
        self.timeout = timeout
        self.items: List[BatchItem] = []
        self.created_at = datetime.utcnow()
        self.status = BatchStatus.QUEUED
        self.is_full = False
        self.is_timeouted = False
    
    def add_item(self, item: BatchItem) -> bool:
        """Add item to batch"""
        if len(self.items) < self.max_size:
            self.items.append(item)
            self.is_full = (len(self.items) >= self.max_size)
            return True
        return False
    
    def is_ready(self) -> bool:
        """Check if batch is ready for processing"""
        if self.is_full:
            return True
        
        age = (datetime.utcnow() - self.created_at).total_seconds()
        if age >= self.timeout:
            self.is_timeouted = True
            return True
        
        return False
    
    def get_age(self) -> float:
        """Get batch age in seconds"""
        return (datetime.utcnow() - self.created_at).total_seconds()


class BatchProcessor:
    """Batch processor for efficient request handling"""
    
    _instance: Optional['BatchProcessor'] = None
    
    def __init__(self):
        self.enabled = False
        self.batch_handler: Optional[Callable] = None
        
        self.batches: Dict[str, Batch] = {}
        self.pending_queue: asyncio.Queue = asyncio.Queue()
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        
        self.batch_counter = 0
        self.item_counter = 0
        
        self.max_batch_size = 100
        self.batch_timeout = 5  # seconds
        self.max_concurrent_batches = 10
        self.semaphore = asyncio.Semaphore(self.max_concurrent_batches)
        
        self.completed_batches = 0
        self.failed_batches = 0
        self.processed_items = 0
        self.failed_items = 0
        self.total_processing_time = 0.0
        
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.processor_task: Optional[asyncio.Task] = None
        
        self.lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'BatchProcessor':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = BatchProcessor()
        return cls._instance
    
    async def enable(self, batch_handler: Callable) -> bool:
        """Enable batch processor with handler"""
        try:
            async with self.lock:
                self.batch_handler = batch_handler
                self.enabled = True
                
                # Start processor task
                if self.processor_task is None or self.processor_task.done():
                    self.processor_task = asyncio.create_task(self._processor_loop())
                
                return True
        except Exception as e:
            print(f"Error enabling batch processor: {e}")
            return False
    
    async def disable(self) -> bool:
        """Disable batch processor"""
        try:
            async with self.lock:
                self.enabled = False
                
                if self.processor_task:
                    self.processor_task.cancel()
                    try:
                        await self.processor_task
                    except asyncio.CancelledError:
                        pass
                    self.processor_task = None
                
                # Cancel all processing tasks
                for task in self.processing_tasks.values():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                self.processing_tasks.clear()
                
                return True
        except Exception as e:
            print(f"Error disabling batch processor: {e}")
            return False
    
    async def submit_item(self, data: Any) -> Tuple[bool, str, str]:
        """Submit item for batch processing"""
        if not self.enabled or not self.batch_handler:
            return False, "", "Batch processor not enabled"
        
        try:
            async with self.lock:
                self.item_counter += 1
                item_id = f"item_{self.item_counter}"
                
                # Get or create current batch
                if not self.batches:
                    self.batch_counter += 1
                    batch_id = f"batch_{self.batch_counter}"
                    self.batches[batch_id] = Batch(batch_id, self.max_batch_size, self.batch_timeout)
                else:
                    batch_id = list(self.batches.keys())[-1]
                
                batch = self.batches[batch_id]
                item = BatchItem(item_id, data)
                
                if not batch.add_item(item):
                    # Current batch is full, create new
                    self.batch_counter += 1
                    batch_id = f"batch_{self.batch_counter}"
                    batch = Batch(batch_id, self.max_batch_size, self.batch_timeout)
                    self.batches[batch_id] = batch
                    batch.add_item(item)
                
                # Queue batch if ready
                if batch.is_ready():
                    await self.processing_queue.put(batch_id)
                    del self.batches[batch_id]
                
                return True, item_id, batch_id
        except Exception as e:
            print(f"Error submitting item: {e}")
            return False, "", str(e)
    
    async def _processor_loop(self) -> None:
        """Main processor loop"""
        while self.enabled:
            try:
                # Check for timeout-ready batches
                async with self.lock:
                    ready_batches = [
                        (bid, b) for bid, b in self.batches.items()
                        if b.is_ready()
                    ]
                    for batch_id, batch in ready_batches:
                        await self.processing_queue.put(batch_id)
                        del self.batches[batch_id]
                
                # Get next batch to process
                try:
                    batch_id = self.processing_queue.get_nowait()
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process batch
                async with self.lock:
                    if batch_id not in self.batches:
                        # Batch already moved to processing
                        pass
                
                # Get batch from processing_queue tracking
                await self.semaphore.acquire()
                
                if batch_id in self.batches:
                    batch = self.batches[batch_id]
                    task = asyncio.create_task(
                        self._process_batch(batch, batch_id)
                    )
                    self.processing_tasks[batch_id] = task
                else:
                    self.semaphore.release()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Processor loop error: {e}")
                await asyncio.sleep(1)
    
    async def _process_batch(self, batch: Batch, batch_id: str) -> None:
        """Process a single batch"""
        try:
            batch.status = BatchStatus.PROCESSING
            start_time = time.time()
            
            # Call batch handler
            result = await self.batch_handler(batch.items)
            
            processing_time = time.time() - start_time
            
            # Update statistics
            async with self.lock:
                self.completed_batches += 1
                self.processed_items += len(batch.items)
                self.total_processing_time += processing_time
                
                batch.status = BatchStatus.COMPLETED
            
            # Clean up
            del self.batches[batch_id]
            if batch_id in self.processing_tasks:
                del self.processing_tasks[batch_id]
            
            self.semaphore.release()
        
        except Exception as e:
            print(f"Batch processing error: {e}")
            
            async with self.lock:
                self.failed_batches += 1
                self.failed_items += len(batch.items)
                batch.status = BatchStatus.FAILED
            
            if batch_id in self.processing_tasks:
                del self.processing_tasks[batch_id]
            
            self.semaphore.release()
    
    async def get_statistics(self) -> BatchStatistics:
        """Get processor statistics"""
        try:
            async with self.lock:
                total_batches = self.completed_batches + self.failed_batches
                total_items = self.processed_items + self.failed_items
                
                avg_batch_size = (total_items / total_batches) if total_batches > 0 else 0
                avg_processing_time = (
                    self.total_processing_time / self.completed_batches
                ) if self.completed_batches > 0 else 0
                throughput = (
                    self.processed_items / self.total_processing_time
                ) if self.total_processing_time > 0 else 0
                
                return BatchStatistics(
                    total_batches=total_batches,
                    completed_batches=self.completed_batches,
                    failed_batches=self.failed_batches,
                    total_items=total_items,
                    processed_items=self.processed_items,
                    failed_items=self.failed_items,
                    avg_batch_size=round(avg_batch_size, 2),
                    avg_processing_time=round(avg_processing_time, 3),
                    throughput_items_per_sec=round(throughput, 2)
                )
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return BatchStatistics(0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)
    
    async def reset(self) -> bool:
        """Reset batch processor"""
        try:
            await self.disable()
            self.batches.clear()
            self.completed_batches = 0
            self.failed_batches = 0
            self.processed_items = 0
            self.failed_items = 0
            self.total_processing_time = 0.0
            self.item_counter = 0
            self.batch_counter = 0
            return True
        except Exception as e:
            print(f"Error resetting: {e}")
            return False
