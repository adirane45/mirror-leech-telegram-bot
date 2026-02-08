"""
Batch Processor Models
Data structures for batch processing
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional
from datetime import datetime


@dataclass
class BatchItem:
    """Item to be processed in batch"""
    item_id: str
    data: Any
    created_at: datetime = field(default_factory=datetime.now)
    priority: int = 0  # Higher priority items processed first


@dataclass
class Batch:
    """Batch container"""
    batch_id: str
    items: List[BatchItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    dispatched_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, dispatched, completed, failed
