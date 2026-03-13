# Quick Reference: Priority Improvements

**TL;DR**: Focus on architecture consolidation → type safety → testing → performance

---

## 🔴 Critical (Do First - Week 1-2)

### 1. Fix Architectural Bloat
**Problem**: 154 files in `src/bot/core/` - too many managers  
**Solution**: Consolidate into domain-based structure  
**Impact**: 🎯 Maintenance -60%, Navigation +60%

**🤖 GitHub Copilot Prompt**:
```
Open new chat and paste:

"I'm analyzing src/bot/core/ with 154 Python files that need consolidation.

Context:
- Telegram bot for file mirroring/leeching
- Multiple manager classes with overlapping responsibilities
- Need domain-based organization

Task: Categorize these files into domains:
1. Download management
2. Storage/caching  
3. Monitoring/alerting
4. API/web
5. Security
6. Task management

Files: [paste output of: ls src/bot/core/*.py]

For each, suggest domain and identify merge candidates."
```

```bash
# Action: Audit and categorize modules
cd src/bot/core
ls -la | wc -l  # Currently 154+

# Target structure:
src/bot/core/
  ├── download/       # ~10 files
  ├── storage/        # ~8 files
  ├── monitoring/     # ~12 files
  ├── api/           # ~15 files
  ├── security/      # ~8 files
  └── task_management/ # ~10 files
```

**Start Now**:
```bash
# 1. Create domain directories
mkdir -p src/bot/core/{download,storage,monitoring,api,security,task_management}

# 2. Identify merge candidates
grep -l "Failover" src/bot/core/*.py  # Merge these
grep -l "Cache" src/bot/core/*.py     # Consolidate caching
grep -l "Dashboard" src/bot/core/*.py # Group dashboard code
```

---

### 2. Expand Type Safety
**Problem**: Only 5 modules strictly typed  
**Solution**: Add 15-20 more core modules to strict typing  
**Impact**: 🎯 Bugs -30%, IDE support +100%

```bash
# Quick win: Add type hints to function signatures
make type-check  # See current errors

# Add to pyproject.toml:
[[tool.mypy.overrides]]
module = [
    "src.bot.core.cache_manager",
    "src.bot.core.alert_manager",
    "src.bot.core.batch_processor",
    "src.bot.helper.ext_utils.bot_utils",
]
strict = true
```

**Start Now**:
```bash
# Pick one file, make it strictly typed:
mypy --strict src/bot/core/alert_manager.py
# Fix revealed issues, commit

# Repeat for other core managers
```

**🤖 GitHub Copilot Prompt**:
```
New chat for each module:

"Add strict type hints to this Python module:

File: src/bot/core/alert_manager.py

```python
[paste AlertManager class - 50-80 lines]
```

Requirements:
- Python 3.11+ type syntax
- Pass mypy --strict
- Use typing.Protocol for interfaces
- Document complex types with comments
- Show before/after diff

Current mypy errors:
[paste errors if any]"
```

**💡 Copilot Tips**:
- Paste only class signature first, iterate on methods
- Include mypy errors to guide fixes
- Ask for explanations of complex types
- Request migration guide for type changes

---

### 3. Fix Test Collection
**Problem**: `make ci-test` has collection issues  
**Solution**: Fix imports and missing __init__.py  
**Impact**: 🎯 Enable proper CI/CD

```bash
# Identify broken tests
pytest tests/ --collect-only 2>&1 | grep -i error

# Common fixes:
find tests/ -type d -exec touch {}/__init__.py \;
```

**Start Now**:
```bash
pytest tests/ --collect-only  # Check output
pytest tests/unit/ -v          # Run unit tests
pytest tests/integration/ -v   # Run integration tests
```

---

## 🟡 High Priority (Week 2-4)

### 4. Add Test Coverage
**Target**: 60% minimum coverage  
**Current**: Unknown (need baseline)

```bash
# Get baseline
pytest tests/ --cov=src --cov-report=term --cov-report=html
firefox htmlcov/index.html  # View coverage report

# Focus areas (priority order):
# 1. Core managers (cache, alert, task)
# 2. Download handlers (aria2, qbittorrent)
# 3. Upload handlers (gdrive, rclone)
# 4. Security (rate limiting, validation)
```

**🤖 GitHub Copilot Prompt**:
```
New chat per module:

"Generate comprehensive pytest tests:

Class to test:
```python
class CacheManager:
    async def get(self, key: str) -> Optional[Any]:
        '''Retrieve from L1 → L2 → L3 cache'''
        [paste implementation]
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        '''Store in all cache levels'''
        [paste implementation]
```

Requirements:
- pytest + pytest-asyncio
- Mock Redis and disk I/O  
- Test cache hierarchy fallback
- Test TTL expiration
- Test error handling
- Target: >80% coverage
- Include fixtures for common setup

Generate: tests/unit/test_cache_system.py"
```

**Batch Testing Strategy**:
- 1 Copilot chat per module (keep focused)
- Generate 3-5 test classes per chat
- Review and run tests before next module
- Iterate in same chat for fixes

---

### 5. Implement Dependency Injection
**Why**: Easier testing, better modularity  
**How**: Use dependency-injector or manual DI

```python
# Before (hard to test):
class AlertManager:
    def __init__(self):
        self.logger = LOGGER  # Global!
        self.config = Config()  # Direct instantiation

# After (testable):
class AlertManager:
    def __init__(self, logger: LoggerManager, config: Config):
        self.logger = logger
        self.config = config

# In tests:
def test_alert_manager():
    mock_logger = Mock(spec=LoggerManager)
    mock_config = Mock(spec=Config)
    manager = AlertManager(mock_logger, mock_config)
    # Easy to test!
```

---

### 6. Async/Await Audit
**Find blocking operations**:

```bash
# Find sync I/O that should be async
grep -r "requests\." src/ --include="*.py"
grep -r "^import requests" src/ --include="*.py"
grep -r "open(" src/ --include="*.py" | grep -v "aiofiles"

# Replace with:
# requests → httpx async
# open() → aiofiles.open()
# time.sleep() → asyncio.sleep()
```

**🤖 GitHub Copilot Prompt**:
```
New chat:

"Audit this module for blocking I/O:

File: src/bot/helper/ext_utils/download_utils.py

```python
[paste 50-100 lines of relevant code]
```

Find:
1. Synchronous I/O (requests, open(), time.sleep)
2. Missing async/await
3. Blocking database calls

For each issue show:
- Line number
- Current code
- Async replacement
- Required imports"
```

**Follow-up in same chat**:
```
"Convert this function to async:

```python
[paste specific function]
```

Requirements:
- Use httpx for HTTP
- Use aiofiles for files
- Add type hints
- Include error handling
- Generate corresponding unit test"
```

---

## 🟢 Medium Priority (Week 4-6)

### 7. Enhanced Monitoring
```python
# Add custom metrics
from prometheus_client import Counter, Histogram

downloads_total = Counter(
    'mltb_downloads_total',
    'Total downloads',
    ['source', 'status']
)

download_size_bytes = Histogram(
    'mltb_download_size_bytes',
    'Download size distribution'
)

# Use in code:
downloads_total.labels(source='aria2', status='success').inc()
download_size_bytes.observe(file_size)
```

---

### 8. Security Hardening
```bash
# Run security audit
pip install pip-audit safety
pip-audit
safety check

# Add to CI:
bandit -r src/ -f json -o security-report.json
```

---

### 9. Performance Baseline
```bash
# Install profiling tools
pip install py-spy memory_profiler locust

# Profile critical paths
py-spy record -o profile.svg -- python src/bot/__main__.py

# Memory profiling
python -m memory_profiler src/bot/core/cache_manager.py

# Load testing
locust -f tests/performance/locustfile.py
```

---

## 🔵 Lower Priority (Week 6-10)

### 10. Documentation
- Add docstrings (Google style)
- Generate API docs with Sphinx/MkDocs
- Create architecture diagrams
- Document deployment runbooks

### 11. CI/CD Enhancements
- Parallel test execution
- Automated dependency updates (Dependabot)
- Performance regression testing
- Automated releases

### 12. Code Quality Gates
- Complexity limits (cyclomatic < 10)
- Coverage enforcement (>60%)
- Type coverage tracking
- Security vulnerability scanning

---

## 📊 Success Metrics

| Metric | Current | Target (4 weeks) | Target (10 weeks) |
|--------|---------|------------------|-------------------|
| Core modules | 154 | 100 | 60-70 |
| Type coverage | ~10% | 40% | 80% |
| Test coverage | ??? | 40% | 60-70% |
| CI build time | ??? | <8 min | <5 min |
| Cyclomatic complexity | ??? | <12 avg | <10 avg |

---

## 🚀 Quick Start Commands

```bash
# Week 1 Setup
pip install vulture radon pytest-cov

# Run audits
make lint                           # Existing linting
radon cc src/ -a -s                # Complexity report
vulture src/                       # Find dead code
pytest tests/ --cov=src --cov-report=html  # Coverage

# Start refactoring
git checkout -b refactor/core-consolidation
mkdir -p src/bot/core/{download,storage,monitoring,api,security,task_management}

# Pick first merge target
git mv src/bot/core/cache_manager.py src/bot/core/storage/
git mv src/bot/core/advanced_cache.py src/bot/core/storage/
# Merge duplicates, update imports, test
```

---

## 📋 Daily Checklist (During Refactor Period)

- [ ] Run `make ci-check` before committing
- [ ] Ensure tests pass: `pytest tests/`
- [ ] Check type safety: `make type-check`
- [ ] Run security scan: `bandit -r src/bot/core/`
- [ ] Update documentation for changed modules
- [ ] Create PR with clear description of changes

---

## ⚠️ Common Pitfalls to Avoid

1. **Don't** refactor everything at once - do incremental changes
2. **Don't** break backward compatibility without deprecation warnings
3. **Don't** merge PRs without reviewing test coverage impact
4. **Don't** skip type hints on new code
5. **Don't** forget to update documentation

---

## 🎯 This Week's Focus (Week 1)

```bash
# Monday: Audit
bash -c 'cd src/bot/core && ls -1 *.py | head -20'  # Review first 20 files
radon cc src/bot/core/ -a -s | head -30              # Complexity report

# Tuesday-Wednesday: Consolidate 
# Pick one domain (e.g., caching), merge related files

# Thursday: Type Safety
# Add strict typing to 2-3 newly consolidated modules

# Friday: Testing
# Fix test collection issues, add tests for refactored code
pytest tests/ --cov=src/bot/core/storage --cov-report=term
```

---

## 📞 Need Help?

- Review detailed plan: [IMPROVEMENT_ROADMAP.md](IMPROVEMENT_ROADMAP.md)
- Check existing docs: [docs/](../docs/)
- Run make help for available commands

**Remember**: Perfect is the enemy of done. Ship incremental improvements!
