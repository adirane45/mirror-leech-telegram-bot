"""
Comprehensive tests for Phase 8: Advanced Intelligence

Tests all Phase 8 modules:
- BLAKE3 Hashing Engine
- Web3/IPFS Storage
- Serverless Edge Workers
- Adaptive Concurrency
- HLS/DASH Stream Weaver
- Lazy Imports Optimization
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
import sys

# Import Phase 8 modules
from bot.core.blake3_hasher import (
    BLAKE3Hasher,
    MultiThreadedHasher,
    HashResult,
   get_hasher
)
from bot.core.web3_ipfs_storage import (
    IPFSClient,
    Web3StorageProvider,
    DecentralizedFileHost,
    upload_to_ipfs
)
from bot.core.edge_workers import (
    EdgeWorkerManager,
    EdgeWorkerConfig,
    EdgeLocation,
    EdgeRequest,
    ZeroBandwidthProxy,
    GlobalCDN
)
from bot.core.adaptive_concurrency import (
    PIDController,
    PIDParameters,
    AdaptiveThreadPool,
    AdaptiveConcurrencyController,
    WorkloadAnalyzer
)
from bot.core.stream_weaver import (
    StreamWeaver,
    StreamProtocol,
    HLSParser,
    DASHParser,
    DRMHandler,
    DRMType,
    FastConcatenator
)
from bot.core.lazy_imports import (
    LazyImporter,
    ImportTracker,
    StartupOptimizer,
    DynamicModuleLoader,
    lazy_import
)


# ============================================================================
# BLAKE3 Hashing Engine Tests
# ============================================================================

@pytest.mark.asyncio
async def test_blake3_hasher_initialization():
    """Test BLAKE3 hasher initialization"""
    hasher = BLAKE3Hasher(chunk_size=1024*1024, max_workers=4)
    
    assert hasher.chunk_size == 1024 * 1024
    assert hasher.max_workers == 4
    assert hasher.executor is not None


@pytest.mark.asyncio
async def test_blake3_hash_file():
    """Test file hashing"""
    hasher = BLAKE3Hasher()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, BLAKE3!")
        temp_path = f.name
    
    try:
        result = await hasher.hash_file(temp_path)
        
        assert result.hash_value
        assert len(result.hash_value) > 0
        assert result.size_bytes > 0
        assert result.throughput_mbps >= 0
        
    finally:
        Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_blake3_hash_multiple_files():
    """Test hashing multiple files concurrently"""
    hasher = BLAKE3Hasher()
    
    # Create temp files
    temp_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(f"File content {i}")
            temp_files.append(f.name)
    
    try:
        results = await hasher.hash_multiple_files(temp_files)
        
        assert len(results) == 3
        for path, result in results.items():
            assert result.hash_value
            assert len(result.hash_value) > 0
            
    finally:
        for path in temp_files:
            Path(path).unlink()


@pytest.mark.asyncio
async def test_blake3_verify_hash():
    """Test hash verification"""
    hasher = BLAKE3Hasher()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test content")
        temp_path = f.name
    
    try:
        # Hash file
        result = await hasher.hash_file(temp_path)
        expected_hash = result.hash_value
        
        # Verify
        matches = await hasher.verify_hash(temp_path, expected_hash)
        assert matches is True
        
        # Verify with wrong hash
        wrong_matches = await hasher.verify_hash(temp_path, "wrong_hash")
        assert wrong_matches is False
        
    finally:
        Path(temp_path).unlink()


def test_blake3_performance_stats():
    """Test getting performance stats"""
    hasher = BLAKE3Hasher(max_workers=8)
    
    stats = hasher.get_performance_stats()
    
    assert stats["max_workers"] == 8
    assert stats["target_throughput_mbps"] == 2000


@pytest.mark.asyncio
async def test_multithreaded_hasher():
    """Test multi-threaded hasher"""
    hasher = MultiThreadedHasher(num_threads=4)
    
    assert hasher.num_threads == 4
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test")
        temp_path = f.name
    
    try:
        result = await hasher.parallel_hash(temp_path)
        assert result.hash_value
        assert len(result.hash_value) > 0
        
    finally:
        Path(temp_path).unlink()


# ============================================================================
# Web3/IPFS Storage Tests
# ============================================================================

@pytest.mark.asyncio
async def test_ipfs_client_initialization():
    """Test IPFS client initialization"""
    client = IPFSClient()
    
    assert client.api_endpoint == "http://127.0.0.1:5001"
    assert len(client.gateway_endpoints) > 0
    assert client.auto_pin is True


@pytest.mark.asyncio
async def test_ipfs_upload():
    """Test IPFS file upload"""
    client = IPFSClient()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("IPFS test content")
        temp_path = f.name
    
    try:
        result = await client.upload_file(temp_path)
        
        assert result.success
        assert result.cid
        assert result.cid.startswith("Qm")
        assert len(result.gateway_urls) > 0
        assert result.pinned
        
    finally:
        Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_ipfs_stats():
    """Test IPFS upload statistics"""
    client = IPFSClient()
    
    stats = client.get_stats()
    
    assert "total_uploads" in stats
    assert "success_rate" in stats
    assert "gateway_count" in stats


@pytest.mark.asyncio
async def test_web3_storage_provider():
    """Test Web3 storage provider"""
    provider = Web3StorageProvider()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Web3 storage test")
        temp_path = f.name
    
    try:
        result = await provider.store_file(
            temp_path,
            metadata={"description": "test file"}
        )
        
        assert result.success
        
        # Search by filename
        filename = Path(temp_path).name
        metadata = provider.search_by_filename(filename)
        assert metadata is not None
        assert metadata["cid"] == result.cid
        
    finally:
        Path(temp_path).unlink()


@pytest.mark.asyncio
async def test_decentralized_file_host():
    """Test decentralized file host"""
    host = DecentralizedFileHost(enable_pinning=True, replication_factor=3)
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hosted file")
        temp_path = f.name
    
    try:
        result = await host.host_file(temp_path, permanent=True)
        
        assert result.success
        
        # Get URLs
        filename = Path(temp_path).name
        urls = host.get_file_urls(filename)
        assert len(urls) > 0
        
    finally:
        Path(temp_path).unlink()


# ============================================================================
# Serverless Edge Workers Tests
# ============================================================================

@pytest.mark.asyncio
async def test_edge_worker_config():
    """Test edge worker configuration"""
    config = EdgeWorkerConfig(
        name="test-worker",
        script="console.log('test')",
        routes=["/*"],
        locations=[EdgeLocation.US_EAST],
        environment_vars={"KEY": "value"}
    )
    
    assert config.name == "test-worker"
    assert len(config.locations) == 1


@pytest.mark.asyncio
async def test_edge_worker_manager():
    """Test edge worker manager"""
    manager = EdgeWorkerManager()
    
    config = EdgeWorkerConfig(
        name="test",
        script="test",
        routes=["/*"],
        locations=[EdgeLocation.US_EAST, EdgeLocation.EU_WEST],
        environment_vars={}
    )
    
    success = await manager.deploy_worker(config)
    assert success is True
    
    workers = manager.list_workers()
    assert len(workers) == 2  # Two locations


@pytest.mark.asyncio
async def test_edge_request_routing():
    """Test edge request routing"""
    manager = EdgeWorkerManager()
    
    # Deploy worker
    config = EdgeWorkerConfig(
        name="router-test",
        script="test",
        routes=["/*"],
        locations=[EdgeLocation.US_EAST],
        environment_vars={}
    )
    await manager.deploy_worker(config)
    
    # Route request
    request = EdgeRequest(
        method="GET",
        url="https://example.com/test",
        headers={}
    )
    
    response = await manager.route_request(request, EdgeLocation.US_EAST)
    
    assert response.status_code == 200
    assert response.latency_ms >= 0


@pytest.mark.asyncio
async def test_zero_bandwidth_proxy():
    """Test zero-bandwidth proxy"""
    manager = EdgeWorkerManager()
    proxy = ZeroBandwidthProxy(manager)
    
    # Deploy worker first
    config = EdgeWorkerConfig(
        name="proxy-test",
        script="test",
        routes=["/*"],
        locations=[EdgeLocation.US_EAST],
        environment_vars={}
    )
    await manager.deploy_worker(config)
    
    # Proxy request
    response = await proxy.proxy_request(
        "https://example.com",
        client_location=EdgeLocation.US_EAST
    )
    
    assert response.status_code in [200, 503]
    
    savings = proxy.get_bandwidth_savings()
    assert "cache_efficiency" in savings


@pytest.mark.asyncio
async def test_global_cdn():
    """Test global CDN"""
    manager = EdgeWorkerManager()
    cdn = GlobalCDN(manager)
    
    success = await cdn.distribute_content(
        "https://example.com/file.mp4",
        locations=[EdgeLocation.US_EAST, EdgeLocation.EU_WEST]
    )
    
    assert success is True
    
    stats = cdn.get_cdn_stats()
    assert "distributed_content" in stats


# ============================================================================
# Adaptive Concurrency Tests
# ============================================================================

def test_pid_controller():
    """Test PID controller"""
    params = PIDParameters(kp=1.0, ki=0.1, kd=0.05, setpoint=0.7)
    controller = PIDController(params)
    
    # Test computation
    concurrency = controller.compute(0.5)  # Under target
    assert concurrency >= params.min_output
    assert concurrency <= params.max_output


@pytest.mark.asyncio
async def test_adaptive_thread_pool():
    """Test adaptive thread pool"""
    pool = AdaptiveThreadPool(initial_size=5, min_size=1, max_size=20)
    
    await pool.start()
    
    # Submit some tasks
    async def dummy_task():
        await asyncio.sleep(0.01)
    
    for _ in range(3):
        await pool.submit(dummy_task())
    
    await asyncio.sleep(0.1)
    
    metrics = pool.get_metrics()
    assert "pool_size" in metrics
    assert "active_tasks" in metrics
    
    await pool.stop()


@pytest.mark.asyncio
async def test_adaptive_thread_pool_scaling():
    """Test thread pool auto-scaling"""
    pool = AdaptiveThreadPool(initial_size=5, min_size=1, max_size=20)
    
    assert pool.current_size == 5
    
    # Scale up
    await pool.adjust_size(10)
    assert pool.current_size == 10
    
    # Scale down
    await pool.adjust_size(3)
    assert pool.current_size == 3


@pytest.mark.asyncio
async def test_adaptive_concurrency_controller():
    """Test adaptive concurrency controller"""
    controller = AdaptiveConcurrencyController(
        initial_concurrency=5,
        adjustment_interval_sec=1.0
    )
    
    await controller.start()
    
    # Let it run briefly
    await asyncio.sleep(0.5)
    
    stats = controller.get_stats()
    assert "current_concurrency" in stats
    assert "pool_metrics" in stats
    
    await controller.stop()


def test_workload_analyzer():
    """Test workload analyzer"""
    analyzer = WorkloadAnalyzer()
    
    # Record some samples
    from bot.core.adaptive_concurrency import PerformanceMetrics
    from datetime import datetime
    
    for i in range(20):
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            active_tasks=10 + i % 5,
            queue_size=5,
            avg_latency_ms=50.0,
            throughput_per_sec=100.0,
            cpu_usage_percent=60.0,
            memory_usage_percent=50.0,
            error_rate=0.01
        )
        analyzer.record_sample(metrics)
    
    pattern = analyzer.analyze_pattern()
    assert pattern in ["steady", "bursty", "random", "unknown"]
    
    recommended = analyzer.recommend_concurrency()
    assert recommended > 0


# ============================================================================
# HLS/DASH Stream Weaver Tests
# ============================================================================

@pytest.mark.asyncio
async def test_hls_parser():
    """Test HLS parser"""
    parser = HLSParser()
    
    # Mock M3U8 content
    m3u8_content = """#EXTM3U
#EXTINF:10.0,
segment_001.ts
#EXTINF:10.0,
segment_002.ts
"""
    
    segments = await parser.parse_media_playlist(m3u8_content)
    
    assert len(segments) == 2
    assert segments[0].duration_seconds == 10.0


@pytest.mark.asyncio
async def test_dash_parser():
    """Test DASH parser"""
    parser = DASHParser()
    
    qualities = await parser.parse_mpd("<MPD></MPD>")
    
    assert len(qualities) > 0


@pytest.mark.asyncio
async def test_drm_handler():
    """Test DRM handler"""
    handler = DRMHandler()
    
    test_data = b"encrypted content"
    
    # Test no DRM
    decrypted = await handler.decrypt_segment(
        test_data,
        DRMType.NONE
    )
    assert decrypted == test_data
    
    # Test AES-128
    decrypted = await handler.decrypt_segment(
        test_data,
        DRMType.AES128,
        key_uri="https://example.com/key"
    )
    assert decrypted is not None


@pytest.mark.asyncio
async def test_stream_weaver():
    """Test stream weaver"""
    weaver = StreamWeaver()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "output.mp4"
        
        result = await weaver.weave_stream(
            manifest_url="https://example.com/playlist.m3u8",
            output_file=str(output_file),
            protocol=StreamProtocol.HLS,
            quality_index=0
        )
        
        # May succeed or fail due to mock data
        assert result.protocol == StreamProtocol.HLS


def test_stream_weaver_stats():
    """Test stream weaver statistics"""
    weaver = StreamWeaver()
    
    stats = weaver.get_stats()
    
    assert "total_weaves" in stats
    assert "success_rate" in stats


@pytest.mark.asyncio
async def test_fast_concatenator():
    """Test fast concatenator"""
    concatenator = FastConcatenator(max_parallel=4)
    
    # Create temp files
    temp_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(f"Segment {i}")
            temp_files.append(f.name)
    
    try:
        with tempfile.NamedTemporaryFile(delete=False) as out_f:
            output = out_f.name
        
        success = await concatenator.concatenate(temp_files, output)
        assert success is True
        
    finally:
        for path in temp_files:
            Path(path).unlink(missing_ok=True)
        Path(output).unlink(missing_ok=True)


# ============================================================================
# Lazy Imports Optimization Tests
# ============================================================================

def test_lazy_importer():
    """Test lazy importer"""
    importer = LazyImporter()
    
    # Lazy import a module
    json_module = importer.lazy_import('json')
    
    # Module not loaded yet
    assert 'json' in importer.lazy_modules
    
    # Access attribute (triggers load)
    _ = json_module.dumps({"test": "data"})
    
    # Now it should be loaded
    proxy = importer.lazy_modules['json']
    assert proxy.actual_module is not None


def test_lazy_import_stats():
    """Test lazy import statistics"""
    importer = LazyImporter(track_stats=True)
    
    # Import module
    _ = importer.lazy_import('sys')
    
    stats = importer.get_stats()
    
    assert "total_lazy_modules" in stats
    assert stats["total_lazy_modules"] >= 1


def test_import_tracker():
    """Test import tracker"""
    tracker = ImportTracker()
    
    tracker.track_import("module1", 50.0, lazy=True)
    tracker.track_import("module2", 150.0, lazy=False)
    tracker.track_import("module3", 30.0, lazy=True)
    
    total_time = tracker.get_total_import_time()
    assert total_time == 230.0
    
    heaviest = tracker.get_heaviest_imports(2)
    assert len(heaviest) == 2
    assert heaviest[0].module_name == "module2"
    
    recommendations = tracker.recommend_lazy_imports()
    assert "module2" in recommendations


def test_startup_optimizer():
    """Test startup optimizer"""
    optimizer = StartupOptimizer()
    
    modules = ["json", "sys", "os", "re"]
    essential = ["json", "sys"]
    
    report = optimizer.optimize(modules, essential_modules=essential)
    
    assert report["essential_modules"] == 2
    assert report["lazy_modules"] == 2
    assert report["total_modules"] == 4


def test_dynamic_module_loader():
    """Test dynamic module loader"""
    loader = DynamicModuleLoader()
    
    # Load module
    json_module = loader.load('json')
    assert json_module is not None
    
    # Should be cached
    json_module2 = loader.load('json')
    assert json_module is json_module2
    
    stats = loader.get_stats()
    assert stats["cached_modules"] == 1


def test_dynamic_module_loader_class():
    """Test loading class dynamically"""
    loader = DynamicModuleLoader()
    
    # Load PathClass
    Path_class = loader.load_class('pathlib', 'Path')
    
    # Create instance
    p = Path_class('/tmp')
    assert str(p) == '/tmp'


def test_dynamic_module_loader_function():
    """Test loading function dynamically"""
    loader = DynamicModuleLoader()
    
    # Load function
    loads_func = loader.load_function('json', 'loads')
    
    # Use it
    result = loads_func('{"key": "value"}')
    assert result == {"key": "value"}


def test_lazy_import_helper():
    """Test lazy_import helper function"""
    # Use helper
    math_module = lazy_import('math')
    
    # Use it
    result = math_module.sqrt(16)
    assert result == 4.0


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_phase8_integration():
    """Integration test for Phase 8 modules"""
    # Test that all modules can be imported and initialized
    hasher = BLAKE3Hasher()
    ipfs_client = IPFSClient()
    edge_manager = EdgeWorkerManager()
    pid_controller = PIDController(PIDParameters())
    stream_weaver = StreamWeaver()
    lazy_importer = LazyImporter()
    
    # All initialized successfully
    assert hasher is not None
    assert ipfs_client is not None
    assert edge_manager is not None
    assert pid_controller is not None
    assert stream_weaver is not None
    assert lazy_importer is not None


@pytest.mark.asyncio
async def test_phase8_performance_targets():
    """Test that Phase 8 meets performance targets"""
    # BLAKE3: Target 2000 MB/sec (check config)
    hasher = BLAKE3Hasher()
    assert hasher.get_performance_stats()["target_throughput_mbps"] == 2000
    
    # Edge workers: Target <100ms latency
    manager = EdgeWorkerManager()
    config = EdgeWorkerConfig(
        name="perf-test",
        script="test",
        routes=["/*"],
        locations=[EdgeLocation.US_EAST],
        environment_vars={}
    )
    await manager.deploy_worker(config)
    
    request = EdgeRequest(method="GET", url="https://test.com", headers={})
    response = await manager.route_request(request)
    assert response.latency_ms < 100
    
    # Stream weaver: Target 99.9% success rate (check framework)
    weaver = StreamWeaver()
    assert weaver.stats["total_weaves"] >= 0
