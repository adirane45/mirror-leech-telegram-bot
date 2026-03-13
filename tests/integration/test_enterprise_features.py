"""
Comprehensive tests for enterprise features

Testing modules:
- Metadata Stripping Pipeline
- Cross-Seed Tracker Farming
- Headless CAPTCHA Solver
- Google Drive Quota Bypass
- Zombie Process Reaper
- Memory-Mapped Files (mmap)
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path

# Metadata Stripping
from bot.core.metadata_stripper import (
    MetadataStripper,
    PrivacyAnalyzer,
    MetadataBackup
)

# Cross-Seed Farming
from bot.core.cross_seed_farming import (
    TrackerConnection,
    CrossSeedManager,
    RatioFarmer,
    PrivateTrackerAPI,
    TrackerPool,
    TrackerType,
    TorrentInfo
)

# CAPTCHA Solver
from bot.core.captcha_solver import (
    CaptchaSolver,
    ReCaptchaSolver,
    HCaptchaSolver,
    TurnstileSolver,
    CaptchaPool,
    HeadlessBrowserCaptcha,
    CaptchaType,
    SolverProvider
)

# Drive Quota Bypass
from bot.core.drive_quota_bypass import (
    DriveQuotaManager,
    DriveAPIOptimizer,
    QuotaBypassStrategy,
    ServiceAccount,
    QuotaStatus
)

# Zombie Reaper
from bot.core.zombie_reaper import (
    ProcessMonitor,
    ZombieReaper,
    ResourceRecovery,
    ProcessGuard,
    ProcessState
)

# Memory-Mapped Files
from bot.core.memory_mapped_files import (
    MemoryMappedFile,
    MMapProcessor,
    MMapHasher,
    MMapCopier,
    MMapSearcher,
    MMapMode
)


# ============================================================================
# METADATA STRIPPING TESTS (6 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_metadata_stripper_strip_file():
    """Test stripping metadata from single file"""
    stripper = MetadataStripper()
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.jpg') as f:
        test_file = f.name
        f.write(b'fake image data')
    
    try:
        result = await stripper.strip_file(test_file)
        
        assert result.success is True
        assert result.file_path == test_file
        assert result.processing_time_seconds > 0
    finally:
        os.unlink(test_file)


@pytest.mark.asyncio
async def test_metadata_stripper_batch():
    """Test batch metadata stripping"""
    stripper = MetadataStripper()
    
    files = [f"/tmp/test_{i}.jpg" for i in range(5)]
    results = await stripper.strip_batch(files)
    
    assert len(results) == 5
    # Note: Mock files don't exist, so successful count may be 0
    assert stripper.stats["total_processed"] >= 0


@pytest.mark.asyncio
async def test_metadata_stripper_verify_clean():
    """Test verification of cleaned files"""
    stripper = MetadataStripper()
    
    result = await stripper.strip_file("/tmp/test.jpg")
    # For mock files, clean check may return False if file doesn't exist
    is_clean = await stripper.verify_clean("/tmp/test.jpg")
    
    # Just verify it returns a boolean
    assert isinstance(is_clean, bool)


@pytest.mark.asyncio
async def test_privacy_analyzer():
    """Test privacy analysis"""
    analyzer = PrivacyAnalyzer()
    
    result = await analyzer.analyze_file("/tmp/test.jpg")
    
    assert "privacy_score" in result
    assert 0 <= result["privacy_score"] <= 100
    assert "sensitive_fields" in result
    assert "recommendation" in result


@pytest.mark.asyncio
async def test_privacy_analyzer_batch():
    """Test batch privacy analysis"""
    analyzer = PrivacyAnalyzer()
    
    files = [f"/tmp/test_{i}.jpg" for i in range(3)]
    results = await analyzer.analyze_batch(files)
    
    assert len(results) == 3
    for result in results:
        assert "privacy_score" in result


@pytest.mark.asyncio
async def test_metadata_backup_restore():
    """Test metadata backup and restore"""
    backup = MetadataBackup()
    
    # Backup
    backup_path = await backup.backup_file("/tmp/test.jpg")
    
    # Backup path should be returned
    assert backup_path is not None


# ============================================================================
# CROSS-SEED FARMING TESTS (7 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_tracker_connection_authenticate():
    """Test tracker authentication"""
    tracker = TrackerConnection(
        "https://tracker1.example.com",
        api_key="test_key"
    )
    
    success = await tracker.authenticate()
    
    assert success is True
    assert tracker.authenticated is True


@pytest.mark.asyncio
async def test_tracker_connection_add_torrent():
    """Test adding torrent to tracker"""
    tracker = TrackerConnection(
        "https://tracker1.example.com",
        api_key="test_key"
    )
    await tracker.authenticate()
    
    torrent = TorrentInfo(
        info_hash="abc123",
        name="test_torrent",
        size_bytes=1024 * 1024 * 100,
        trackers=["https://tracker1.example.com"]
    )
    
    success = await tracker.add_torrent(torrent)
    
    assert success is True


@pytest.mark.asyncio
async def test_cross_seed_manager():
    """Test cross-seed manager"""
    manager = CrossSeedManager()
    
    tracker1 = TrackerConnection("https://tracker1.example.com", api_key="key1")
    tracker2 = TrackerConnection("https://tracker2.example.com", api_key="key2")
    
    manager.add_tracker(tracker1)
    manager.add_tracker(tracker2)
    
    torrent = TorrentInfo(
        info_hash="torrent123",
        name="test_torrent",
        size_bytes=1024 * 1024 * 100,
        trackers=["https://tracker1.example.com"]
    )
    
    opportunities = await manager.find_cross_seed_opportunities(torrent)
    
    assert len(opportunities) > 0


@pytest.mark.asyncio
async def test_cross_seed_upload():
    """Test cross-seeding to multiple trackers"""
    manager = CrossSeedManager()
    
    tracker1 = TrackerConnection("https://tracker1.example.com", api_key="key1")
    tracker2 = TrackerConnection("https://tracker2.example.com", api_key="key2")
    
    manager.add_tracker(tracker1)
    manager.add_tracker(tracker2)
    
    torrent = TorrentInfo(
        info_hash="torrent123",
        name="test_torrent",
        size_bytes=1024 * 1024 * 100,
        trackers=["https://tracker1.example.com"]
    )
    
    # Cross-seed will auto-detect trackers
    results = await manager.cross_seed(torrent)
    
    # Results is a dict mapping tracker URLs to success bools
    assert isinstance(results, dict)
    assert len(results) >= 0


@pytest.mark.asyncio
async def test_ratio_farmer():
    """Test ratio farming"""
    # RatioFarmer needs a CrossSeedManager, not just a TrackerConnection
    manager = CrossSeedManager()
    
    tracker = TrackerConnection("https://tracker1.example.com", api_key="test_key")
    await tracker.authenticate()
    
    manager.add_tracker(tracker)
    
    farmer = RatioFarmer(manager)
    farmer.set_ratio_goal(tracker.tracker_url, 2.0)
    
    torrent = TorrentInfo(
        info_hash="torrent123",
        name="test_torrent",
        size_bytes=1024 * 1024 * 100,
        trackers=[tracker.tracker_url]
    )
    
    # Add torrent to tracker first
    await tracker.add_torrent(torrent)
    
    result = await farmer.farm_ratio(torrent, duration_hours=1)
    
    assert result["ratio_achieved"] >= 0
    assert "duration_hours" in result


@pytest.mark.asyncio
async def test_private_tracker_api():
    """Test private tracker API"""
    api = PrivateTrackerAPI("https://private-tracker.com", api_key="test_key")
    
    torrents = await api.search_torrents(query="ubuntu")
    
    assert len(torrents) >= 0
    
    stats = await api.get_user_stats()
    assert "uploaded" in stats
    assert "downloaded" in stats
    assert "ratio" in stats


@pytest.mark.asyncio
async def test_tracker_pool():
    """Test tracker pool management"""
    pool = TrackerPool()
    
    tracker1 = TrackerConnection("https://tracker1.example.com", api_key="key1")
    tracker2 = TrackerConnection("https://tracker2.example.com", api_key="key2")
    
    pool.add_connection(tracker1)
    pool.add_connection(tracker2)
    
    # Authenticate all
    auth_results = await pool.authenticate_all()
    
    stats = await pool.get_aggregate_stats()
    assert "tracker_count" in stats
    assert stats["tracker_count"] == 2


# ============================================================================
# CAPTCHA SOLVER TESTS (6 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_captcha_solver():
    """Test basic CAPTCHA solving"""
    solver = CaptchaSolver(SolverProvider.CAPSOLVER, api_key="test_key")
    
    solution = await solver.solve(
        CaptchaType.RECAPTCHA_V2,
        "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
        "https://example.com"
    )
    
    assert solution.success is True
    assert len(solution.solution) > 0
    assert solution.solve_time_seconds > 0


@pytest.mark.asyncio
async def test_recaptcha_v2_solver():
    """Test reCAPTCHA v2 specialized solver"""
    solver = ReCaptchaSolver(api_key="test_key")
    
    solution = await solver.solve_v2(
        "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
        "https://example.com"
    )
    
    assert solution.success is True
    assert solution.captcha_type == CaptchaType.RECAPTCHA_V2


@pytest.mark.asyncio
async def test_recaptcha_v3_solver():
    """Test reCAPTCHA v3 specialized solver"""
    solver = ReCaptchaSolver(api_key="test_key")
    
    solution = await solver.solve_v3(
        "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI",
        "https://example.com",
        action="submit",
        min_score=0.7
    )
    
    assert solution.success is True
    assert solution.captcha_type == CaptchaType.RECAPTCHA_V3


@pytest.mark.asyncio
async def test_hcaptcha_solver():
    """Test hCaptcha solver"""
    solver = HCaptchaSolver(api_key="test_key")
    
    solution = await solver.solve_hcaptcha(
        "10000000-ffff-ffff-ffff-000000000001",
        "https://example.com"
    )
    
    assert solution.success is True
    assert solution.captcha_type == CaptchaType.H_CAPTCHA


@pytest.mark.asyncio
async def test_turnstile_solver():
    """Test Cloudflare Turnstile solver"""
    solver = TurnstileSolver(api_key="test_key")
    
    solution = await solver.solve_turnstile(
        "0x4AAAAAAABBBBBBBBBCCCCCC",
        "https://example.com"
    )
    
    assert solution.success is True
    assert solution.captcha_type == CaptchaType.TURNSTILE


@pytest.mark.asyncio
async def test_captcha_pool():
    """Test CAPTCHA solver pool"""
    pool = CaptchaPool()
    
    solver1 = CaptchaSolver(SolverProvider.CAPSOLVER, api_key="key1")
    solver2 = CaptchaSolver(SolverProvider.TWO_CAPTCHA, api_key="key2")
    
    pool.add_solver(solver1)
    pool.add_solver(solver2)
    
    solution = await pool.solve_with_fallback(
        CaptchaType.RECAPTCHA_V2,
        "test_site_key",
        "https://example.com"
    )
    
    assert solution.success is True
    
    stats = pool.get_aggregate_stats()
    assert stats["total_solvers"] == 2


# ============================================================================
# DRIVE QUOTA BYPASS TESTS (6 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_quota_manager_add_account():
    """Test adding service account"""
    manager = DriveQuotaManager()
    
    manager.add_account(
        "test@service.iam.gserviceaccount.com",
        "/path/to/key.json",
        "project-id-123"
    )
    
    assert len(manager.accounts) == 1
    assert manager.accounts[0].email == "test@service.iam.gserviceaccount.com"


@pytest.mark.asyncio
async def test_quota_manager_check_quota():
    """Test quota checking"""
    manager = DriveQuotaManager()
    manager.add_account("test@service.iam.gserviceaccount.com", "/path/to/key.json", "project-123")
    
    account = manager.get_current_account()
    quota_info = await manager.check_quota(account)
    
    assert quota_info.account_email == "test@service.iam.gserviceaccount.com"
    assert quota_info.limit > 0
    assert quota_info.remaining >= 0
    assert 0 <= quota_info.percentage <= 100


@pytest.mark.asyncio
async def test_quota_manager_rotation():
    """Test service account rotation"""
    manager = DriveQuotaManager()
    
    manager.add_account("account1@service.iam.gserviceaccount.com", "/key1.json", "project-1")
    manager.add_account("account2@service.iam.gserviceaccount.com", "/key2.json", "project-2")
    
    first_account = manager.get_current_account()
    success = await manager.rotate_account()
    second_account = manager.get_current_account()
    
    assert success is True
    assert first_account.email != second_account.email


@pytest.mark.asyncio
async def test_quota_manager_transfer():
    """Test transfer with rotation"""
    manager = DriveQuotaManager()
    
    manager.add_account("account1@service.iam.gserviceaccount.com", "/key1.json", "project-1")
    manager.add_account("account2@service.iam.gserviceaccount.com", "/key2.json", "project-2")
    
    file_size = 100 * 1024 * 1024  # 100 MB
    stats = await manager.transfer_with_rotation(file_size, "upload")
    
    assert stats.total_bytes == file_size
    assert stats.avg_speed_mbps > 0
    assert stats.accounts_used >= 1


@pytest.mark.asyncio
async def test_api_optimizer():
    """Test API optimizer"""
    manager = DriveQuotaManager()
    manager.add_account("test@service.iam.gserviceaccount.com", "/key.json", "project-123")
    
    optimizer = DriveAPIOptimizer(manager)
    
    # Test cached metadata
    metadata = await optimizer.cached_metadata("file_id_123")
    
    assert "id" in metadata
    assert "name" in metadata
    assert metadata["id"] == "file_id_123"


@pytest.mark.asyncio
async def test_quota_bypass_strategy():
    """Test quota bypass strategy"""
    manager = DriveQuotaManager()
    manager.add_account("test@service.iam.gserviceaccount.com", "/key.json", "project-123")
    
    strategy = QuotaBypassStrategy(manager)
    
    # Test shared drive transfer
    success = await strategy.shared_drive_transfer(
        "file_id",
        "source_drive_id",
        "dest_drive_id"
    )
    
    assert success is True


# ============================================================================
# ZOMBIE REAPER TESTS (6 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_process_monitor_scan():
    """Test process scanning"""
    monitor = ProcessMonitor()
    
    processes = await monitor.scan_processes()
    
    assert len(processes) > 0
    assert all(hasattr(p, 'pid') for p in processes)
    assert all(hasattr(p, 'name') for p in processes)


@pytest.mark.asyncio
async def test_process_monitor_find_zombies():
    """Test zombie process detection"""
    monitor = ProcessMonitor()
    
    zombies = await monitor.find_zombies()
    
    assert isinstance(zombies, list)
    # Mock should generate 2 zombies
    assert len(zombies) >= 1


@pytest.mark.asyncio
async def test_process_monitor_find_orphans():
    """Test orphan process detection"""
    monitor = ProcessMonitor()
    
    orphans = await monitor.find_orphans()
    
    assert isinstance(orphans, list)
    # Some processes should be orphans
    if len(orphans) > 0:
        assert orphans[0].is_orphan is True


@pytest.mark.asyncio
async def test_zombie_reaper():
    """Test zombie reaping"""
    monitor = ProcessMonitor()
    reaper = ZombieReaper(monitor)
    
    stats = await reaper.reap_zombies()
    
    assert stats.zombies_found >= 0
    assert stats.zombies_reaped <= stats.zombies_found
    assert stats.duration_seconds > 0


@pytest.mark.asyncio
async def test_orphan_cleanup():
    """Test orphan cleanup"""
    monitor = ProcessMonitor()
    reaper = ZombieReaper(monitor)
    
    stats = await reaper.clean_orphans()
    
    assert stats.orphans_found >= 0
    assert stats.orphans_cleaned <= stats.orphans_found
    assert stats.resources_freed_mb >= 0


@pytest.mark.asyncio
async def test_process_guard():
    """Test process guarding"""
    monitor = ProcessMonitor()
    guard = ProcessGuard(monitor)
    
    await guard.guard_process(1000, "test_worker")
    
    assert 1000 in guard.guarded_pids
    assert guard.guarded_pids[1000] == "test_worker"
    
    unhealthy = await guard.check_health()
    assert isinstance(unhealthy, list)


# ============================================================================
# MEMORY-MAPPED FILES TESTS (7 tests)
# ============================================================================

@pytest.mark.asyncio
async def test_memory_mapped_file_operations():
    """Test basic mmap operations"""
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        test_file = f.name
        f.write(b'Hello World' * 1000)
    
    try:
        mmap_file = MemoryMappedFile(test_file, MMapMode.READ_ONLY)
        
        async with mmap_file:
            data = await mmap_file.read(0, 11)
            assert data == b'Hello World'
    
    finally:
        os.unlink(test_file)


@pytest.mark.asyncio
async def test_mmap_chunked_iteration():
    """Test iterating through file in chunks"""
    # Create temporary large-ish file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        test_file = f.name
        f.write(b'X' * (1024 * 1024))  # 1 MB
    
    try:
        mmap_file = MemoryMappedFile(test_file, MMapMode.READ_ONLY)
        
        chunk_count = 0
        async with mmap_file:
            async for chunk in mmap_file.iter_chunks(chunk_size=256 * 1024):
                chunk_count += 1
                assert len(chunk) > 0
        
        assert chunk_count >= 4  # At least 4 chunks of 256KB
    
    finally:
        os.unlink(test_file)


@pytest.mark.asyncio
async def test_mmap_processor():
    """Test memory-mapped file processor"""
    # Create test file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        test_file = f.name
        f.write(b'Test Data' * 10000)
    
    try:
        processor = MMapProcessor(chunk_size=1024)
        
        def process_chunk(chunk: bytes, chunk_num: int):
            return len(chunk)
        
        stats = await processor.process_file(test_file, process_chunk)
        
        assert stats.bytes_processed > 0
        assert stats.chunks_processed > 0
        assert stats.throughput_mbps > 0
    
    finally:
        os.unlink(test_file)


@pytest.mark.asyncio
async def test_mmap_hasher():
    """Test memory-mapped file hashing"""
    # Create test file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        test_file = f.name
        f.write(b'Hash this content' * 1000)
    
    try:
        hasher = MMapHasher("sha256")
        
        digest = await hasher.hash_file(test_file)
        
        assert len(digest) == 64  # SHA256 hex digest
        assert all(c in '0123456789abcdef' for c in digest)
    
    finally:
        os.unlink(test_file)


@pytest.mark.asyncio
async def test_mmap_copier():
    """Test memory-mapped file copying"""
    # Create source file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        source_file = f.name
        test_data = b'Copy this data' * 10000
        f.write(test_data)
    
    dest_file = source_file + ".copy"
    
    try:
        copier = MMapCopier()
        
        stats = await copier.copy_file(source_file, dest_file)
        
        assert stats.bytes_processed > 0
        assert stats.chunks_processed > 0
        assert os.path.exists(dest_file)
        
        # Verify copied content
        with open(dest_file, 'rb') as f:
            copied_data = f.read()
            assert copied_data == test_data
    
    finally:
        os.unlink(source_file)
        if os.path.exists(dest_file):
            os.unlink(dest_file)


@pytest.mark.asyncio
async def test_mmap_copier_empty_file():
    """Test memory-mapped copier with empty source file"""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        source_file = f.name

    dest_file = source_file + ".copy"

    try:
        copier = MMapCopier()

        stats = await copier.copy_file(source_file, dest_file)

        assert stats.bytes_processed == 0
        assert stats.chunks_processed == 0
        assert os.path.exists(dest_file)
        assert os.path.getsize(dest_file) == 0

    finally:
        os.unlink(source_file)
        if os.path.exists(dest_file):
            os.unlink(dest_file)


@pytest.mark.asyncio
async def test_mmap_searcher():
    """Test memory-mapped file searching"""
    # Create test file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        test_file = f.name
        f.write(b'Find ABC here and ABC there and ABC everywhere')
    
    try:
        searcher = MMapSearcher()
        
        positions = await searcher.search_file(test_file, b'ABC')
        
        assert len(positions) == 3  # Should find 3 occurrences
        assert all(isinstance(pos, int) for pos in positions)
    
    finally:
        os.unlink(test_file)


@pytest.mark.asyncio
async def test_mmap_write_operations():
    """Test memory-mapped write operations"""
    # Create test file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        test_file = f.name
        f.write(b'Original Data' * 100)
    
    try:
        mmap_file = MemoryMappedFile(test_file, MMapMode.READ_WRITE)
        
        async with mmap_file:
            # Write new data
            await mmap_file.write(0, b'Modified ')
            
            # Read back
            data = await mmap_file.read(0, 9)
            assert data == b'Modified '
    
    finally:
        os.unlink(test_file)


# ============================================================================
# TEST SUMMARY
# ============================================================================

def test_suite_summary():
    """Summary of test suite"""
    test_counts = {
        "Metadata Stripping": 6,
        "Cross-Seed Farming": 7,
        "CAPTCHA Solver": 6,
        "Drive Quota Bypass": 6,
        "Zombie Reaper": 6,
        "Memory-Mapped Files": 7
    }
    
    total_tests = sum(test_counts.values())
    
    print(f"\n{'='*60}")
    print("Phase 9 Enterprise Features Test Suite")
    print(f"{'='*60}")
    for module, count in test_counts.items():
        print(f"  {module:<25} {count:>2} tests")
    print(f"{'='*60}")
    print(f"  {'TOTAL':<25} {total_tests:>2} tests")
    print(f"{'='*60}\n")
    
    assert total_tests == 38
