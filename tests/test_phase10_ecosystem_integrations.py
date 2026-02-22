"""
Comprehensive tests for Phase 10: Ecosystem & Integrations

Testing modules:
- Index Link Generation
- Batch Operations
- Link Bypassers
- Debrid Service Integrations
"""

import pytest

from bot.core.index_generator import IndexGenerator, IndexStorage, IndexFileItem
from bot.core.batch_operations import BatchOperationsManager, BatchRequest
from bot.core.link_bypassers import LinkBypassEngine
from bot.core.debrid_manager import DebridManager, DebridService


@pytest.mark.asyncio
async def test_index_generator_builds_metadata_and_html():
    generator = IndexGenerator(title="Project Share")
    items = [
        IndexFileItem(name="video.mkv", url="https://files.example/video.mkv", size_bytes=1024),
        IndexFileItem(name="report.pdf", url="https://files.example/report.pdf", size_bytes=2048),
    ]

    metadata = generator.build_index(items, expires_in_days=3)
    html = generator.build_index_html(items, metadata)

    assert metadata.total_files == 2
    assert metadata.total_size_bytes == 3072
    assert metadata.expires_at is not None
    assert "Project Share" in html
    assert "video.mkv" in html
    assert "report.pdf" in html


def test_index_generator_build_items_from_links():
    generator = IndexGenerator()
    links = [
        "https://cdn.example/path/photo.jpg",
        "https://cdn.example/files/archive.zip",
        "https://cdn.example/README",
    ]

    items = generator.build_items_from_links(links)

    assert len(items) == 3
    categories = {item.category for item in items}
    assert "images" in categories
    assert "archives" in categories
    assert "other" in categories


def test_index_storage_upload_and_fetch():
    storage = IndexStorage(base_url="https://index.example")
    token_url = storage.upload_index("<html></html>", "abc123")

    assert token_url.startswith("https://index.example/")
    token = token_url.rsplit("/", 1)[-1]
    assert storage.get_index(token) == "<html></html>"


def test_batch_operations_parse_and_create():
    manager = BatchOperationsManager()
    text = """
    https://example.com/a
    https://example.com/a
    magnet:?xt=urn:btih:abc123
    invalid_link
    # comment line
    https://example.com/b
    """
    valid, invalid = manager.parse_link_list(text)

    assert "https://example.com/a" in valid
    assert "https://example.com/b" in valid
    assert any(link.startswith("magnet:") for link in valid)
    assert "invalid_link" in invalid

    request = BatchRequest(user_id=123, links=valid, mode="mirror", stagger_seconds=1)
    summary, entries = manager.create_batch(request)

    assert summary.total_links == len(valid)
    assert summary.queued_count == len(entries)
    assert summary.mode == "mirror"
    assert all(entry.status == "queued" for entry in entries)


@pytest.mark.asyncio
async def test_link_bypass_engine_normalizes_and_tracks_stats():
    engine = LinkBypassEngine(enabled=True)
    result = await engine.normalize_link("https://bit.ly/example")

    assert result.original_url == "https://bit.ly/example"
    assert result.final_url
    assert result.service in {"shortener", "ad", "filehost", "streaming"}

    stats = engine.get_stats()
    assert stats["total"] == 1
    assert stats["bypassed"] in {0, 1}


@pytest.mark.asyncio
async def test_debrid_manager_unrestricts_and_adds_magnets():
    manager = DebridManager(DebridService.REAL_DEBRID, api_token="token")
    unrestrict = await manager.unrestrict_link("https://host.example/file")

    assert unrestrict.success is True
    assert unrestrict.unrestricted_url.startswith("https://debrid.example/")

    magnet = await manager.add_magnet("magnet:?xt=urn:btih:deadbeef")
    assert magnet.success is True
    assert len(magnet.links) == 3

    status = await manager.get_user_status()
    assert status["status"] == "active"
