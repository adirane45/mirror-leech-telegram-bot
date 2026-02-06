# CodeScene Integration - Quick Reference

## 🚀 Getting Started

### One-Time Setup

```bash
# The analysis tools are already installed!
# They run without needing a CodeScene account or token

# Just run the analysis:
bash scripts/codescene_analyze.sh full
```

### Running Analysis

```bash
# Full analysis (recommended)
bash scripts/codescene_analyze.sh full

# Quick complexity check (30 seconds)
bash scripts/codescene_analyze.sh quick

# Hotspot analysis only (change patterns)
bash scripts/codescene_analyze.sh hotspots
```

---

## 📊 Understanding Your Reports

### Reports Location
All reports saved in: `.codescene/reports/`

```bash
# View latest reports
ls -lh .codescene/reports/

# Check complexity summary
cat .codescene/reports/complexity_*.json | grep -A5 summary

# Check code health
cat .codescene/reports/health_*.json | grep health_score

# Check technical debt
cat .codescene/reports/tech_debt_*.json | grep total_hours
```

---

## 🎯 Current Status (Feb 6, 2026)

| Metric | Value | Target |
|--------|-------|--------|
| Code Health Score | 58.37/100 | 75+ |
| Documentation | 21% | 80% |
| High Complexity Functions | 13 | <3 |
| Technical Debt | 224 hours | <50h |
| Bare Excepts | 100 | 0 |

---

## 🔥 Top 5 Issues to Fix NOW

### 1. Refactor `direct_link_generator()` (Complexity: 43)
**File:** `bot/helper/mirror_leech_utils/download_utils/direct_link_generator.py:27`

**Problem:** One massive function handles all download providers

**Solution:**
```python
# Before: One giant function
def direct_link_generator(link):
    if 'mediafire' in link:
        # 50 lines of mediafire logic
    elif 'gofile' in link:
        # 40 lines of gofile logic
    # ... 300 more lines

# After: Provider pattern
PROVIDERS = {
    'mediafire': MediaFireProvider(),
    'gofile': GoFileProvider(),
    'linkbox': LinkBoxProvider(),
}

def direct_link_generator(link):
    provider = detect_provider(link)
    return PROVIDERS[provider].generate_link(link)
```

**Time:** 4-6 hours  
**Impact:** Reduces complexity from 43 → ~5 per function

---

### 2. Split `bot/helper/ext_utils/bot_utils.py` (1,254 complexity, 160 changes)
**Problem:** God file with everything

**Solution:**
```bash
# Split into focused modules:
bot_utils.py → 
  - argument_parser.py (args handling)
  - formatters.py (size, time, speed formatting)  
  - validators.py (input validation)
  - converters.py (unit conversions)
```

**Time:** 6-8 hours  
**Impact:** Reduces hotspot score by 90%, easier maintenance

---

### 3. Fix Bare Except Clauses (100 occurrences)
**Problem:** Catches all exceptions, masks errors

**Bad:**
```python
try:
    await download_file(url)
except:  # ❌ Catches EVERYTHING
    pass
```

**Good:**
```python
try:
    await download_file(url)
except (aiohttp.ClientError, asyncio.TimeoutError) as e:
    logger.error(f"Download failed: {e}")
    raise DownloadError(f"Failed to download {url}") from e
```

**Time:** 1-2 hours  
**Impact:** Prevents mysterious failures, improves debugging

---

### 4. Add Docstrings to Phase 4 Modules
**Problem:** 0% documentation in new code

**Solution:**
```python
# Add to every public function:
async def enable(self, max_size_mb: int = 100) -> bool:
    """
    Enable the cache manager with specified size limit.
    
    Args:
        max_size_mb: Maximum cache size in megabytes (default: 100)
        
    Returns:
        bool: True if enabled successfully, False otherwise
        
    Example:
        >>> cache = CacheManager.get_instance()
        >>> await cache.enable(max_size_mb=200)
        True
    """
```

**Files to document:**
- `bot/core/query_optimizer.py`
- `bot/core/cache_manager.py`
- `bot/core/rate_limiter.py`
- `bot/core/batch_processor.py`
- `bot/core/load_balancer.py`
- `bot/core/connection_pool_manager.py`

**Time:** 2-3 hours  
**Impact:** Improves documentation from 21% → 35%

---

### 5. Refactor God Objects
**Problem:** Classes with 20+ methods doing too much

**Target:**
- `RedisManager` (21 methods) → Split into:
  - `RedisCacheService`
  - `RedisQueueService`
  - `RedisLockService`

- `DbManager` (22 methods) → Split into:
  - `UserRepository`
  - `SettingsRepository`
  - `StatsRepository`

**Pattern: Repository Pattern**
```python
# Before
class DbManager:
    def get_user(self, user_id): ...
    def save_user(self, user): ...
    def get_settings(self, user_id): ...
    def save_settings(self, settings): ...
    # ... 18 more methods

# After  
class UserRepository:
    def get(self, user_id): ...
    def save(self, user): ...
    def delete(self, user_id): ...

class SettingsRepository:
    def get(self, user_id): ...
    def save(self, user_id, settings): ...
```

**Time:** 4-6 hours each  
**Impact:** Better testability, clearer responsibilities

---

## 📋 Quick Fix Checklist

Copy and track your progress:

```markdown
## Week 1: Documentation & Quick Wins
- [ ] Add docstrings to Phase 4 modules (2h)
- [ ] Fix 20 bare except clauses (1h)
- [ ] Add type hints to Phase 4 public APIs (1h)
- [ ] Document `direct_link_generator.py` functions (1h)

## Week 2: Complexity Reduction
- [ ] Refactor `direct_link_generator()` (6h)
- [ ] Extract `mediafireFolder()` to module (4h)
- [ ] Simplify `linkBox()` (3h)
- [ ] Split `arg_parser()` into stages (2h)

## Week 3: Hotspot Files
- [ ] Split `bot_utils.py` (8h)
- [ ] Split `common.py` (8h)
- [ ] Modularize `status_utils.py` (6h)

## Week 4: God Objects
- [ ] Refactor `RedisManager` (6h)
- [ ] Refactor `DbManager` (6h)
- [ ] Extract job functions (4h)
```

---

## 🔄 Tracking Improvements

### After Each Refactoring Session

```bash
# 1. Run analysis
bash scripts/codescene_analyze.sh full

# 2. Compare metrics
echo "Previous health score: 58.37"
cat .codescene/reports/health_*.json | grep health_score

# 3. Check complexity improvements
python3 scripts/analyze_complexity.py 2>&1 | grep "High Complexity Functions:"

# 4. Commit with metrics
git commit -m "refactor: Split direct_link_generator

- Reduced complexity from 43 to 5 per provider
- Added docstrings (40% coverage)
- Fixed 15 bare except clauses

CodeScene metrics:
- Health score: 58.37 → 62.5 (+4.13)
- High complexity functions: 13 → 10 (-3)
"
```

---

## 💡 Pro Tips

### 1. Focus on Hotspots First
Files that change frequently get the biggest ROI:
```bash
# See what's changing most
python3 scripts/analyze_hotspots.py 2>&1 | head -30
```

### 2. Use Feature Branches
```bash
# One refactoring per branch
git checkout -b refactor/split-bot-utils
# ... refactor ...
bash scripts/codescene_analyze.sh full
# ... verify improvement ...
git commit -m "refactor: Split bot_utils.py"
```

### 3. Write Tests First
Before refactoring:
```bash
# Ensure existing behavior covered
pytest tests/ -v --cov=bot

# Then refactor confidently
# Tests catch any regressions
```

### 4. Refactor in Small Steps
```python
# Don't refactor everything at once!
# Step 1: Extract function
# Step 2: Add tests  
# Step 3: Run analysis
# Step 4: Commit
# Repeat
```

---

## 🎯 Success Criteria

You'll know you're succeeding when:

### Short Term (1 Month)
- ✅ Code health score > 65
- ✅ Documentation > 40%
- ✅ High complexity functions < 8
- ✅ Technical debt < 150 hours

### Medium Term (3 Months)
- ✅ Code health score > 75
- ✅ Documentation > 70%
- ✅ High complexity functions < 3
- ✅ Technical debt < 50 hours
- ✅ Zero bare except clauses

### Long Term (6 Months)
- ✅ Code health score > 85
- ✅ Documentation > 80%
- ✅ No very high complexity functions
- ✅ Technical debt < 20 hours
- ✅ Automated quality gates in CI/CD

---

## 🆘 Common Issues

### "Analysis takes too long"
```bash
# Run quick analysis (30 seconds)
bash scripts/codescene_analyze.sh quick

# Or analyze specific module
python3 scripts/analyze_complexity.py --path bot/core/
```

### "Too many issues, where to start?"
Start with the Action Plan in `CODESCENE_ANALYSIS_REPORT.md`:
1. Week 1: Documentation (high leverage, low effort)
2. Week 2: Top 3 complexity hotspots
3. Week 3: Top 3 file hotspots

### "Don't want to break existing code"
```bash
# 1. Run tests BEFORE refactoring
pytest tests/ -v

# 2. Refactor

# 3. Run tests AFTER
pytest tests/ -v

# 4. Compare - should be identical
```

---

## 📚 Resources

- **Full Report:** `CODESCENE_ANALYSIS_REPORT.md`
- **Configuration:** `.codescene/config.yml`
- **Reports:** `.codescene/reports/`
- **Scripts:** `scripts/analyze_*.py`

---

## 🔄 Next Steps

1. **Review full report:** `CODESCENE_ANALYSIS_REPORT.md`
2. **Pick one quick win** from the checklist above
3. **Implement, test, commit**
4. **Re-run analysis** to see improvement
5. **Repeat weekly** until health score > 75

---

*Last updated: February 6, 2026*  
*Next review: After first refactoring session*
