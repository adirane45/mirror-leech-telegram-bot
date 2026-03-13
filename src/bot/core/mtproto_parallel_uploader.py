"""
Phase 11: MTProto Parallel Chunk Uploading

Mock parallel chunk uploader for Telegram MTProto workflows.
"""

import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any, List


@dataclass
class ChunkUploadResult:
    chunk_index: int
    file_id: str
    size_bytes: int


@dataclass
class ParallelUploadResult:
    file_path: str
    file_size: int
    chunk_size: int
    chunks_uploaded: int
    duration_seconds: float
    file_id: str


class MTProtoParallelUploader:
    """Upload file chunks in parallel with a Telegram client."""

    def __init__(self, client: Any) -> None:
        self.client = client

    async def upload_file_parallel(
        self,
        filepath: str,
        chat_id: int,
        num_workers: int = 4,
        chunk_size: int = 4 * 1024 * 1024,
    ) -> ParallelUploadResult:
        file_size = await asyncio.to_thread(os.path.getsize, filepath)
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        workers = max(1, min(num_workers, total_chunks))

        start = time.perf_counter()
        tasks = []
        for chunk_index in range(total_chunks):
            if chunk_index >= workers:
                break
            tasks.append(
                asyncio.create_task(
                    self._upload_chunk(
                        filepath,
                        chat_id,
                        chunk_index,
                        chunk_size,
                    )
                )
            )

        chunk_results = await asyncio.gather(*tasks)

        file_id = self._reassemble_chunks(chunk_results)
        duration = max(time.perf_counter() - start, 0.000001)

        return ParallelUploadResult(
            file_path=filepath,
            file_size=file_size,
            chunk_size=chunk_size,
            chunks_uploaded=len(chunk_results),
            duration_seconds=duration,
            file_id=file_id,
        )

    async def _upload_chunk(
        self,
        filepath: str,
        chat_id: int,
        chunk_index: int,
        chunk_size: int,
    ) -> ChunkUploadResult:
        data = await asyncio.to_thread(
            self._read_chunk_sync,
            filepath,
            chunk_index,
            chunk_size,
        )

        result = await self._send_chunk(chat_id, data, chunk_index)
        return ChunkUploadResult(
            chunk_index=chunk_index,
            file_id=result,
            size_bytes=len(data),
        )

    @staticmethod
    def _read_chunk_sync(filepath: str, chunk_index: int, chunk_size: int) -> bytes:
        """Read one file chunk (blocking)."""
        with open(filepath, "rb") as handle:
            handle.seek(chunk_index * chunk_size)
            return handle.read(chunk_size)

    async def _send_chunk(self, chat_id: int, data: bytes, chunk_index: int) -> str:
        if self.client is None:
            await asyncio.sleep(0.01)
            return f"chunk-{chunk_index}"

        await asyncio.sleep(0)
        response = await self.client.send_photo(
            chat_id,
            photo=data,
            caption=f"Chunk {chunk_index + 1}",
        )
        return str(response.photo.file_id)

    def _reassemble_chunks(self, results: List[ChunkUploadResult]) -> str:
        if not results:
            return ""
        ordered = sorted(results, key=lambda item: item.chunk_index)
        return ordered[0].file_id
