# Implementation Checklist - Week by Week

**Purpose**: Track progress on code quality, architecture, and optimization improvements  
**Duration**: 10 weeks  
**Start Date**: March 8, 2026

---

## Week 1: Foundation & Assessment

### Goals
- Establish baselines
- Audit architecture
- Set up tracking
- Quick wins

### 🤖 GitHub Copilot Sessions (Week 1)

**Planned Sessions**: 5-6 focused chats  
**Total Time**: ~3-4 hours across the week  
**Strategy**: New chat for each major task

| Day | Session | Prompt Goal | Duration | New Chat? |
|-----|---------|-------------|----------|-----------|
| Mon | 1 | Module categorization | 30 min | ✅ Yes |
| Tue | 2 | Consolidation planning | 30 min | ✅ Yes |
| Wed | 3 | Implementation | 45 min | ✅ Yes |
| Thu | 4 | Type hints | 30 min | ✅ Yes |
| Fri | 5 | Test generation | 30 min | ✅ Yes |

**See**: [GITHUB_COPILOT_STRATEGY.md](GITHUB_COPILOT_STRATEGY.md#session-1-module-analysis) for exact prompts

### Tasks

#### Architecture Audit
  ```bash
  find src/bot/core -name "*.py" -exec wc -l {} + | sort -rn > core-audit.txt
  ```
  - [ ] Failover-related: `failover_manager.py`, `failover_cascade_detector.py`, etc.
  - [ ] Cache-related: `cache_manager.py`, `advanced_cache.py`, `file_cache_manager.py`
  - [ ] Dashboard-related: All `dashboard_*.py` files
  - [ ] Alert-related: `alert_manager.py`, `alert_manager_models.py`, etc.

**🤖 Copilot Prompt** (Session 1, Monday):
```
"I'm analyzing src/bot/core/ with 154 Python files needing consolidation.

Context:
- Telegram bot for file mirroring/leeching  
- Multiple manager classes with overlapping responsibilities

Files to categorize:
[paste: ls -1 src/bot/core/*.py]

Task: Categorize into domains:
1. Download management
2. Storage/caching
3. Monitoring/alerting  
4. API/web
5. Security
6. Task management

For each file: suggest domain + identify merge candidates."
```

#### Baseline Metrics
- [ ] Run complexity analysis
  ```bash
  pip install radon
  radon cc src/ -a -s > complexity-baseline.txt
  radon mi src/ > maintainability-baseline.txt
  ```
- [ ] Measure test coverage
  ```bash
  pytest tests/ --cov=src --cov-report=html --cov-report=term > coverage-baseline.txt
  ```
- [ ] Check dead code
  ```bash
  pip install vulture
  vulture src/ > dead-code-report.txt
  ```
- [ ] Document current state in tracking spreadsheet

#### Type Safety Audit
  ```bash
  make type-check-strict
  ```

**🤖 Copilot Prompt** (Can combine with implementation sessions):
```
"Check type coverage for this module:

File: src/bot/core/cache_manager.py

```python
[paste class signatures only - 30-40 lines]
```

Questions:
1. Which functions lack type hints?
2. What's the estimated type coverage %?
3. Show before/after for adding strict hints
4. List mypy --strict errors to expect"
```
#### Quick Wins
- [ ] Enable autoflake in pre-commit (remove unused imports)
- [ ] Add `.editorconfig` for consistent formatting
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] Create `.github/ISSUE_TEMPLATE/` for bugs and features
- [ ] Add `CODEOWNERS` file

**Deliverables**:
- Architecture audit document
- Baseline metrics report
- Prioritized consolidation plan
- 5 quick wins completed

---

## Week 2: Architecture Consolidation Phase 1

### Goals
- Consolidate storage/cache modules
- Consolidate failover modules
- Create domain directories

### 🤖 GitHub Copilot Sessions (Week 2)

**Focus**: Implementation-heavy week  
**Sessions**: 6-8 chats  
**Tip**: Keep implementation chats <30 min, start fresh for new modules

### Tasks

#### Domain Structure Setup
- [ ] Create domain directories
  ```bash
  mkdir -p src/bot/core/{download,storage,monitoring,api,security,task_management}
  touch src/bot/core/{download,storage,monitoring,api,security,task_management}/__init__.py
  ```

#### Storage/Cache Consolidation
- [ ] Analyze cache-related modules
  - [ ] `cache_manager.py` (main functionality)
  - [ ] `advanced_cache.py` (advanced features)
  - [ ] `file_cache_manager.py` (file-specific)
- [ ] Create unified `src/bot/core/storage/cache_system.py`
- [ ] Merge functionality, remove duplicates
- [ ] Add comprehensive docstrings
- [ ] Update all imports across codebase
- [ ] Add unit tests for consolidated module
- [ ] Deprecation warnings for old imports (if public API)

#### Failover Consolidation
- [ ] Analyze failover-related modules
  - [ ] `failover_manager.py`
  - [ ] `failover_cascade_detector.py`
  - [ ] `failover_recovery_executor.py`
  - [ ] `failover_models.py`
- [ ] Create unified `src/bot/core/monitoring/failover_system.py`
- [ ] Merge related functionality
- [ ] Update imports
- [ ] Test failover scenarios

#### Type Safety Expansion
- [ ] Add strict typing to consolidated storage module
- [ ] Add strict typing to consolidated failover module
- [ ] Fix any mypy errors

**Deliverables**:
- 2 major consolidations complete (~10-15 files → 2-3)
- All tests passing
- No import errors

---

## Week 3: Architecture Consolidation Phase 2 + Testing Infrastructure

### Goals
- Consolidate dashboard modules
- Consolidate alert modules
- Fix test collection issues
- Start dependency injection

### Tasks

#### Dashboard Consolidation
- [ ] Analyze dashboard modules
  - [ ] `dashboard_manager.py`
  - [ ] `dashboard_routes.py`
  - [ ] `dashboard_html.py`
  - [ ] `advanced_dashboard*.py` (4-5 files)
- [ ] Create `src/bot/core/api/dashboard/` package
- [ ] Reorganize into:
  - [ ] `manager.py` (core logic)
  - [ ] `routes.py` (FastAPI routes)
  - [ ] `templates.py` (HTML templates)
  - [ ] `websocket.py` (WebSocket handlers)
- [ ] Update all references

#### Alert Consolidation
- [ ] Merge alert-related modules
  - [ ] `alert_manager.py`
  - [ ] `alert_manager_models.py`
  - [ ] `command_alert_system.py`
- [ ] Create `src/bot/core/monitoring/alerts.py`
- [ ] Update imports

#### Test Infrastructure
- [ ] Fix pytest collection issues
  ```bash
  pytest tests/ --collect-only 2>&1 | grep -i error
  ```
- [ ] Add missing `__init__.py` files
- [ ] Fix circular imports
- [ ] Ensure all tests can be discovered
- [ ] Run full test suite successfully
  ```bash
  pytest tests/ -v
  ```

#### Dependency Injection Setup
- [ ] Install `dependency-injector`
  ```bash
  pip install dependency-injector
  ```
- [ ] Create `src/bot/core/di_container.py`
- [ ] Refactor 2-3 managers to use DI
- [ ] Update initialization code

**Deliverables**:
- 2 more major consolidations (~10 files → 2-3)
- All tests discoverable and passing
- DI container skeleton in place

---

## Week 4: Testing & Coverage

### Goals
- Achieve 40% test coverage
- Add tests for consolidated modules
- Set up coverage reporting

### 🤖 GitHub Copilot Sessions (Week 4)

**Focus**: Test generation - Copilot excels at this!  
**Sessions**: 4-6 chats (1 per module)  
**Tip**: Include the code to test in prompt for better context

### Tasks

#### Unit Tests for Core Managers
- [ ] Write tests for `storage/cache_system.py`

  **🤖 Copilot Prompt** (New chat - excellent for test generation):
  ```
  "Generate comprehensive pytest tests for this CacheManager:

  ```python
  class CacheManager:
    async def get(self, key: str) -> Optional[Any]:
      # L1→L2→L3 fallback logic
      [paste key implementation - 20-30 lines]
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
      # Write to all levels
      [paste implementation]
  ```

  Requirements:
  - pytest + pytest-asyncio
  - Mock Redis and disk I/O
  - Test: L1/L2/L3 hits, misses, promotions, TTL, errors
  - Target: >80% coverage
  - Include fixtures for mocks

  Generate: tests/unit/test_cache_system.py"
  ```
  - [ ] Test get/set operations
  - [ ] Test cache eviction
  - [ ] Test hierarchical cache fallback
  - [ ] Target: >80% coverage
- [ ] Write tests for `monitoring/failover_system.py`
  - [ ] Test failover detection
  - [ ] Test recovery execution
  - [ ] Test cascade prevention
- [ ] Write tests for `monitoring/alerts.py`
  - [ ] Test alert creation
  - [ ] Test severity handling
  - [ ] Test notification dispatch
- [ ] Write tests for `api/dashboard/`
  - [ ] Test route handlers
  - [ ] Test WebSocket connections
  - [ ] Test metrics collection

#### Integration Tests
- [ ] Test download → cache → upload pipeline
- [ ] Test failover scenarios with mocked services
- [ ] Test API endpoints end-to-end

#### Coverage Configuration
- [ ] Set up coverage thresholds in pytest.ini
  ```ini
  [tool:pytest]
  addopts = --cov=src --cov-report=html --cov-report=term --cov-fail-under=40
  ```
- [ ] Add coverage badge to README
- [ ] Configure CI to enforce coverage

**Deliverables**:
- 40%+ test coverage
- Coverage reports in CI
- Tests for all consolidated modules

---

## Week 5: Type Safety & Async Optimization

### Goals
- Expand strict typing to 20+ modules
- Identify and fix blocking I/O
- Add async context managers

### Tasks

#### Type Safety Expansion
- [ ] Add strict typing to 10 more modules
  ```toml
  [[tool.mypy.overrides]]
  module = [
      "src.bot.core.storage.*",
      "src.bot.core.monitoring.*",
      "src.bot.core.security.rate_limiter",
      "src.bot.core.task_management.task_coordinator",
      # ... 6 more
  ]
  **🤖 Copilot Prompt** (Session 1, Tuesday):
  ```
  "Design unified cache system from these modules:

  1. cache_manager.py (500 lines) - Basic get/set
  2. advanced_cache.py (800 lines) - Advanced features  
  3. file_cache_manager.py (300 lines) - File-specific

  Goals:
  - Unified API covering all functionality
  - Hierarchical caching (L1: memory, L2: Redis, L3: disk)
  - Backward compatible imports
  - Type hints (Python 3.11+)
  - Async/await

  Provide:
  1. Class structure outline
  2. Public API methods
  3. Migration strategy for existing code"
  ```

  strict = true
  ```
  **🤖 Copilot Prompt** (Session 2, Wednesday - Implementation):
  ```
  "Implement the CacheManager class based on this design:

  [paste design from previous chat]

  Requirements:
  - Implement get() method with L1→L2→L3 fallback
  - Implement set() method writing to all levels
  - Add eviction policies (LRU for L1)
  - Include type hints
  - Add docstrings

  Show implementation for core methods (get, set, delete, clear)."
  ```

  **💡 Token-saving tip**: Implement 2-3 methods per chat, not entire class at once

- [ ] Fix all revealed type errors

**🤖 Copilot Prompt** (After implementation):
```
"Add strict type hints to this new module:

File: src/bot/core/storage/cache_system.py

Current code (relevant sections):
```python
[paste 50-80 lines - focus on public API]
```

Requirements:
- Pass mypy --strict
- Use Protocol for cache backend interface
- Document complex return types
- Add TypedDict for configuration

Show updated code with full type annotations."
```
- [ ] Add type hints to helper utilities
- [ ] Create Protocol definitions for third-party APIs

#### Async/Await Audit
- [ ] Find all blocking operations
  ```bash
  grep -r "requests\." src/ --include="*.py" | tee blocking-io.txt
  grep -r "open(" src/ --include="*.py" | grep -v "aiofiles" | tee -a blocking-io.txt
  grep -r "time\.sleep" src/ --include="*.py" | tee -a blocking-io.txt
  ```
- [ ] Replace `requests` with `httpx` async
  ```bash
  pip install httpx
  # Update imports: requests → httpx.AsyncClient
  ```
- [ ] Replace file I/O with `aiofiles`
- [ ] Replace `time.sleep()` with `asyncio.sleep()`

#### Async Context Managers
- [ ] Add `__aenter__` / `__aexit__` to managers
  ```python
  class DownloadManager:
      async def __aenter__(self):
          await self.initialize()
          return self
      
      async def __aexit__(self, *args):
          await self.cleanup()
  ```
- [ ] Use context managers in calling code

**Deliverables**:
- 40%+ of codebase strictly typed
- All blocking I/O identified and prioritized
- 30-50% of blocking ops converted to async

---

## Week 6: Performance Optimization

### Goals
- Implement hierarchical caching
- Add connection pooling
- Set up performance monitoring

### Tasks

#### Cache Optimization
- [ ] Implement cache hierarchy (L1/L2/L3)
  ```python
  class HierarchicalCache:
      def __init__(self):
          self.l1_cache = LRUCache(maxsize=1000)  # Memory
          self.l2_cache = RedisCache()            # Redis
          self.l3_cache = DiskCache()             # Disk
  ```
- [ ] Measure cache hit rates
- [ ] Implement cache warming for common queries
- [ ] Add cache metrics to Prometheus

#### Connection Pooling
- [ ] Configure HTTP client pool sizes
  ```python
  httpx.AsyncClient(
      limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
  )
  ```
- [ ] Optimize Redis connection pool
- [ ] Add database connection pooling (if applicable)

#### Performance Monitoring
- [ ] Add custom Prometheus metrics
  ```python
  from prometheus_client import Counter, Histogram, Gauge
  
  downloads_total = Counter('mltb_downloads_total', 'Total downloads', ['source', 'status'])
  download_duration = Histogram('mltb_download_duration_seconds', 'Download time')
  active_downloads = Gauge('mltb_active_downloads', 'Currently active downloads')
  ```
- [ ] Set up Grafana dashboards
- [ ] Configure alerting rules

#### Performance Baseline
- [ ] Install profiling tools
  ```bash
  pip install py-spy memory_profiler locust
  ```
- [ ] Profile critical paths
  ```bash
  py-spy record -o profile.svg -- python src/bot/__main__.py
  ```
- [ ] Run load tests with locust
- [ ] Document baseline performance metrics

**Deliverables**:
- Hierarchical cache implemented
- 20-30% reduction in external API calls
- Performance metrics tracking in Prometheus

---

## Week 7: Code Quality & Security

### Goals
- Enhanced linting and static analysis
- Security hardening
- Database query optimization

### Tasks

#### Enhanced Linting
- [ ] Add complexity limits to pylintrc
  ```ini
  [DESIGN]
  max-complexity = 10
  max-args = 5
  max-locals = 15
  ```
- [ ] Add flake8 plugins
  ```bash
  pip install flake8-comprehensions flake8-builtins flake8-simplify
  ```
- [ ] Enable docstring enforcement
- [ ] Run radon complexity reports in CI

#### Security Hardening
- [ ] Run security scans
  ```bash
  pip install pip-audit safety
  pip-audit
  safety check
  bandit -r src/ -ll
  ```
- [ ] Fix identified vulnerabilities
- [ ] Add security scanning to CI
- [ ] Review and rotate secrets
- [ ] Audit input validation

#### Database Optimization
- [ ] Enable slow query logging
- [ ] Identify N+1 query patterns
- [ ] Add database indexes
  - [ ] Index frequently queried fields
  - [ ] Create composite indexes
- [ ] Implement query result caching
- [ ] Measure query performance improvement

**Deliverables**:
- No high-severity security issues
- Complexity <10 average
- 40-60% reduction in slow queries

---

## Week 8: Documentation & Observability

### Goals
- Comprehensive documentation
- Enhanced monitoring and tracing
- CI/CD improvements

### Tasks

#### Documentation
- [ ] Add/update docstrings (Google style) for all public APIs
- [ ] Generate API documentation
  ```bash
  pip install mkdocs mkdocs-material
  mkdocs build
  ```
- [ ] Create architecture diagrams
  - [ ] System architecture
  - [ ] Data flow diagrams
  - [ ] Deployment architecture
- [ ] Write Architecture Decision Records (ADRs)
  - [ ] Decision to consolidate core modules
  - [ ] Choice of DI framework
  - [ ] Async/await migration strategy
- [ ] Update README with new structure

#### Distributed Tracing
- [ ] Add OpenTelemetry spans to critical paths
  ```python
  from opentelemetry import trace
  
  tracer = trace.get_tracer(__name__)
  
  with tracer.start_as_current_span("download_file"):
      # download logic
  ```
- [ ] Configure trace sampling
- [ ] Set up Jaeger/Zipkin for trace visualization
- [ ] Add trace context propagation

#### Enhanced Monitoring
- [ ] Implement custom business metrics
- [ ] Set up log aggregation
- [ ] Create alerting rules
  ```yaml
  - alert: HighErrorRate
    expr: rate(http_errors_total[5m]) > 0.05
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes > 2e9
  ```
- [ ] Test incident response procedures

#### CI/CD Improvements
- [ ] Add parallel test execution
  ```yaml
  strategy:
    matrix:
      test-suite: [unit, integration, performance]
  ```
- [ ] Set up automated dependency updates (Dependabot)
- [ ] Add PR quality gates
- [ ] Configure automated releases

**Deliverables**:
- Complete API documentation
- Distributed tracing operational
- Enhanced CI pipeline

---

## Week 9: Testing Excellence

### Goals
- Achieve 60%+ test coverage
- Add performance regression tests
- Implement property-based testing

### Tasks

#### Expand Test Coverage
- [ ] Add tests for all download handlers
  - [ ] Aria2 handler
  - [ ] qBittorrent handler
  - [ ] SABnzbd handler
  - [ ] yt-dlp handler
- [ ] Add tests for all upload handlers
  - [ ] Google Drive upload
  - [ ] Rclone upload
  - [ ] Telegram upload
- [ ] Add tests for security components
  - [ ] Rate limiting
  - [ ] Input validation
  - [ ] Authentication
- [ ] Add tests for task management
  - [ ] Celery task routing
  - [ ] Queue management
  - [ ] Priority handling

#### Performance Testing
- [ ] Create load test scenarios
  ```python
  # tests/performance/locustfile.py
  from locust import HttpUser, task, between
  
  class BotUser(HttpUser):
      wait_time = between(1, 3)
      
      @task
      def download_file(self):
          self.client.post("/api/v1/download", json={...})
  ```
- [ ] Set up continuous benchmarking
- [ ] Configure performance regression alerts
- [ ] Document performance characteristics

#### Property-Based Testing
- [ ] Install hypothesis
  ```bash
  pip install hypothesis
  ```
- [ ] Add property tests for validators
  ```python
  from hypothesis import given
  from hypothesis import strategies as st
  
  @given(st.text())
  def test_url_validator(url):
      # Property: validator never crashes
      result = validate_url(url)
      assert isinstance(result, bool)
  ```
- [ ] Add property tests for data transformations

**Deliverables**:
- 60-70% test coverage
- Performance regression testing in CI
- Property-based tests for critical functions

---

## Week 10: Polish & Optimization

### Goals
- Final consolidation pass
- Performance tuning
- Documentation review
- Retrospective

### Tasks

#### Final Consolidation
- [ ] Review remaining core modules
- [ ] Identify any remaining merge opportunities
- [ ] Clean up any TODOs and FIXMEs
- [ ] Remove dead code (use vulture)
- [ ] Final refactoring pass

#### Performance Tuning
- [ ] Review profiling results
- [ ] Optimize hotspots
- [ ] Tune cache sizes
- [ ] Optimize database queries
- [ ] Test under load
- [ ] Document performance improvements

#### Final Testing
- [ ] Full regression test suite
- [ ] Load testing in staging
- [ ] Security audit
- [ ] Deployment dry-run

#### Documentation Review
- [ ] Review and update all documentation
- [ ] Update architecture diagrams
- [ ] Write migration guide (if needed)
- [ ] Create deployment checklist
- [ ] Write operations runbook

#### Retrospective
- [ ] Document what worked well
- [ ] Document challenges faced
- [ ] Measure improvements against baseline
  - [ ] Core module count: 154 → ___
  - [ ] Test coverage: ___% → ___%
  - [ ] Type coverage: ___% → ___%
  - [ ] Average complexity: ___ → ___
- [ ] Create maintenance plan
- [ ] Plan next improvement phase

**Deliverables**:
- All objectives met or documented
- Performance improvements verified
- Complete documentation
- Retrospective document

---

## Success Criteria Checklist

### Architecture
- [ ] Core modules reduced from 154 to <70
- [ ] Clean domain-based structure
- [ ] No duplicate functionality
- [ ] Clear separation of concerns

### Type Safety
- [ ] 80%+ of public APIs type-hinted
- [ ] 20+ modules with strict typing
- [ ] No critical mypy errors
- [ ] Type stubs for third-party libraries

### Testing
- [ ] 60%+ overall test coverage
- [ ] 80%+ coverage for core modules
- [ ] All tests passing in CI
- [ ] Performance regression tests

### Performance
- [ ] 30%+ improvement in concurrent operations
- [ ] 40%+ reduction in API response time
- [ ] Cache hit rate >70%
- [ ] No memory leaks

### Quality
- [ ] Average cyclomatic complexity <10
- [ ] No high-severity security issues
- [ ] All linting rules passing
- [ ] Documentation complete

### Operations
- [ ] CI build time <10 minutes
- [ ] Monitoring and alerting operational
- [ ] Deployment process documented
- [ ] Incident response runbook complete

---

## Weekly Review Template

**Week #**: ___  
**Date**: ___

### Completed Tasks
- Task 1
- Task 2
- ...

### Blockers/Issues
- Issue 1
- Issue 2
- ...

### Metrics Update
| Metric | Last Week | This Week | Target |
|--------|-----------|-----------|--------|
| Core modules | | | <70 |
| Test coverage | | | 60% |
| Type coverage | | | 80% |
| Complexity | | | <10 |

### Next Week Focus
- Priority 1
- Priority 2
- ...

### Notes
---

## Ongoing Maintenance (After Week 10)

### Weekly
- [ ] Review and merge dependency updates
- [ ] Check for security vulnerabilities
- [ ] Review CI failures
- [ ] Monitor performance metrics

### Monthly
- [ ] Review and update documentation
- [ ] Check test coverage trends
- [ ] Review complexity metrics
- [ ] Team retrospective

### Quarterly
- [ ] Major dependency upgrades
- [ ] Architecture review
- [ ] Performance optimization pass
- [ ] Security audit

---

**Remember**: This is a living document. Adjust timeline and priorities as needed based on team capacity and business requirements.

---

## 🤖 GitHub Copilot Integration Summary

### Chat Session Best Practices

**When to Start New Chat**:
- ✅ New module/domain (e.g., cache → failover systems)
- ✅ Different task type (implementation → testing → documentation)  
- ✅ After 30+ minutes in same chat
- ✅ When responses become generic
- ❌ For follow-up questions on same topic
- ❌ When iterating on same code section

### Token Management Tips

1. **Paste smartly**: 50-100 lines max per prompt
2. **Use diffs**: For large files, show only changes needed
3. **Reference, don't repeat**: "As discussed earlier..." instead of re-pasting
4. **Break tasks**: Large refactoring → multiple focused chats
5. **Save context**: Document decisions in `.copilot-context/` folder

### Weekly Copilot Usage Pattern

```
Week 1-2: Architecture & Planning
  → 5-7 chats per week
  → Design-heavy prompts
  → Save outputs as context for implementation

Week 3-4: Implementation  
  → 8-12 chats per week
  → Code generation prompts
  → Follow-up chats for fixes

Week 5-6: Testing & Documentation
  → 6-8 chats per week  
  → Test generation (Copilot is excellent here!)
  → Docstring generation

Week 7-10: Optimization & Polish
  → 4-6 chats per week
  → Performance analysis
  → Code review assistance
```

### Prompt Templates Quick Reference

Copy these to `.copilot-context/templates/` for reuse:

**Module Refactoring**:
```
"Refactor [CLASS] in [FILE]:
```python
[PASTE CODE]
```
Goals: [LIST]
Requirements: [TYPE HINTS, ASYNC, ETC]
Provide: [EXPECTED OUTPUT]"
```

**Type Hints**:
```
"Add strict type hints to:
```python
[PASTE SIGNATURES]
```
Pass mypy --strict
Show before/after diff"
```

**Test Generation**:
```
"Generate pytest tests:
```python
[PASTE CODE TO TEST]
```
Requirements: [COVERAGE, MOCKS]
Generate: [TEST FILE PATH]"
```

**See full guide**: [GITHUB_COPILOT_STRATEGY.md](GITHUB_COPILOT_STRATEGY.md)

---

**Good luck with your improvements! 🚀🤖**
