"""Backward-compatible imports for mmap APIs."""

from .mmap import (
    MMapCopier,
    MMapHasher,
    MMapInfo,
    MMapMode,
    MMapProcessor,
    MMapSearcher,
    MemoryMappedFile,
    ProcessStats,
    copy_large_file,
    hash_large_file,
    process_large_file,
    search_in_file,
)

__all__ = [
    "MMapMode",
    "MMapInfo",
    "ProcessStats",
    "MemoryMappedFile",
    "MMapProcessor",
    "MMapHasher",
    "MMapCopier",
    "MMapSearcher",
    "hash_large_file",
    "copy_large_file",
    "search_in_file",
    "process_large_file",
]
