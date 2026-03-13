import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from .file_map import MemoryMappedFile
from .types import MMapMode, ProcessStats

logger = logging.getLogger(__name__)


class MMapProcessor:
    def __init__(self, chunk_size: int = 16 * 1024 * 1024, max_concurrent: int = 4) -> None:
        self.chunk_size = chunk_size
        self.max_concurrent = max_concurrent
        self.stats: dict[str, float | int] = {
            "bytes_processed": 0,
            "chunks_processed": 0,
            "processing_time": 0.0,
        }
        logger.info(f"MMapProcessor initialized: chunk_size={chunk_size:,}")

    async def process_file(
        self,
        file_path: str,
        processor_func: Callable[[bytes, int], Any],
        mode: MMapMode = MMapMode.READ_ONLY,
    ) -> ProcessStats:
        start_time = time.perf_counter()
        mmap_file = MemoryMappedFile(file_path, mode)

        async with mmap_file:
            chunk_num = 0
            tasks: list[asyncio.Task[None]] = []

            async for chunk in mmap_file.iter_chunks(self.chunk_size):
                tasks.append(asyncio.create_task(self._process_chunk(chunk, chunk_num, processor_func)))
                chunk_num += 1
                self.stats["bytes_processed"] = int(self.stats["bytes_processed"]) + len(chunk)

                if len(tasks) >= self.max_concurrent:
                    await asyncio.gather(*tasks)
                    tasks = []

            if tasks:
                await asyncio.gather(*tasks)

        duration = time.perf_counter() - start_time
        bytes_processed = int(self.stats["bytes_processed"])
        throughput = (bytes_processed / duration) / (1024 * 1024) if duration > 0 else 0.0
        self.stats["processing_time"] = duration

        logger.info(
            f"Processed {bytes_processed:,} bytes in {duration:.2f}s ({throughput:.2f} MB/s)"
        )

        return ProcessStats(
            bytes_processed=bytes_processed,
            chunks_processed=chunk_num,
            duration_seconds=duration,
            throughput_mbps=throughput,
            memory_peak_mb=self.chunk_size / (1024 * 1024),
        )

    async def _process_chunk(
        self,
        chunk: bytes,
        chunk_num: int,
        processor_func: Callable[[bytes, int], Any],
    ) -> None:
        try:
            await asyncio.to_thread(processor_func, chunk, chunk_num)
            self.stats["chunks_processed"] = int(self.stats["chunks_processed"]) + 1
        except Exception as error:
            logger.error(f"Error processing chunk {chunk_num}: {error}")
