import asyncio
import hashlib
import logging
import time
from pathlib import Path

from .file_map import MemoryMappedFile
from .types import MMapMode, ProcessStats
from .utils import preallocate_file_sync

logger = logging.getLogger(__name__)


class MMapHasher:
    def __init__(self, algorithm: str = "sha256") -> None:
        self.algorithm = algorithm
        logger.info(f"MMapHasher initialized: algorithm={algorithm}")

    async def hash_file(self, file_path: str, chunk_size: int = 64 * 1024 * 1024) -> str:
        start_time = time.perf_counter()
        hasher = hashlib.new(self.algorithm)
        mmap_file = MemoryMappedFile(file_path, MMapMode.READ_ONLY)

        async with mmap_file:
            async for chunk in mmap_file.iter_chunks(chunk_size):
                hasher.update(chunk)

        duration = time.perf_counter() - start_time
        file_size = (await asyncio.to_thread(Path(file_path).stat)).st_size
        throughput = (file_size / duration) / (1024 * 1024) if duration > 0 else 0.0

        digest = hasher.hexdigest()
        logger.info(
            f"Hashed {file_size:,} bytes in {duration:.2f}s ({throughput:.2f} MB/s): {digest[:16]}..."
        )
        return digest


class MMapCopier:
    def __init__(self) -> None:
        logger.info("MMapCopier initialized")

    async def copy_file(
        self,
        source_path: str,
        dest_path: str,
        chunk_size: int = 32 * 1024 * 1024,
    ) -> ProcessStats:
        start_time = time.perf_counter()
        file_size = (await asyncio.to_thread(Path(source_path).stat)).st_size

        if file_size == 0:
            await asyncio.to_thread(preallocate_file_sync, dest_path, 0)
            duration = time.perf_counter() - start_time
            return ProcessStats(0, 0, duration, 0.0, 0.0)

        await asyncio.to_thread(preallocate_file_sync, dest_path, file_size)

        source_mmap = MemoryMappedFile(source_path, MMapMode.READ_ONLY)
        dest_mmap = MemoryMappedFile(dest_path, MMapMode.READ_WRITE)

        async with source_mmap, dest_mmap:
            position = 0
            chunks = 0
            async for chunk in source_mmap.iter_chunks(chunk_size):
                await dest_mmap.write(position, chunk)
                position += len(chunk)
                chunks += 1

        duration = time.perf_counter() - start_time
        throughput = (file_size / duration) / (1024 * 1024) if duration > 0 else 0.0
        logger.info(
            f"Copied {file_size:,} bytes in {duration:.2f}s ({throughput:.2f} MB/s)"
        )

        return ProcessStats(
            bytes_processed=file_size,
            chunks_processed=chunks,
            duration_seconds=duration,
            throughput_mbps=throughput,
            memory_peak_mb=chunk_size / (1024 * 1024),
        )


class MMapSearcher:
    def __init__(self) -> None:
        logger.info("MMapSearcher initialized")

    async def search_file(self, file_path: str, pattern: bytes) -> list[int]:
        start_time = time.perf_counter()
        mmap_file = MemoryMappedFile(file_path, MMapMode.READ_ONLY)

        async with mmap_file:
            positions = mmap_file.search(pattern)

        duration = time.perf_counter() - start_time
        file_size = (await asyncio.to_thread(Path(file_path).stat)).st_size
        logger.info(
            f"Searched {file_size:,} bytes in {duration:.2f}s: found {len(positions)} matches"
        )
        return positions

    async def replace_pattern(
        self,
        file_path: str,
        old_pattern: bytes,
        new_pattern: bytes,
    ) -> int:
        if len(old_pattern) != len(new_pattern):
            raise ValueError("Pattern lengths must match")

        start_time = time.perf_counter()
        mmap_file = MemoryMappedFile(file_path, MMapMode.READ_WRITE)

        async with mmap_file:
            positions = mmap_file.search(old_pattern)
            for position in positions:
                await mmap_file.write(position, new_pattern)

        duration = time.perf_counter() - start_time
        logger.info(f"Replaced {len(positions)} occurrences in {duration:.2f}s")
        return len(positions)
