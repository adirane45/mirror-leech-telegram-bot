from collections.abc import Callable
from typing import Any

from .operations import MMapCopier, MMapHasher, MMapSearcher
from .processor import MMapProcessor
from .types import ProcessStats


async def hash_large_file(file_path: str, algorithm: str = "sha256") -> str:
    hasher = MMapHasher(algorithm)
    return await hasher.hash_file(file_path)


async def copy_large_file(source_path: str, dest_path: str) -> ProcessStats:
    copier = MMapCopier()
    return await copier.copy_file(source_path, dest_path)


async def search_in_file(file_path: str, pattern: bytes) -> list[int]:
    searcher = MMapSearcher()
    return await searcher.search_file(file_path, pattern)


async def process_large_file(
    file_path: str,
    processor: Callable[[bytes, int], Any],
) -> ProcessStats:
    proc = MMapProcessor()
    return await proc.process_file(file_path, processor)
