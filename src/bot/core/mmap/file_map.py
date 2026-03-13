import asyncio
import logging
import mmap
from collections.abc import AsyncGenerator
from pathlib import Path
from types import TracebackType
from typing import BinaryIO

from .types import MMapMode

logger = logging.getLogger(__name__)


class MemoryMappedFile:
    def __init__(
        self,
        file_path: str,
        mode: MMapMode = MMapMode.READ_ONLY,
        length: int | None = None,
        offset: int = 0,
    ) -> None:
        self.file_path = file_path
        self.mode = mode
        self.offset = offset
        self.file_handle: BinaryIO | None = None
        self.mmap_obj: mmap.mmap | None = None
        self.file_size = 0
        self.map_length = length
        logger.info(f"MemoryMappedFile initialized: {file_path} (mode={mode})")

    async def open(self) -> None:
        self.file_size = await asyncio.to_thread(lambda: Path(self.file_path).stat().st_size)
        if self.map_length is None:
            self.map_length = self.file_size - self.offset

        mode_str = "rb" if self.mode == MMapMode.READ_ONLY else "r+b"
        # Use explicit function to satisfy type checker
        def _open_file() -> BinaryIO:
            return open(self.file_path, mode_str)  # type: ignore[return-value]
        self.file_handle = await asyncio.to_thread(_open_file)
        file_handle = self.file_handle
        if file_handle is None:
            raise RuntimeError("Failed to open file handle")

        access = {
            MMapMode.READ_ONLY: mmap.ACCESS_READ,
            MMapMode.READ_WRITE: mmap.ACCESS_WRITE,
            MMapMode.COPY_ON_WRITE: mmap.ACCESS_COPY,
        }[self.mode]

        self.mmap_obj = await asyncio.to_thread(
            mmap.mmap,
            file_handle.fileno(),
            length=self.map_length,
            access=access,
            offset=self.offset,
        )

        logger.info(f"Mapped {self.map_length:,} bytes ({self.file_size:,} total)")

    def _require_mmap(self) -> mmap.mmap:
        if self.mmap_obj is None:
            raise RuntimeError("File not mapped")
        return self.mmap_obj

    async def read(self, position: int, size: int) -> bytes:
        if self.mmap_obj is None:
            await self.open()
        mmap_obj = self._require_mmap()
        mmap_obj.seek(position)
        return mmap_obj.read(size)

    async def write(self, position: int, data: bytes) -> None:
        if self.mmap_obj is None:
            await self.open()
        if self.mode == MMapMode.READ_ONLY:
            raise ValueError("Cannot write in read-only mode")

        mmap_obj = self._require_mmap()
        mmap_obj.seek(position)
        mmap_obj.write(data)

    async def read_chunk(self, chunk_size: int, position: int = 0) -> bytes:
        return await self.read(position, chunk_size)

    async def iter_chunks(self, chunk_size: int = 8 * 1024 * 1024) -> AsyncGenerator[bytes, None]:
        if self.mmap_obj is None:
            await self.open()

        if self.map_length is None:
            return

        position = 0
        while position < self.map_length:
            size = min(chunk_size, self.map_length - position)
            chunk = await self.read(position, size)
            yield chunk
            position += size

    def search(self, pattern: bytes) -> list[int]:
        mmap_obj = self._require_mmap()
        positions: list[int] = []
        start = 0
        while True:
            pos = mmap_obj.find(pattern, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        logger.debug(f"Found pattern at {len(positions)} positions")
        return positions

    async def close(self) -> None:
        if self.mmap_obj:
            self.mmap_obj.close()
            self.mmap_obj = None

        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

        logger.info(f"Closed memory map: {self.file_path}")

    async def __aenter__(self) -> "MemoryMappedFile":
        await self.open()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()
