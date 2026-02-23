"""
Phase 4: Batch Processor
Process multiple items efficiently through batching
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4
import logging

from .batch_processor_models import BatchItem, Batch

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Singleton batch processor for efficient bulk operation handling
    """

    _instance: Optional['BatchProcessor'] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self.enabled = False
        self.pending_items: List[BatchItem] = []
        self.batches: Dict[str, Batch] = {}
        self.current_batch: Optional[Batch] = None
        
        # Configuration
        self.max_batch_size = 100
        self.batch_timeout_seconds = 5.0
        self.process_handler: Optional[Callable] = None
        
        # Statistics
        self.total_items_processed = 0
        self.total_batches_processed = 0
        self.failed_items = 0
        
        # Internal
        self.processor_task: Optional[asyncio.Task] = None
        self.last_batch_dispatch = time.time()

    @classmethod
    def get_instance(cls) -> 'BatchProcessor':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = BatchProcessor()
        return cls._instance

    async def enable(
        self,
        process_handler: Optional[Callable] = None,
        max_batch_size: int = 100,
        batch_timeout: float = 5.0
    ) -> bool:
        """
        Enable the Batch Processor
        
        Args:
            process_handler: Async function to handle batch processing
            max_batch_size: Maximum items per batch
            batch_timeout: Max wait time before processing partial batch
            
        Returns:
            Success status
        """
        async with self._lock:
            self.enabled = True
            self.process_handler = process_handler
            self.max_batch_size = max_batch_size
            self.batch_timeout_seconds = batch_timeout
            
            # Start processor task
            if self.processor_task is None:
                self.processor_task = asyncio.create_task(self._process_batches_loop())
            
            logger.info(
                f"Batch Processor enabled "
                f"(batch_size={max_batch_size}, timeout={batch_timeout}s)"
            )
            return True

    async def disable(self) -> bool:
        """Disable the Batch Processor"""
        async with self._lock:
            self.enabled = False
            
            # Cancel processor task
            if self.processor_task:
                self.processor_task.cancel()
                self.processor_task = None
            
            logger.info("Batch Processor disabled")
            return True

    async def submit_item(
        self,
        data: Any,
        priority: int = 0
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Submit item to batch processor
        
        Args:
            data: Item data to process
            priority: Item priority (higher = process sooner)
            
        Returns:
            Tuple of (success, item_id, batch_id or None)
        """
        if not self.enabled:
            logger.warning("Batch Processor not enabled")
            return False, "", None

        try:
            item_id = str(uuid4())
            item = BatchItem(item_id=item_id, data=data, priority=priority)
            
            # Add to pending items (sorted by priority)
            self.pending_items.append(item)
            self.pending_items.sort(key=lambda x: -x.priority)  # Higher priority first
            
            logger.debug(f"Submitted item {item_id} to batch processor")
            
            # Get current batch ID if dispatched yet
            batch_id = self.current_batch.batch_id if self.current_batch else None
            
            # Check if batch should be dispatched
            if len(self.pending_items) >= self.max_batch_size:
                await self._dispatch_batch()
                batch_id = self.current_batch.batch_id if self.current_batch else batch_id
            
            return True, item_id, batch_id
            
        except Exception as e:
            logger.error(f"Error submitting item: {e}")
            self.failed_items += 1
            return False, "", None

    async def _dispatch_batch(self) -> bool:
        """Dispatch current batch for processing"""
        if not self.pending_items:
            return False

        try:
            # Create new batch
            batch = Batch(batch_id=str(uuid4()))
            batch.items = self.pending_items[:]
            self.pending_items = []
            
            batch.dispatched_at = datetime.now()
            batch.status = "dispatched"
            
            self.batches[batch.batch_id] = batch
            self.current_batch = batch
            
            logger.info(f"Dispatched batch {batch.batch_id} with {len(batch.items)} items")
            
            # Process batch
            if self.process_handler:
                try:
                    result = await self.process_handler(batch.items)
                    batch.status = "completed"
                    batch.completed_at = datetime.now()
                    self.total_items_processed += len(batch.items)
                    self.total_batches_processed += 1
                    logger.info(f"Completed batch {batch.batch_id}")
                except Exception as e:
                    batch.status = "failed"
                    batch.completed_at = datetime.now()
                    logger.error(f"Error processing batch {batch.batch_id}: {e}")
                    self.failed_items += len(batch.items)
            
            return True
            
        except Exception as e:
            logger.error(f"Error dispatching batch: {e}")
            return False

    async def _process_batches_loop(self) -> None:
        """Background task to dispatch batches on timeout"""
        while self.enabled:
            try:
                await asyncio.sleep(0.5)  # Check every 500ms
                
                # Check if batch should timeout
                if self.pending_items:
                    elapsed = time.time() - self.last_batch_dispatch
                    if elapsed >= self.batch_timeout_seconds:
                        await self._dispatch_batch()
                        self.last_batch_dispatch = time.time()
                        
            except Exception as e:
                logger.error(f"Error in process batches loop: {e}")

    async def flush(self) -> bool:
        """
        Flush any pending items immediately
        
        Returns:
            Success status
        """
        try:
            if self.pending_items:
                await self._dispatch_batch()
            return True
        except Exception as e:
            logger.error(f"Error flushing batches: {e}")
            return False

    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific batch"""
        if batch_id not in self.batches:
            return None
        
        batch = self.batches[batch_id]
        return {
            'batch_id': batch.batch_id,
            'status': batch.status,
            'item_count': len(batch.items),
            'created_at': batch.created_at.isoformat(),
            'dispatched_at': batch.dispatched_at.isoformat() if batch.dispatched_at else None,
            'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
            'processing_time_seconds': (
                (batch.completed_at - batch.dispatched_at).total_seconds()
                if batch.dispatched_at and batch.completed_at else None
            )
        }

    async def get_statistics(self) -> Dict[str, Any]:
        """Get batch processor statistics"""
        pending_count = len(self.pending_items)
        completed_batches = sum(
            1 for b in self.batches.values() if b.status == 'completed'
        )
        pending_batches = sum(
            1 for b in self.batches.values() if b.status in ['pending', 'dispatched']
        )
        
        return {
            'enabled': self.enabled,
            'pending_items': pending_count,
            'pending_batches': pending_batches,
            'completed_batches': completed_batches,
            'total_items_processed': self.total_items_processed,
            'total_batches_processed': self.total_batches_processed,
            'failed_items': self.failed_items,
            'max_batch_size': self.max_batch_size,
            'batch_timeout_seconds': self.batch_timeout_seconds,
            'throughput_items_per_sec': (
                self.total_items_processed / self.total_batches_processed
                if self.total_batches_processed > 0 else 0.0
            )
        }
