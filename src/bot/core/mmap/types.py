from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MMapMode(str, Enum):
    READ_ONLY = "r"
    READ_WRITE = "r+"
    COPY_ON_WRITE = "c"


@dataclass
class MMapInfo:
    file_path: str
    size: int
    mode: MMapMode
    offset: int
    length: int
    page_aligned: bool
    created_at: datetime


@dataclass
class ProcessStats:
    bytes_processed: int
    chunks_processed: int
    duration_seconds: float
    throughput_mbps: float
    memory_peak_mb: float
