"""
Memory-Mapped Files (mmap) for Phase 9 Enterprise Features

Efficient large file handling using memory-mapped I/O.

Features:
- Memory-mapped file access
- Efficient streaming
- Large file support (multi-GB)
- Platform-specific optimizations
- Chunk-based processing
"""

import asyncio
import logging
import mmap
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Callable, Any
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class MMapMode(str, Enum):
    """Memory map access modes"""
    READ_ONLY = "r"
    READ_WRITE = "r+"
    COPY_ON_WRITE = "c"


@dataclass
class MMapInfo:
    """Memory map information"""
    file_path: str
    size: int
    mode: MMapMode
    offset: int
    length: int
    page_aligned: bool
    created_at: datetime


@dataclass
class ProcessStats:
    """Processing statistics"""
    bytes_processed: int
    chunks_processed: int
    duration_seconds: float
    throughput_mbps: float
    memory_peak_mb: float


class MemoryMappedFile:
    """
    Memory-mapped file handler.
    
    Features:
    - Efficient large file access
    - Platform-specific optimizations
    - Automatic memory management
    - Chunked processing support
    """
    
    def __init__(
        self,
        file_path: str,
        mode: MMapMode = MMapMode.READ_ONLY,
        length: Optional[int] = None,
        offset: int = 0
    ):
        """
        Initialize memory-mapped file.
        
        Args:
            file_path: Path to file
            mode: Access mode
            length: Bytes to map (None = entire file)
            offset: Offset in file
        """
        self.file_path = file_path
        self.mode = mode
        self.offset = offset
        
        self.file_handle: Optional[Any] = None
        self.mmap_obj: Optional[mmap.mmap] = None
        self.file_size = 0
        self.map_length = length
        
        logger.info(f"MemoryMappedFile initialized: {file_path} (mode={mode})")
    
    async def open(self):
        """Open and map file"""
        # Get file size
        self.file_size = os.path.getsize(self.file_path)
        
        # Calculate map length
        if self.map_length is None:
            self.map_length = self.file_size - self.offset
        
        # Open file
        mode_str = "rb" if self.mode == MMapMode.READ_ONLY else "r+b"
        self.file_handle = open(self.file_path, mode_str)
        
        # Create memory map
        access = {
            MMapMode.READ_ONLY: mmap.ACCESS_READ,
            MMapMode.READ_WRITE: mmap.ACCESS_WRITE,
            MMapMode.COPY_ON_WRITE: mmap.ACCESS_COPY
        }[self.mode]
        
        self.mmap_obj = mmap.mmap(
            self.file_handle.fileno(),
            length=self.map_length,
            access=access,
            offset=self.offset
        )
        
        logger.info(
            f"Mapped {self.map_length:,} bytes "
            f"({self.file_size:,} total)"
        )
    
    async def read(self, position: int, size: int) -> bytes:
        """
        Read from mapped memory.
        
        Args:
            position: Position in file
            size: Bytes to read
            
        Returns:
            Data bytes
        """
        if self.mmap_obj is None:
            await self.open()
        
        self.mmap_obj.seek(position)
        data = self.mmap_obj.read(size)
        
        return data
    
    async def write(self, position: int, data: bytes):
        """
        Write to mapped memory.
        
        Args:
            position: Position in file
            data: Data to write
        """
        if self.mmap_obj is None:
            await self.open()
        
        if self.mode == MMapMode.READ_ONLY:
            raise ValueError("Cannot write in read-only mode")
        
        self.mmap_obj.seek(position)
        self.mmap_obj.write(data)
    
    async def read_chunk(self, chunk_size: int, position: int = 0) -> bytes:
        """
        Read chunk from file.
        
        Args:
            chunk_size: Size of chunk
            position: Starting position
            
        Returns:
            Chunk data
        """
        return await self.read(position, chunk_size)
    
    async def iter_chunks(self, chunk_size: int = 8 * 1024 * 1024):
        """
        Iterate through file in chunks.
        
        Args:
            chunk_size: Size of each chunk (default 8 MB)
            
        Yields:
            Data chunks
        """
        if self.mmap_obj is None:
            await self.open()
        
        position = 0
        
        while position < self.map_length:
            size = min(chunk_size, self.map_length - position)
            chunk = await self.read(position, size)
            
            yield chunk
            
            position += size
    
    def search(self, pattern: bytes) -> List[int]:
        """
        Search for byte pattern in mapped memory.
        
        Args:
            pattern: Byte pattern to find
            
        Returns:
            List of positions where pattern found
        """
        if self.mmap_obj is None:
            raise RuntimeError("File not mapped")
        
        positions = []
        start = 0
        
        while True:
            pos = self.mmap_obj.find(pattern, start)
            if pos == -1:
                break
            
            positions.append(pos)
            start = pos + 1
        
        logger.debug(f"Found pattern at {len(positions)} positions")
        
        return positions
    
    async def close(self):
        """Close mapped file"""
        if self.mmap_obj:
            self.mmap_obj.close()
            self.mmap_obj = None
        
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        
        logger.info(f"Closed memory map: {self.file_path}")
    
    async def __aenter__(self):
        """Async context manager enter"""
        await self.open()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


class MMapProcessor:
    """
    Processor for memory-mapped files.
    
    Features:
    - Parallel chunk processing
    - Progress tracking
    - Custom processing functions
    - Resource management
    """
    
    def __init__(
        self,
        chunk_size: int = 16 * 1024 * 1024,  # 16 MB default
        max_concurrent: int = 4
    ):
        """
        Initialize mmap processor.
        
        Args:
            chunk_size: Size of processing chunks
            max_concurrent: Max concurrent chunks
        """
        self.chunk_size = chunk_size
        self.max_concurrent = max_concurrent
        
        self.stats = {
            "bytes_processed": 0,
            "chunks_processed": 0,
            "processing_time": 0.0
        }
        
        logger.info(f"MMapProcessor initialized: chunk_size={chunk_size:,}")
    
    async def process_file(
        self,
        file_path: str,
        processor_func: Callable[[bytes, int], Any],
        mode: MMapMode = MMapMode.READ_ONLY
    ) -> ProcessStats:
        """
        Process file using memory mapping.
        
        Args:
            file_path: Path to file
            processor_func: Function to process each chunk
            mode: File access mode
            
        Returns:
            ProcessStats
        """
        import time
        start_time = time.perf_counter()
        
        mmap_file = MemoryMappedFile(file_path, mode)
        
        async with mmap_file:
            chunk_num = 0
            tasks = []
            
            async for chunk in mmap_file.iter_chunks(self.chunk_size):
                # Process chunk
                task = asyncio.create_task(
                    self._process_chunk(chunk, chunk_num, processor_func)
                )
                tasks.append(task)
                
                chunk_num += 1
                self.stats["bytes_processed"] += len(chunk)
                
                # Limit concurrent tasks
                if len(tasks) >= self.max_concurrent:
                    await asyncio.gather(*tasks)
                    tasks = []
            
            # Process remaining tasks
            if tasks:
                await asyncio.gather(*tasks)
        
        duration = time.perf_counter() - start_time
        throughput = (self.stats["bytes_processed"] / duration) / (1024 * 1024)
        
        self.stats["processing_time"] = duration
        
        logger.info(
            f"Processed {self.stats['bytes_processed']:,} bytes in {duration:.2f}s "
            f"({throughput:.2f} MB/s)"
        )
        
        return ProcessStats(
            bytes_processed=self.stats["bytes_processed"],
            chunks_processed=chunk_num,
            duration_seconds=duration,
            throughput_mbps=throughput,
            memory_peak_mb=self.chunk_size / (1024 * 1024)
        )
    
    async def _process_chunk(
        self,
        chunk: bytes,
        chunk_num: int,
        processor_func: Callable[[bytes, int], Any]
    ):
        """Process a single chunk"""
        try:
            await asyncio.to_thread(processor_func, chunk, chunk_num)
            self.stats["chunks_processed"] += 1
            
        except Exception as e:
            logger.error(f"Error processing chunk {chunk_num}: {e}")


class MMapHasher:
    """
    Fast file hashing using memory-mapped I/O.
    
    Optimized for large files.
    """
    
    def __init__(self, algorithm: str = "sha256"):
        """
        Initialize mmap hasher.
        
        Args:
            algorithm: Hash algorithm
        """
        self.algorithm = algorithm
        
        logger.info(f"MMapHasher initialized: algorithm={algorithm}")
    
    async def hash_file(
        self,
        file_path: str,
        chunk_size: int = 64 * 1024 * 1024  # 64 MB chunks
    ) -> str:
        """
        Hash file using memory-mapped I/O.
        
        Args:
            file_path: Path to file
            chunk_size: Size of chunks to hash
            
        Returns:
            Hex digest of hash
        """
        import time
        start_time = time.perf_counter()
        
        hasher = hashlib.new(self.algorithm)
        mmap_file = MemoryMappedFile(file_path, MMapMode.READ_ONLY)
        
        async with mmap_file:
            async for chunk in mmap_file.iter_chunks(chunk_size):
                hasher.update(chunk)
        
        duration = time.perf_counter() - start_time
        file_size = os.path.getsize(file_path)
        throughput = (file_size / duration) / (1024 * 1024)
        
        digest = hasher.hexdigest()
        
        logger.info(
            f"Hashed {file_size:,} bytes in {duration:.2f}s "
            f"({throughput:.2f} MB/s): {digest[:16]}..."
        )
        
        return digest


class MMapCopier:
    """
    Fast file copying using memory-mapped I/O.
    
    Optimized for large files with minimal memory overhead.
    """
    
    def __init__(self):
        """Initialize mmap copier"""
        logger.info("MMapCopier initialized")
    
    async def copy_file(
        self,
        source_path: str,
        dest_path: str,
        chunk_size: int = 32 * 1024 * 1024  # 32 MB chunks
    ) -> ProcessStats:
        """
        Copy file using memory-mapped I/O.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            chunk_size: Copy chunk size
            
        Returns:
            ProcessStats
        """
        import time
        start_time = time.perf_counter()
        
        # Get source size
        file_size = os.path.getsize(source_path)
        
        # Create destination file
        with open(dest_path, 'wb') as dest:
            dest.write(b'\x00' * file_size)  # Pre-allocate
        
        # Open both files as memory-mapped
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
        throughput = (file_size / duration) / (1024 * 1024)
        
        logger.info(
            f"Copied {file_size:,} bytes in {duration:.2f}s "
            f"({throughput:.2f} MB/s)"
        )
        
        return ProcessStats(
            bytes_processed=file_size,
            chunks_processed=chunks,
            duration_seconds=duration,
            throughput_mbps=throughput,
            memory_peak_mb=chunk_size / (1024 * 1024)
        )


class MMapSearcher:
    """
    Fast binary search in large files using memory-mapped I/O.
    """
    
    def __init__(self):
        """Initialize mmap searcher"""
        logger.info("MMapSearcher initialized")
    
    async def search_file(
        self,
        file_path: str,
        pattern: bytes
    ) -> List[int]:
        """
        Search for byte pattern in file.
        
        Args:
            file_path: Path to file
            pattern: Byte pattern to search for
            
        Returns:
            List of positions where pattern found
        """
        import time
        start_time = time.perf_counter()
        
        mmap_file = MemoryMappedFile(file_path, MMapMode.READ_ONLY)
        
        async with mmap_file:
            positions = mmap_file.search(pattern)
        
        duration = time.perf_counter() - start_time
        file_size = os.path.getsize(file_path)
        
        logger.info(
            f"Searched {file_size:,} bytes in {duration:.2f}s: "
            f"found {len(positions)} matches"
        )
        
        return positions
    
    async def replace_pattern(
        self,
        file_path: str,
        old_pattern: bytes,
        new_pattern: bytes
    ) -> int:
        """
        Replace byte pattern in file.
        
        Args:
            file_path: Path to file
            old_pattern: Pattern to replace
            new_pattern: Replacement pattern
            
        Returns:
            Number of replacements made
        """
        if len(old_pattern) != len(new_pattern):
            raise ValueError("Pattern lengths must match")
        
        import time
        start_time = time.perf_counter()
        
        mmap_file = MemoryMappedFile(file_path, MMapMode.READ_WRITE)
        
        async with mmap_file:
            positions = mmap_file.search(old_pattern)
            
            # Replace each occurrence
            for pos in positions:
                await mmap_file.write(pos, new_pattern)
        
        duration = time.perf_counter() - start_time
        
        logger.info(
            f"Replaced {len(positions)} occurrences in {duration:.2f}s"
        )
        
        return len(positions)


# Convenience functions
async def hash_large_file(file_path: str, algorithm: str = "sha256") -> str:
    """Quick hash of large file"""
    hasher = MMapHasher(algorithm)
    return await hasher.hash_file(file_path)


async def copy_large_file(source_path: str, dest_path: str) -> ProcessStats:
    """Quick copy of large file"""
    copier = MMapCopier()
    return await copier.copy_file(source_path, dest_path)


async def search_in_file(file_path: str, pattern: bytes) -> List[int]:
    """Quick search in file"""
    searcher = MMapSearcher()
    return await searcher.search_file(file_path, pattern)


async def process_large_file(
    file_path: str,
    processor: Callable[[bytes, int], Any]
) -> ProcessStats:
    """Quick processing of large file"""
    proc = MMapProcessor()
    return await proc.process_file(file_path, processor)
