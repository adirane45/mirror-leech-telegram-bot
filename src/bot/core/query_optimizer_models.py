"""
Query Optimizer Models
Data structures for query analysis, statistics, and optimization results
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, UTC


class QueryType(Enum):
    """Types of queries"""
    SELECT = "SELECT"
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    GRAPHQL = "GRAPHQL"
    UNKNOWN = "UNKNOWN"


@dataclass
class OptimizationResult:
    """Result of query optimization analysis"""
    query: str
    query_type: QueryType
    execution_time_ms: Optional[float] = None
    estimated_improvement_percent: float = 0.0
    n_plus_one_detected: bool = False
    recommendations: List[str] = field(default_factory=list)
    optimized_query: Optional[str] = None
    cache_suggestion: bool = False
    index_suggestions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class QueryStatistics:
    """Statistics about query execution"""
    query_hash: str
    query: str
    execution_count: int = 0
    total_execution_time_ms: float = 0.0
    avg_execution_time_ms: float = 0.0
    min_execution_time_ms: float = float('inf')
    max_execution_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_executed: Optional[datetime] = None
