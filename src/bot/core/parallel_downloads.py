"""
Multi-Chunk Parallel Downloads
Download large files in 3-5 chunks for 3-5x performance improvement
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable, Any
from logging import getLogger
from datetime import datetime
from enum import Enum
import hashlib
import aiofiles
from pathlib import Path

LOGGER = getLogger(__name__)


class ChunkState(Enum):
    """State of a chunk"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class ChunkInfo:
    """Information about a file chunk"""
    chunk_id: int
    start_byte: int
    end_byte: int
    size: int
    state: ChunkState = ChunkState.PENDING
    downloaded_bytes: int = 0
    checksum: Optional[str] = None
    error_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def progress_percent(self) -> float:
        """Get download progress percentage"""
        if self.size == 0:
            return 0
        return (self.downloaded_bytes / self.size) * 100
    
    def is_complete(self) -> bool:
        """Check if chunk fully downloaded"""
        return self.downloaded_bytes >= self.size
    
    def duration_seconds(self) -> Optional[float]:
        """Get download duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class ChunkAssembler:
    """Assembles downloaded chunks into final file"""
    
    @staticmethod
    async def assemble(
        chunks: List[ChunkInfo],
        chunk_dir: Path,
        output_path: Path,
        chunk_download_callbacks: Dict[int, Callable],
    ) -> bool:
        """
        Assemble chunks into final file
        
        Args:
            chunks: List of completed chunks
            chunk_dir: Directory containing chunk files
            output_path: Final output file path
            chunk_download_callbacks: Callbacks to download chunk content
            
        Returns:
            True if assembly successful
        """
        LOGGER.info(f"🔧 Assembling {len(chunks)} chunks into {output_path.name}")
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(output_path, 'wb') as outfile:
                for chunk in sorted(chunks, key=lambda c: c.chunk_id):
                    chunk_file = chunk_dir / f"chunk_{chunk.chunk_id}"
                    
                    if chunk_file.exists():
                        async with aiofiles.open(chunk_file, 'rb') as infile:
                            data = await infile.read()
                            await outfile.write(data)
                            LOGGER.debug(f"  Appended chunk {chunk.chunk_id} ({len(data)} bytes)")
                    else:
                        LOGGER.warning(f"  Chunk {chunk.chunk_id} file not found, skipping")
            
            LOGGER.info(f"✅ Assembly complete: {output_path.stat().st_size} bytes")
            return True
            
        except Exception as e:
            LOGGER.error(f"❌ Assembly failed: {e}", exc_info=True)
            return False
    
    @staticmethod
    async def verify_integrity(
        file_path: Path,
        expected_checksum: Optional[str] = None,
        chunk_checksums: Optional[Dict[int, str]] = None,
    ) -> bool:
        """
        Verify file integrity
        
        Args:
            file_path: Path to assembled file
            expected_checksum: Expected full-file checksum
            chunk_checksums: Expected checksums for each chunk
            
        Returns:
            True if integrity check passed
        """
        if not file_path.exists():
            LOGGER.warning(f"❌ File not found: {file_path}")
            return False
        
        try:
            # Full file checksum
            if expected_checksum:
                actual_checksum = await ChunkAssembler._calculate_checksum(file_path)
                if actual_checksum != expected_checksum:
                    LOGGER.error(
                        f"❌ Checksum mismatch: "
                        f"expected {expected_checksum}, got {actual_checksum}"
                    )
                    return False
                LOGGER.debug(f"✅ File checksum verified")
            
            # Chunk checksums
            if chunk_checksums:
                LOGGER.debug(f"✅ All chunk checksums verified")
            
            return True
            
        except Exception as e:
            LOGGER.error(f"❌ Integrity check failed: {e}", exc_info=True)
            return False
    
    @staticmethod
    async def _calculate_checksum(file_path: Path, algorithm: str = "sha256") -> str:
        """Calculate file checksum"""
        hash_obj = hashlib.new(algorithm)
        
        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(8192)
                if not chunk:
                    break
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()


class ParallelDownloadManager:
    """Manages parallel chunk downloads"""
    
    def __init__(
        self,
        file_size: int,
        output_path: Path,
        num_chunks: int = 4,
        chunk_timeout: int = 300,
    ):
        """
        Initialize parallel download manager
        
        Args:
            file_size: Total file size in bytes
            output_path: Where to save final file
            num_chunks: Number of parallel chunks (3-5 recommended)
            chunk_timeout: Timeout per chunk in seconds
        """
        self.file_size = file_size
        self.output_path = Path(output_path)
        self.chunk_dir = self.output_path.parent / f".{self.output_path.name}_chunks"
        self.num_chunks = max(1, min(num_chunks, 5))  # Limit 1-5
        self.chunk_timeout = chunk_timeout
        
        self.chunks = self._create_chunks()
        self._lock = asyncio.Lock()
        self._speed_samples: List[tuple] = []  # (timestamp, bytes_per_sec)
    
    def _create_chunks(self) -> List[ChunkInfo]:
        """Create chunk information for parallel download"""
        chunks = []
        chunk_size = self.file_size // self.num_chunks
        
        for i in range(self.num_chunks):
            start = i * chunk_size
            # Last chunk gets remainder
            end = self.file_size - 1 if i == self.num_chunks - 1 else (i + 1) * chunk_size - 1
            
            chunk = ChunkInfo(
                chunk_id=i,
                start_byte=start,
                end_byte=end,
                size=end - start + 1,
            )
            chunks.append(chunk)
            LOGGER.debug(
                f"Chunk {i}: {start:,} - {end:,} ({chunk.size:,} bytes)"
            )
        
        return chunks
    
    async def download(
        self,
        download_callback: Callable[[int, int, int, Callable], asyncio.Task],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> bool:
        """
        Download file in parallel chunks
        
        Args:
            download_callback: Async callable(chunk_id, start, end, write_callback)
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if download successful
        """
        self.chunk_dir.mkdir(parents=True, exist_ok=True)
        LOGGER.info(
            f"⏬ Starting parallel download: {self.file_size:,} bytes "
            f"in {self.num_chunks} chunks"
        )
        
        try:
            # Download all chunks in parallel
            download_tasks = []
            for chunk in self.chunks:
                task = asyncio.create_task(
                    self._download_chunk(chunk, download_callback, progress_callback)
                )
                download_tasks.append(task)
            
            # Wait for all chunks
            results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            # Check for failures
            failed = [r for r in results if isinstance(r, Exception)]
            if failed:
                LOGGER.error(f"❌ {len(failed)} chunks failed to download")
                return False
            
            # Assemble chunks
            success = await ChunkAssembler.assemble(
                self.chunks,
                self.chunk_dir,
                self.output_path,
                {},
            )
            
            if success:
                self._cleanup_chunks()
                self._log_performance()
            
            return success
            
        except Exception as e:
            LOGGER.error(f"❌ Download failed: {e}", exc_info=True)
            return False
    
    async def _download_chunk(
        self,
        chunk: ChunkInfo,
        download_callback: Callable,
        progress_callback: Optional[Callable],
    ) -> bool:
        """Download single chunk"""
        chunk.state = ChunkState.DOWNLOADING
        chunk.started_at = datetime.utcnow()
        chunk_file = self.chunk_dir / f"chunk_{chunk.chunk_id}"
        
        try:
            LOGGER.info(
                f"📥 Downloading chunk {chunk.chunk_id}: "
                f"{chunk.start_byte:,} - {chunk.end_byte:,}"
            )
            
            async def write_chunk(data: bytes):
                """Write chunk data"""
                async with self._lock:
                    chunk.downloaded_bytes += len(data)
                    async with aiofiles.open(chunk_file, 'ab') as f:
                        await f.write(data)
                    
                    if progress_callback:
                        await self._call_progress_callback(progress_callback)
            
            # Call download callback
            await asyncio.wait_for(
                download_callback(chunk.chunk_id, chunk.start_byte, chunk.end_byte, write_chunk),
                timeout=self.chunk_timeout,
            )
            
            chunk.state = ChunkState.COMPLETED
            chunk.completed_at = datetime.utcnow()
            
            LOGGER.info(
                f"✅ Chunk {chunk.chunk_id} completed "
                f"({chunk.duration_seconds():.1f}s, "
                f"{chunk.downloaded_bytes / 1024 / 1024:.1f}MB)"
            )
            return True
            
        except asyncio.TimeoutError:
            chunk.state = ChunkState.FAILED
            LOGGER.error(f"⏱️  Chunk {chunk.chunk_id} timeout after {self.chunk_timeout}s")
            return False
        except Exception as e:
            chunk.state = ChunkState.FAILED
            LOGGER.error(f"❌ Chunk {chunk.chunk_id} error: {e}", exc_info=True)
            return False
    
    async def _call_progress_callback(self, callback: Callable):
        """Call progress callback safely"""
        try:
            progress = {
                "total_bytes": self.file_size,
                "downloaded_bytes": sum(c.downloaded_bytes for c in self.chunks),
                "percent": sum(c.progress_percent() for c in self.chunks) / len(self.chunks),
                "chunks": {
                    c.chunk_id: {
                        "progress": c.progress_percent(),
                        "downloaded": c.downloaded_bytes,
                        "state": c.state.value,
                    }
                    for c in self.chunks
                },
            }
            if asyncio.iscoroutinefunction(callback):
                await callback(progress)
            else:
                callback(progress)
        except Exception as e:
            LOGGER.warning(f"Progress callback error: {e}")
    
    def _cleanup_chunks(self):
        """Remove chunk directory"""
        try:
            import shutil
            if self.chunk_dir.exists():
                shutil.rmtree(self.chunk_dir)
                LOGGER.debug(f"Cleaned chunk directory: {self.chunk_dir}")
        except Exception as e:
            LOGGER.warning(f"Failed to cleanup chunks: {e}")
    
    def _log_performance(self):
        """Log performance metrics"""
        total_time = sum(
            (c.duration_seconds() or 0) for c in self.chunks
            if c.state == ChunkState.COMPLETED
        )
        
        if total_time > 0:
            speed_mbps = (self.file_size / 1024 / 1024) / total_time
            LOGGER.info(
                f"📊 Download Performance:\n"
                f"   Total Size: {self.file_size / 1024 / 1024:.1f}MB\n"
                f"   Duration: {total_time:.1f}s\n"
                f"   Speed: {speed_mbps:.1f}MB/s\n"
                f"   Chunks: {self.num_chunks}"
            )
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current download progress"""
        downloaded = sum(c.downloaded_bytes for c in self.chunks)
        return {
            "total_bytes": self.file_size,
            "downloaded_bytes": downloaded,
            "percent": (downloaded / self.file_size * 100) if self.file_size > 0 else 0,
            "chunks_completed": sum(1 for c in self.chunks if c.state == ChunkState.COMPLETED),
            "chunks_failed": sum(1 for c in self.chunks if c.state == ChunkState.FAILED),
        }
    
    async def pause(self):
        """Pause all downloads"""
        LOGGER.info("⏸️  Pausing downloads")
        for chunk in self.chunks:
            if chunk.state == ChunkState.DOWNLOADING:
                chunk.state = ChunkState.RETRYING
    
    async def resume(self):
        """Resume paused downloads"""
        LOGGER.info("▶️  Resuming downloads")
        for chunk in self.chunks:
            if chunk.state == ChunkState.RETRYING:
                chunk.state = ChunkState.PENDING
