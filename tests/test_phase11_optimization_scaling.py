"""
Tests for Phase 11: Optimization & Scaling

Currently covers:
- Zero-Copy Transfers (os.sendfile)
"""

import asyncio
import os
import socket
import tempfile

import pytest

from bot.core.zero_copy_uploader import ZeroCopyUploader
from bot.core.mtproto_parallel_uploader import MTProtoParallelUploader
from bot.core.gdrive_batch_optimizer import GDriveBatchOptimizer
from bot.core.recursive_extractor import RecursiveExtractor
from bot.core.salvage_mode import SalvageMode


def _recv_all(sock: socket.socket, expected: int, timeout: float = 2.0) -> bytes:
    sock.settimeout(timeout)
    received = b""
    while len(received) < expected:
        try:
            chunk = sock.recv(65536)
        except socket.timeout:
            break
        if not chunk:
            break
        received += chunk
    return received


@pytest.mark.asyncio
async def test_zero_copy_sendfile_to_socket():
    uploader = ZeroCopyUploader(chunk_size=128 * 1024)

    payload = os.urandom(64 * 1024)
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(payload)
        temp_path = temp.name

    sender, receiver = socket.socketpair()
    try:
        result = await uploader.sendfile_to_socket(temp_path, sender, use_sendfile=True)
        sender.shutdown(socket.SHUT_WR)
        received = _recv_all(receiver, len(payload))

        assert result.bytes_sent == len(payload)
        assert result.used_zero_copy in {True, False}
        assert result.error is None
        assert received == payload
    finally:
        sender.close()
        receiver.close()
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_zero_copy_fallback_path():
    uploader = ZeroCopyUploader(chunk_size=64 * 1024)

    payload = os.urandom(64 * 1024)
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(payload)
        temp_path = temp.name

    sender, receiver = socket.socketpair()
    try:
        result = await uploader.sendfile_to_socket(temp_path, sender, use_sendfile=False)
        sender.shutdown(socket.SHUT_WR)
        received = _recv_all(receiver, len(payload))

        assert result.bytes_sent == len(payload)
        assert result.used_zero_copy is False
        assert result.error is None
        assert received == payload
    finally:
        sender.close()
        receiver.close()
        os.unlink(temp_path)


class _FakePhoto:
    def __init__(self, file_id: str):
        self.file_id = file_id


class _FakeResponse:
    def __init__(self, file_id: str):
        self.photo = _FakePhoto(file_id)


class _FakeClient:
    def __init__(self):
        self.calls = 0

    async def send_photo(self, chat_id, photo, caption=None):
        self.calls += 1
        return _FakeResponse(f"file-{self.calls}")


@pytest.mark.asyncio
async def test_mtproto_parallel_uploader():
    payload = os.urandom(256 * 1024)
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(payload)
        temp_path = temp.name

    client = _FakeClient()
    uploader = MTProtoParallelUploader(client)

    try:
        result = await uploader.upload_file_parallel(
            temp_path,
            chat_id=12345,
            num_workers=2,
            chunk_size=64 * 1024,
        )

        assert result.file_size == len(payload)
        assert result.chunks_uploaded == 2
        assert result.file_id.startswith("file-")
        assert client.calls == 2
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_gdrive_batch_optimizer():
    optimizer = GDriveBatchOptimizer()
    metadata = await optimizer.batch_get_metadata(["a1", "b2"])

    assert metadata["a1"]["id"] == "a1"
    assert metadata["b2"]["name"] == "file_b2"

    update_result = await optimizer.batch_update_metadata({"a1": {"name": "new"}})
    assert update_result.processed == 1
    assert update_result.failed == 0

    copy_result = await optimizer.batch_copy_files(["a1", "b2"], "dest")
    assert copy_result.processed == 2
    assert copy_result.failed == 0


def _create_nested_zip(base_dir: str) -> str:
    outer_path = os.path.join(base_dir, "outer.zip")
    inner_path = os.path.join(base_dir, "inner.zip")
    inner_file_path = os.path.join(base_dir, "inner.txt")

    with open(inner_file_path, "w", encoding="utf-8") as handle:
        handle.write("hello")

    import zipfile

    with zipfile.ZipFile(inner_path, "w") as inner_zip:
        inner_zip.write(inner_file_path, arcname="inner.txt")

    with zipfile.ZipFile(outer_path, "w") as outer_zip:
        outer_zip.write(inner_path, arcname="inner.zip")

    return outer_path


def test_recursive_extractor():
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_path = _create_nested_zip(tmpdir)
        output_dir = os.path.join(tmpdir, "extract")

        extractor = RecursiveExtractor(max_depth=3)
        result = extractor.extract_recursive(archive_path, output_dir)

        assert result.archives_processed >= 1
        assert any(path.endswith("inner.txt") for path in result.extracted_files)


def test_salvage_mode():
    payload = b"0123456789"
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(payload)
        temp_path = temp.name

    output_path = f"{temp_path}.salvaged"
    try:
        salvage = SalvageMode()
        result = salvage.recover_file(temp_path, output_path, [(3, 6)])

        with open(output_path, "rb") as handle:
            recovered = handle.read()

        assert result.bytes_written == len(recovered)
        assert recovered == b"0126789"
    finally:
        os.unlink(temp_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
