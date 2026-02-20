import hashlib

import pytest

from bot.core.file_cache_manager import FileCacheManager


@pytest.mark.asyncio
async def test_compute_hashes(tmp_path):
    data = b"cache-test"
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(data)

    manager = FileCacheManager()
    hashes = await manager.compute_hashes(str(file_path))

    assert hashes is not None
    assert hashes["md5"] == hashlib.md5(data).hexdigest()
    assert hashes["sha1"] == hashlib.sha1(data).hexdigest()


@pytest.mark.asyncio
async def test_cache_key_uses_sha1(tmp_path):
    data = b"cache-key"
    file_path = tmp_path / "sample.bin"
    file_path.write_bytes(data)

    manager = FileCacheManager()
    hashes = await manager.compute_hashes(str(file_path))

    key = manager._cache_key(hashes, len(data))
    assert key is not None
    assert hashes["sha1"] in key
