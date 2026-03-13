"""
Phase 11: Zero-Copy Transfers (os.sendfile)

Uses os.sendfile to stream file contents to a socket efficiently.
"""

import asyncio
import os
import socket
import time
from dataclasses import dataclass
from typing import IO, Optional


@dataclass
class ZeroCopyResult:
    file_path: str
    bytes_sent: int
    duration_seconds: float
    throughput_mbps: float
    used_zero_copy: bool
    error: Optional[str] = None


class ZeroCopyUploader:
    """Zero-copy upload helper using os.sendfile where possible."""

    def __init__(self, chunk_size: int = 1024 * 1024):
        self.chunk_size = max(64 * 1024, chunk_size)

    async def sendfile_to_socket(
        self,
        file_path: str,
        out_socket: socket.socket,
        use_sendfile: bool = True,
    ) -> ZeroCopyResult:
        return await asyncio.to_thread(
            self._sendfile_to_socket_sync,
            file_path,
            out_socket,
            use_sendfile,
        )

    def _sendfile_to_socket_sync(
        self,
        file_path: str,
        out_socket: socket.socket,
        use_sendfile: bool,
    ) -> ZeroCopyResult:
        start = time.perf_counter()
        bytes_sent = 0
        used_zero_copy = False
        try:
            file_size = os.path.getsize(file_path)
            with open(file_path, "rb") as handle:
                offset = 0
                while offset < file_size:
                    remaining = file_size - offset
                    count = min(self.chunk_size, remaining)
                    if use_sendfile and hasattr(os, "sendfile"):
                        try:
                            sent = os.sendfile(out_socket.fileno(), handle.fileno(), offset, count)
                            used_zero_copy = True
                        except OSError:
                            sent = self._fallback_send(out_socket, handle, offset, count)
                        except AttributeError:
                            sent = self._fallback_send(out_socket, handle, offset, count)
                    else:
                        sent = self._fallback_send(out_socket, handle, offset, count)

                    if sent <= 0:
                        break

                    offset += sent
                    bytes_sent += sent

            duration = max(time.perf_counter() - start, 0.000001)
            throughput = (bytes_sent / duration) / (1024 * 1024)
            return ZeroCopyResult(
                file_path=file_path,
                bytes_sent=bytes_sent,
                duration_seconds=duration,
                throughput_mbps=throughput,
                used_zero_copy=used_zero_copy,
            )
        except Exception as exc:
            duration = max(time.perf_counter() - start, 0.000001)
            throughput = (bytes_sent / duration) / (1024 * 1024)
            return ZeroCopyResult(
                file_path=file_path,
                bytes_sent=bytes_sent,
                duration_seconds=duration,
                throughput_mbps=throughput,
                used_zero_copy=used_zero_copy,
                error=str(exc),
            )

    def _fallback_send(
        self,
        out_socket: socket.socket,
        handle: IO[bytes],
        offset: int,
        count: int,
    ) -> int:
        handle.seek(offset)
        data = handle.read(count)
        if not data:
            return 0
        return out_socket.send(data)
