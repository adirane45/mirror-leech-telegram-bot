"""
Comprehensive tests for Phase 7 infrastructure modules

Tests:
- Monitoring & observability
- Security & access control
- Resilience & recovery
- API gateway enhancements
- Advanced caching
- Data migration
- Infrastructure as code
- Testing framework
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta

from bot.core.monitoring import (
    SystemHealthMonitor,
    SLAMonitor,
    DistributedTracer,
    HealthStatus
)
from bot.core.security import (
    TokenBucketRateLimiter,
    RequestSigner,
    DataEncryptor,
    RoleBasedAccessControl,
    AuditTrail,
    UserRole,
    Permission
)
from bot.core.resilience import (
    FailoverManager,
    GracefulDegradation,
    CanaryDeployment,
    DataConsistencyManager,
    FailoverState
)
from bot.core.api_enhancements import (
    APIGateway,
    AuthenticationMiddleware,
    RateLimitMiddleware,
    CORSMiddleware,
    APIVersion,
    Request,
    Response
)
from bot.core.caching import (
    L1MemoryCache,
    BloomFilter,
    MultiLevelCache,
    CachePolicy,
    InvalidationStrategy
)
from bot.core.data_migration import (
    MigrationExecutor,
    SchemaVersionManager,
    DataAuditTrail,
    SchemaValidator
)
from bot.core.infrastructure import (
    ConfigValidator,
    SecretManager,
    ConfigurationManager,
    DriftDetector,
    Environment
)
from bot.core.testing import (
    TestRunner,
    CoverageAnalyzer,
    PerformanceBenchmarker,
    LoadSimulator,
    ContractTester,
    TestType
)


# --- MONITORING TESTS ---

@pytest.mark.asyncio
async def test_health_monitor():
    """Test system health monitoring"""
    monitor = SystemHealthMonitor()
    
    # Register checks
    await monitor.register_check(
        "cpu_check",
        lambda: True,
        critical=True
    )
    await monitor.register_check(
        "memory_check",
        lambda: True,
        critical=False
    )
    
    # Run checks
    result = await monitor.run_all_checks()
    
    assert result.status == HealthStatus.HEALTHY
    assert len(result.checks) == 2
    assert "cpu_check" in result.checks


@pytest.mark.asyncio
async def test_sla_monitor():
    """Test SLA monitoring"""
    sla = SLAMonitor()
    
    # Register SLA
    sla.register_sla(
        "api_endpoint",
        target_uptime=0.99,
        max_response_time_ms=1000
    )
    
    # Record requests
    result = sla.record_request("api_endpoint", 500, True)
    assert result is True
    
    # Record violation
    result = sla.record_request("api_endpoint", 2000, True)
    assert result is False
    
    # Check status
    status = sla.get_sla_status()
    assert "api_endpoint" in status


def test_distributed_tracer():
    """Test distributed tracing"""
    tracer = DistributedTracer()
    
    # Start trace
    trace_id = tracer.start_trace("download_operation")
    assert trace_id is not None
    
    # Add spans
    tracer.add_span(trace_id, "fetch_file", 100, "success")
    tracer.add_span(trace_id, "upload_to_telegram", 200, "success")
    
    # End trace
    trace = tracer.end_trace(trace_id)
    assert trace is not None
    assert len(trace["spans"]) == 2


# --- SECURITY TESTS ---

def test_token_bucket_rate_limiter():
    """Test token bucket rate limiting"""
    limiter = TokenBucketRateLimiter(rate=10, bucket_size=100)
    
    # Allow first requests
    assert limiter.allow_request() is True
    assert limiter.allow_request(50) is True
    
    # Should have 49 tokens left
    assert limiter.allow_request(50) is False


def test_request_signer():
    """Test request signing"""
    signer = RequestSigner("secret_key_123")
    
    # Sign request
    timestamp = datetime.now(timezone.utc).isoformat()
    signature = signer.sign_request(
        "POST",
        "/api/upload",
        body='{"file": "test.zip"}',
        timestamp=timestamp
    )
    
    assert signature is not None
    assert len(signature) == 64  # SHA-256 hex
    
    # Verify signature
    valid = signer.verify_signature(
        "POST",
        "/api/upload",
        signature,
        body='{"file": "test.zip"}',
        timestamp=timestamp
    )
    
    assert valid is True


def test_data_encryptor():
    """Test data encryption"""
    encryptor = DataEncryptor("encryption_key")
    
    # Encrypt
    plaintext = "sensitive_password_123"
    encrypted = encryptor.encrypt(plaintext)
    
    assert encrypted != plaintext
    assert len(encrypted) > 0
    
    # Decrypt
    decrypted = encryptor.decrypt(encrypted)
    assert decrypted == plaintext


def test_rbac():
    """Test role-based access control"""
    rbac = RoleBasedAccessControl()
    
    # Check admin permissions
    assert rbac.check_permission(UserRole.ADMIN, "users", "create") is True
    assert rbac.check_permission(UserRole.USER, "users", "create") is False
    
    # Grant permission
    rbac.grant_permission(UserRole.USER, Permission("tasks", "create"))
    assert rbac.check_permission(UserRole.USER, "tasks", "create") is True


def test_audit_trail():
    """Test audit trail"""
    trail = AuditTrail()
    
    # Log actions
    trail.log_action(
        user_id="user123",
        action="update",
        resource="user:user456",
        old_value={"role": "user"},
        new_value={"role": "admin"}
    )
    
    # Verify integrity
    assert trail.verify_integrity() is True
    
    # Get entries
    entries = trail.get_entries(user_id="user123")
    assert len(entries) == 1
    assert entries[0]["action"] == "update"


# --- RESILIENCE TESTS ---

@pytest.mark.asyncio
async def test_failover_manager():
    """Test failover management"""
    manager = FailoverManager()
    
    # Register instances
    manager.register_instance("primary", "http://primary:8000")
    manager.register_instance("backup", "http://backup:8000")
    
    # Send heartbeats
    manager.heartbeat("primary", healthy=True)
    manager.heartbeat("backup", healthy=True)
    
    # Check health
    health = await manager.check_health()
    assert len(health["healthy"]) == 2


@pytest.mark.asyncio
async def test_graceful_degradation():
    """Test graceful degradation"""
    degradation = GracefulDegradation()
    
    # Register feature
    degradation.register_feature("video_streaming", enabled=True)
    assert degradation.is_enabled("video_streaming") is True
    
    # Degrade feature
    degradation.degrade_feature("video_streaming")
    assert degradation.is_enabled("video_streaming") is False
    
    # Restore feature
    degradation.restore_feature("video_streaming")
    assert degradation.is_enabled("video_streaming") is True


@pytest.mark.asyncio
async def test_canary_deployment():
    """Test canary deployment"""
    canary = CanaryDeployment()
    
    # Deploy canary
    canary.deploy_canary("v2.0", traffic_percent=10)
    assert canary.canary_version == "v2.0"
    assert canary.canary_traffic_percent == 10
    
    # Record metrics (simulate success)
    for _ in range(100):
        canary.record_canary_metric(True, 50.0)
    
    # Promote canary
    result = await canary.promote_canary()
    assert result is True


#--- API GATEWAY TESTS ---

@pytest.mark.asyncio
async def test_authentication_middleware():
    """Test authentication middleware"""
    middleware = AuthenticationMiddleware()
    middleware.add_token("valid_token_123")
    
    # Valid token
    request = Request(
        method="GET",
        path="/api/data",
        headers={"Authorization": "Bearer valid_token_123"}
    )
    response = await middleware.process_request(request)
    assert response is None  # Passes through
    
    # Invalid token
    request2 = Request(
        method="GET",
        path="/api/data",
        headers={"Authorization": "Bearer invalid_token"}
    )
    response2 = await middleware.process_request(request2)
    assert response2.status_code == 401


@pytest.mark.asyncio
async def test_rate_limit_middleware():
    """Test rate limiting middleware"""
    middleware = RateLimitMiddleware(requests_per_second=2)
    
    # First requests should pass
    request = Request(method="GET", path="/api/data")
    assert await middleware.process_request(request) is None
    assert await middleware.process_request(request) is None
    
    # Third should be blocked
    response = await middleware.process_request(request)
    assert response.status_code == 429


# --- CACHING TESTS ---

def test_l1_memory_cache():
    """Test L1 memory cache"""
    cache = L1MemoryCache(max_size=100, strategy=InvalidationStrategy.LRU)
    
    # Set values
    cache.set("key1", "value1", ttl_seconds=60)
    cache.set("key2", "value2", ttl_seconds=60)
    
    # Get values
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    
    # Invalidate
    cache.invalidate("key1")
    assert cache.get("key1") is None


def test_bloom_filter():
    """Test bloom filter"""
    bf = BloomFilter(size=1000, hash_functions=3)
    
    # Add items
    bf.add("item1")
    bf.add("item2")
    
    # Check membership
    assert bf.might_contain("item1") is True
    assert bf.might_contain("item2") is True
    assert bf.might_contain("item3") in [True, False]  # May have false positive


@pytest.mark.asyncio
async def test_multi_level_cache():
    """Test multi-level cache"""
    cache = MultiLevelCache(CachePolicy(ttl_seconds=60))
    
    # Set value
    await cache.set("test_key", "test_value")
    
    # Get value
    value = await cache.get("test_key")
    assert value == "test_value"


# --- MIGRATION TESTS ---

@pytest.mark.asyncio
async def test_migration_executor():
    """Test migration executor"""
    executor = MigrationExecutor()
    
    # Register migration
    def up():
        pass
    
    def down():
        pass
    
    executor.register_migration(
        version="001",
        description="Initial migration",
        up=up,
        down=down
    )
    
    # Apply migration
    result = await executor.apply_migration("001")
    assert result is True
    assert "001" in executor.applied_versions


def test_schema_version_manager():
    """Test schema versioning"""
    manager = SchemaVersionManager()
    
    # Register version
    manager.register_version(
        version=1,
        changes=["CREATE TABLE users", "ADD INDEX user_id"]
    )
    
    assert manager.current_version == 1
    
    # Get version info
    info = manager.get_version_info(1)
    assert info is not None
    assert len(info["changes"]) == 2


def test_data_audit_trail():
    """Test data audit trail"""
    trail = DataAuditTrail()
    
    # Log change
    trail.log_change(
        table_name="users",
        operation="UPDATE",
        record_id=123,
        old_value={"name": "old"},
        new_value={"name": "new"},
        user_id="admin"
    )
    
    # Get history
    history = trail.get_history("users", 123)
    assert len(history) == 1
    assert history[0]["operation"] == "UPDATE"


# --- INFRASTRUCTURE TESTS ---

def test_config_validator():
    """Test configuration validation"""
    validator = ConfigValidator()
    
    # Add rules
    validator.add_rule("port", lambda x: 1 <= x <= 65535)
    validator.add_rule("host", lambda x: isinstance(x, str) and len(x) > 0)
    
    # Valid config
    config = {"port": 8080, "host": "localhost"}
    errors = validator.validate(config)
    assert len(errors) == 0
    
    # Invalid config
    config2 = {"port": 99999, "host": ""}
    errors2 = validator.validate(config2)
    assert len(errors2) == 2


def test_secret_manager():
    """Test secret management"""
    manager = SecretManager()
    
    # Store secret
    manager.store_secret("db_password", "secret123", user_id="admin")
    
    # Retrieve secret
    password = manager.get_secret("db_password", user_id="user1")
    assert password == "secret123"
    
    # Rotate secret
    result = manager.rotate_secret("db_password", "new_secret456", user_id="admin")
    assert result is True


def test_drift_detector():
    """Test infrastructure drift detection"""
    detector = DriftDetector()
    
    # Capture baseline
    baseline = {"server_count": 5, "memory_gb": 32}
    detector.capture_baseline(baseline)
    
    # Scan current state
    current = {"server_count": 6, "memory_gb": 32}
    detector.scan_current_state(current)
    
    # Detect drift
    drift = detector.detect_drift()
    assert drift["drift_detected"] is True
    assert len(drift["modified_items"]) == 1


# --- TESTING FRAMEWORK TESTS ---

@pytest.mark.asyncio
async def test_test_runner():
    """Test the test runner"""
    runner = TestRunner()
    
    # Register test
    async def sample_test():
        assert 1 + 1 == 2
    
    runner.register_test("sample_test", sample_test, TestType.UNIT)
    
    # Run test
    result = await runner.run_test("sample_test")
    assert result.status == "passed"


def test_coverage_analyzer():
    """Test coverage analysis"""
    analyzer = CoverageAnalyzer()
    
    # Add coverage data
    analyzer.add_coverage("module1", 0.95)
    analyzer.add_coverage("module2", 0.70)
    
    # Calculate total
    total = analyzer.get_total_coverage()
    assert total == 0.825  # Average
    
    # Get uncovered
    uncovered = analyzer.get_uncovered_modules()
    assert "module2" in uncovered


@pytest.mark.asyncio
async def test_performance_benchmarker():
    """Test performance benchmarking"""
    benchmarker = PerformanceBenchmarker()
    
    # Benchmark operation
    def fast_operation():
        return sum(range(100))
    
    benchmark = await benchmarker.benchmark(
        "fast_operation",
        fast_operation,
        iterations=10
    )
    
    assert benchmark.iterations == 10
    assert benchmark.avg_time_ms > 0


def test_contract_tester():
    """Test API contract testing"""
    tester = ContractTester()
    
    # Define contract
    tester.define_contract(
        name="upload_file",
        endpoint="/api/upload",
        request_schema={"file_name": str, "file_size": int},
        response_schema={"task_id": str, "status": str}
    )
    
    # Test valid contract
    request = {"file_name": "test.zip", "file_size": 1024}
    response = {"task_id": "task123", "status": "pending"}
    
    valid, error = asyncio.run(
        tester.verify_contract("upload_file", request, response)
    )
    assert valid is True
    assert error is None
