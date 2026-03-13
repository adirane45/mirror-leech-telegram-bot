# Code Quality, Architecture & Optimization Improvement Roadmap

**Project**: Mirror Leech Telegram Bot  
**Generated**: March 8, 2026  
**Current State**: 82K+ LOC, 154 core modules, gradual type-safety adoption

---

## Executive Summary

### Current Assessment
- ✅ **Strengths**: Comprehensive features, Docker/K8s ready, monitoring infrastructure, pre-commit hooks
- ⚠️ **Critical Issues**: Architectural bloat (154 core files), inconsistent type safety, test coverage gaps
- 🎯 **Primary Goals**: Reduce complexity, improve maintainability, enhance type safety, optimize performance

### 🤖 GitHub Copilot Integration

This improvement plan is designed to work seamlessly with GitHub Copilot:
- **Structured prompts** provided for each major task
- **Session management** guidelines to avoid token limits
- **Context preservation** strategies across implementation
- **Dedicated guide**: [GITHUB_COPILOT_STRATEGY.md](GITHUB_COPILOT_STRATEGY.md) (30+ pages)

**Key Benefits**:
- 2-3x faster implementation with AI pair programming
- Excellent for test generation (saves 60-70% of time)
- Helps maintain consistency across refactoring
- Type hint suggestions reduce mypy errors

**See**: Week-by-week Copilot session plans in each priority section below

---

## Priority 1: Critical Architecture & Code Quality (Weeks 1-4)

### 1.1 Core Module Consolidation [HIGH IMPACT]
**Problem**: 154 files in `src/bot/core/` - massive architectural bloat  
**Impact**: High maintenance burden, difficult navigation, code duplication

**Action Items**:
- [ ] **Audit and categorize** core modules by domain (Week 1)
  ```bash
  # Create domain mapping
  src/bot/core/
    ├── download/          # Download-related managers
    ├── storage/           # Cache, Redis, file management
    ├── monitoring/        # Metrics, alerts, health checks
    ├── api/              # API gateway, endpoints
    ├── security/         # Auth, secrets, rate limiting
    ├── task_management/  # Celery, queues, scheduling
    └── infrastructure/   # Core utilities
  ```

- [ ] **Merge similar managers** (Week 2)
  - Consolidate: `failover_manager.py`, `failover_cascade_detector.py`, `failover_recovery_executor.py`, `failover_models.py` → `resilience/failover_system.py`
  - Consolidate: `cache_manager.py`, `advanced_cache.py`, `file_cache_manager.py` → `storage/cache_system.py`
  - Consolidate: `dashboard_manager.py`, `dashboard_routes.py`, `dashboard_html.py`, `advanced_dashboard*.py` → `api/dashboard/`
  - Consolidate: `alert_manager.py`, `alert_manager_models.py`, `command_alert_system.py` → `monitoring/alerts.py`

- [ ] **Apply Facade pattern** (Week 3)
  - Create unified interfaces for related subsystems
  - Example: `DownloadCoordinator` facade over aria2/qbittorrent/sabnzbd managers

- [ ] **Remove duplicate/dead code** (Week 3-4)
  - Search for `enhanced_startup.py` vs `enhanced_startup_new.py` - remove outdated
  - Check for unused imports and functions using `vulture`
  - Remove archived features noted in comments

**Expected Outcome**: Reduce core modules from 154 → ~60-70, improve discoverability by 60%

---

### 1.2 Type Safety Expansion [HIGH PRIORITY]
**Problem**: `strict = false` globally, only 5 modules strictly typed  
**Current**: Types enabled for config and 4 core modules

**Action Items**:
- [ ] **Phase 1: Expand strict typing** (Week 1-2)
  ```toml
  # Add to pyproject.toml strict overrides
  [[tool.mypy.overrides]]
  module = [
      "src.bot.core.cache_manager",
      "src.bot.core.alert_manager", 
      "src.bot.core.rate_limiter",
      "src.bot.core.batch_processor",
      "src.bot.core.task_coordinator",
      "src.bot.helper.ext_utils.bot_utils",
  ]
  strict = true
  ```

- [ ] **Phase 2: Add return type annotations** (Week 2-3)
  - Run `mypy --strict` on each module incrementally
  - Add missing return types (focus on public APIs first)
  - Document complex types with TypedDict/Protocol

- [ ] **Phase 3: Enable stricter checks globally** (Week 4)
  ```toml
  [tool.mypy]
  check_untyped_defs = true           # ✅ Already enabled
  disallow_untyped_defs = true        # Enable for new code
  disallow_any_unimported = true      # Prevent implicit Any
  warn_return_any = true              # Catch loose returns
  ```

- [ ] **Add typed interfaces** for third-party integrations
  - Create Protocol definitions for MyJD, Rclone, SABnzbd APIs
  - Move to `src/bot/interfaces/`

**Expected Outcome**: 80% of codebase with proper type hints, catch 30-40% more bugs at compile time

---

### 1.3 Dependency Injection & Testability [MEDIUM-HIGH]
**Problem**: Tight coupling, global state, difficult to test

**Action Items**:
- [ ] **Implement DI container** (Week 2-3)
  ```python
  # src/bot/core/di_container.py
  from dependency_injector import containers, providers
  
  class CoreContainer(containers.DeclarativeContainer):
      config = providers.Singleton(Config)
      logger = providers.Singleton(LoggerManager, config=config)
      cache = providers.Singleton(CacheManager, config=config)
      rate_limiter = providers.Singleton(RateLimiter, cache=cache)
      # ... etc
  ```

- [ ] **Refactor managers to accept dependencies** (Week 3-4)
  ```python
  class AlertManager:
      def __init__(self, config: Config, logger: LoggerManager, 
                   telegram: TelegramManager):
          self.config = config
          self.logger = logger
          self.telegram = telegram
  ```

- [ ] **Remove global imports** from `src/bot/__init__.py`
  - Pass dependencies explicitly instead of importing LOGGER globally

**Expected Outcome**: 50% easier to write unit tests, enable mocking for integration tests

---

## Priority 2: Testing & Quality Assurance (Weeks 3-6)

### 2.1 Expand Test Coverage [CRITICAL]
**Current**: Test structure exists, but collection issues noted in Makefile

**Action Items**:
- [ ] **Fix test collection issues** (Week 3)
  ```bash
  pytest tests/ --collect-only  # Identify broken imports
  # Fix circular dependencies and missing __init__.py files
  ```

- [ ] **Establish coverage baseline** (Week 3)
  ```bash
  pytest tests/ --cov=src --cov-report=html --cov-report=term
  # Target: 60% coverage baseline
  ```

- [ ] **Add unit tests for critical paths** (Week 4-5)
  - Priority test targets:
    - ✅ Core managers: AlertManager, CacheManager, RateLimiter
    - ✅ Download coordinators: Aria2, qBittorrent handlers
    - ✅ Upload handlers: Google Drive, Rclone
    - ✅ Security: Input validation, rate limiting
    - ✅ Task management: Celery task routing

- [ ] **Add integration tests** (Week 5-6)
  - Test full download → upload pipelines with mocked clients
  - Test failover scenarios
  - Test rate limiting under load

- [ ] **Set up coverage enforcement** (Week 6)
  ```yaml
  # .github/workflows/ci.yml
  - name: Test with coverage
    run: |
      pytest tests/ --cov=src --cov-fail-under=60
  ```

**Expected Outcome**: 60-70% test coverage, catch regressions in CI

---

### 2.2 Performance Testing Framework [MEDIUM]
**Action Items**:
- [ ] **Set up locust/k6 load testing** (Week 4)
  ```python
  # tests/performance/test_load.py
  from locust import HttpUser, task, between
  
  class BotAPIUser(HttpUser):
      wait_time = between(1, 3)
      
      @task
      def download_task(self):
          self.client.post("/api/v1/download", json={...})
  ```

- [ ] **Add benchmark tests** for critical operations
  - Download speed benchmarks
  - Upload throughput
  - Cache hit rates
  - API response times

- [ ] **Set up continuous benchmarking** in CI
  - Track performance metrics over time
  - Alert on performance regressions (>10% slower)

**Expected Outcome**: Prevent performance regressions, baseline metrics established

---

## Priority 3: Performance Optimization (Weeks 5-8)

### 3.1 Async/Await Optimization [HIGH IMPACT]
**Problem**: Potential blocking I/O, underutilized concurrency

**Action Items**:
- [ ] **Audit blocking operations** (Week 5)
  ```bash
  # Find potential blocking calls
  grep -r "requests\." src/  # Should use httpx/aiohttp
  grep -r "open(" src/      # Should use aiofiles
  ```

- [ ] **Replace blocking I/O** (Week 5-6)
  - `requests` → `httpx` or `aiohttp`
  - File operations → `aiofiles`
  - Database queries → use async drivers

- [ ] **Add async context managers** (Week 6)
  ```python
  class AsyncDownloadManager:
      async def __aenter__(self):
          await self.initialize()
          return self
      
      async def __aexit__(self, *args):
          await self.cleanup()
  ```

- [ ] **Implement connection pooling** (Week 6-7)
  - Configure async HTTP client pools
  - Redis connection pooling (already exists, optimize configuration)
  - Database connection pooling

**Expected Outcome**: 30-50% improvement in concurrent operations, reduced latency

---

### 3.2 Caching Strategy Enhancement [MEDIUM]
**Current**: Multiple cache implementations, potential redundancy

**Action Items**:
- [ ] **Audit cache usage** (Week 6)
  - Identify cache hit rates
  - Find redundant caching layers
  - Measure cache memory usage

- [ ] **Implement cache hierarchy** (Week 7)
  ```python
  # L1: In-memory LRU (fast, small)
  # L2: Redis (medium speed, larger)
  # L3: Disk cache (slow, unlimited)
  class HierarchicalCache:
      async def get(self, key: str) -> Optional[Any]:
          # Try L1 → L2 → L3
          # Promote to higher levels on hit
  ```

- [ ] **Add cache warming** for predictable queries (Week 7)
- [ ] **Implement cache invalidation strategy** (Week 8)
  - Time-based expiration (TTL)
  - Event-based invalidation
  - Size-based eviction (LRU/LFU)

**Expected Outcome**: 20-30% reduction in external API calls, improved response times

---

### 3.3 Database Query Optimization [MEDIUM]
**Action Items**:
- [ ] **Add query performance monitoring** (Week 7)
  - Log slow queries (>100ms)
  - Identify N+1 query patterns

- [ ] **Add database indexes** (Week 7-8)
  - Index frequently queried fields
  - Composite indexes for common query patterns

- [ ] **Implement query result caching** (Week 8)
  - Cache expensive aggregations
  - Invalidate on writes

**Expected Outcome**: 40-60% reduction in query time for common operations

---

## Priority 4: Code Quality Tooling (Weeks 6-8)

### 4.1 Enhanced Linting & Static Analysis [MEDIUM]
**Action Items**:
- [ ] **Add complexity checks** (Week 6)
  ```ini
  # .pylintrc
  [DESIGN]
  max-complexity = 10      # Reduce from default 15
  max-args = 5             # Limit function parameters
  max-locals = 15          # Limit local variables
  ```

- [ ] **Enable stricter flake8 plugins** (Week 6)
  ```bash
  pip install flake8-comprehensions flake8-builtins flake8-simplify
  ```

- [ ] **Add security scanning** (Week 7)
  ```yaml
  # .github/workflows/security.yml
  - name: Bandit Security Scan
    run: bandit -r src/ -f json -o bandit-report.json
  
  - name: Safety Check
    run: safety check --json
  ```

- [ ] **Set up code complexity reports** (Week 7)
  ```bash
  # Add to CI
  radon cc src/ -a -nb
  radon mi src/ --min B  # Maintainability index
  ```

**Expected Outcome**: Prevent code smell introduction, enforced quality gates

---

### 4.2 Documentation Enhancement [LOW-MEDIUM]
**Action Items**:
- [ ] **Add docstring enforcement** (Week 7)
  ```python
  # Enable in flake8
  [flake8]
  docstring-convention = google
  require-return-type-hint = True
  ```

- [ ] **Generate API documentation** (Week 8)
  ```bash
  # Add to docs/
  mkdocs build
  # or
  sphinx-build -b html docs/ docs/_build
  ```

- [ ] **Add architecture decision records (ADRs)** (Week 8)
  - Document major architectural decisions
  - Template in `docs/architecture/adr/`

**Expected Outcome**: Improved developer onboarding, better code understanding

---

## Priority 5: CI/CD & DevOps (Weeks 7-10)

### 5.1 Enhanced CI Pipeline [MEDIUM]
**Action Items**:
- [ ] **Parallel test execution** (Week 7)
  ```yaml
  strategy:
    matrix:
      test-suite: [unit, integration, performance]
  ```

- [ ] **Add PR quality gates** (Week 8)
  - Block merge if:
    - Coverage drops below threshold
    - Linting fails
    - Type checking fails
    - Security vulnerabilities detected

- [ ] **Set up automated dependency updates** (Week 8)
  ```yaml
  # .github/dependabot.yml
  version: 2
  updates:
    - package-ecosystem: "pip"
      directory: "/requirements"
      schedule:
        interval: "weekly"
  ```

**Expected Outcome**: Faster feedback, prevent quality regressions

---

### 5.2 Monitoring & Observability [MEDIUM-HIGH]
**Current**: Prometheus + Grafana + OpenTelemetry configured

**Action Items**:
- [ ] **Add custom business metrics** (Week 8)
  ```python
  from prometheus_client import Counter, Histogram
  
  download_requests = Counter('download_requests_total', 'Total downloads')
  upload_duration = Histogram('upload_duration_seconds', 'Upload time')
  ```

- [ ] **Implement distributed tracing** (Week 9)
  - Add OpenTelemetry spans to critical paths
  - Track request flow through services

- [ ] **Set up alerting rules** (Week 9)
  ```yaml
  # alerts.yml
  - alert: HighErrorRate
    expr: rate(http_errors_total[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
  ```

- [ ] **Add log aggregation** (Week 9-10)
  - Centralize logs from all services
  - Set up log-based alerts

**Expected Outcome**: Proactive issue detection, improved incident response

---

## Quick Wins (Can be done in parallel)

### Immediate Improvements (Week 1)
1. **Enable autoflake in pre-commit** - Remove unused imports automatically
2. **Add .editorconfig** - Ensure consistent code style
3. **Set up GitHub issue templates** - Standardize bug reports/feature requests
4. **Add CODEOWNERS** - Auto-assign reviewers for critical paths
5. **Create PR template** - Ensure checklist compliance

### Low-hanging fruit (Weeks 1-2)
1. **Remove TODO/FIXME comments** - Convert to GitHub issues
2. **Standardize error messages** - Create error code catalog
3. **Add logging levels audit** - Ensure appropriate log levels
4. **Create development Docker compose** - Faster local setup
5. **Add make targets for common tasks** - Already partially done, expand

---

## Metrics & Success Criteria

### Code Quality Metrics
- **Cyclomatic Complexity**: Average < 10 per function ✅
- **Type Coverage**: > 80% of public APIs typed ✅
- **Test Coverage**: > 60% overall, > 80% for core modules ✅
- **Maintainability Index**: > 70 (B grade) ✅

### Performance Metrics
- **API Response Time**: p95 < 200ms ✅
- **Download Throughput**: > 50MB/s per client ✅
- **Memory Usage**: < 2GB per instance ✅
- **CPU Utilization**: < 70% under normal load ✅

### Process Metrics
- **CI Build Time**: < 10 minutes ✅
- **PR Review Time**: < 24 hours ✅
- **Time to Fix Critical Bug**: < 4 hours ✅
- **Deployment Frequency**: Daily (or on-demand) ✅

---

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-4)
**Focus**: Architecture cleanup, type safety, testability  
**Goal**: Reduce technical debt, establish quality baseline

### Phase 2: Quality (Weeks 3-6)
**Focus**: Testing, tooling, documentation  
**Goal**: Achieve 60%+ test coverage, enforce quality gates

### Phase 3: Performance (Weeks 5-8)
**Focus**: Optimization, monitoring  
**Goal**: Improve throughput by 30%, reduce latency by 40%

### Phase 4: Operations (Weeks 7-10)
**Focus**: CI/CD, observability, automation  
**Goal**: Reduce manual operations, proactive monitoring

---

## Risk Mitigation

### High-Risk Changes
1. **Core module refactoring**: Use feature flags, gradual rollout
2. **Database migrations**: Test on staging, backup before production
3. **Async/await conversion**: Thorough testing, monitor for deadlocks

### Rollback Strategy
- Keep old code paths behind feature flags during transition
- Maintain backward compatibility for at least 2 releases
- Automated rollback in deployment pipeline if health checks fail

---

## Next Steps

### Week 1 Action Items
1. ✅ Create this improvement roadmap
2. Set up project tracking (GitHub Projects or similar)
3. Audit core modules and create consolidation plan
4. Run baseline metrics (test coverage, complexity, performance)
5. Set up branch protection rules and PR templates
6. 🆕 Review [GitHub Copilot Strategy](GITHUB_COPILOT_STRATEGY.md) guide
7. 🆕 Create `.copilot-context/` folder for session context

### Getting Started
```bash
# Install additional dev tools
pip install vulture radon complexity-report dependency-injector

# Set up Copilot context folders
mkdir -p .copilot-context/{templates,plans,sessions}

# Run initial audits
make lint
make type-check
pytest tests/ --cov=src --cov-report=html
radon cc src/ -a
vulture src/

# Create feature branch for first improvement
git checkout -b refactor/core-consolidation
```

### 🤖 Copilot First Session

After reviewing the strategy guide, start your first Copilot session:

```
Open GitHub Copilot Chat and paste:

"I'm starting a 10-week code improvement project for a Telegram bot.

Current state:
- 154 Python files in src/bot/core/ (architectural bloat)
- ~10% type coverage
- Test coverage unknown
- 82K LOC total

Week 1 goal: Audit and categorize modules

Files in src/bot/core/:
[paste: ls -1 src/bot/core/*.py | head -30]

Task: Analyze these files and suggest:
1. Domain categorization (download, storage, monitoring, api, security, task)
2. Merge candidates (files with similar responsibilities)
3. Priority order for consolidation

Provide a categorization table and consolidation plan."
```

**Save the output** to `.copilot-context/plans/week1-categorization.md`

---

## Resources & References

- **Architecture Patterns**: Clean Architecture, Hexagonal Architecture
- **Python Best Practices**: PEP 8, PEP 484 (Type Hints), PEP 585
- **Testing**: pytest docs, Testing Best Practices
- **Performance**: Python Performance Tips, Async Programming Guide
- **Monitoring**: Prometheus Best Practices, OpenTelemetry Documentation

---

**Document Version**: 1.0  
**Last Updated**: March 8, 2026  
**Owner**: Development Team  
**Review Cadence**: Bi-weekly

---

## Appendix: Tool Recommendations

### Code Quality
- `mypy` - Static type checking ✅ Already using
- `pylint` - Comprehensive linting ✅ Already using
- `black` - Code formatting ✅ Already using
- `isort` - Import sorting ✅ Already using
- `bandit` - Security linting ✅ Already using
- `vulture` - Dead code detection ⚠️ Add
- `radon` - Complexity metrics ⚠️ Add

### Testing
- `pytest` - Test framework ✅ Already using
- `pytest-cov` - Coverage reporting ✅ Already using
- `pytest-asyncio` - Async testing ✅ Already using
- `pytest-mock` - Mocking ✅ Already using
- `pytest-xdist` - Parallel testing ⚠️ Add
- `hypothesis` - Property-based testing ⚠️ Add

### Performance
- `locust` - Load testing ⚠️ Add
- `py-spy` - Profiling ⚠️ Add
- `memory_profiler` - Memory profiling ⚠️ Add
- `asyncio-debug` - Async debugging ⚠️ Add

### Dependency Management
- `pip-audit` - Security vulnerabilities ⚠️ Add
- `pipdeptree` - Dependency visualization ⚠️ Add
- `pip-tools` - Dependency compilation ⚠️ Consider
