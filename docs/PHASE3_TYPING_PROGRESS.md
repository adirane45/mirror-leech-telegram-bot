# Phase 3: Type Safety Hardening Progress

**Date:** March 7, 2026  
**Status:** ✅ Initial module set complete

---

## Objective
Gradually improve type safety across the codebase using mypy strict checking, starting with core configuration modules and progressively expanding to other areas.

---

## Strategy

### 1. **Scoped mypy Overrides**
Added targeted overrides in `pyproject.toml` to isolate integration-heavy modules from strict checks:

**Relaxed modules** (third-party wrapper integrations):
- `integrations.rclone.*`
- `integrations.myjd.*`
- `integrations.sabnzbdapi.*`

These modules are excluded from:
- `disallow_untyped_defs`
- `disallow_untyped_calls`
- `check_untyped_defs`

**Strict enforcement** (core modules):
- `config` package
- `config.main_config`
- `src.bot.core.plugin_manager`
- `src.bot.core.logger_manager`
- `src.bot.core.config_manager`
- `src.bot.core.celery_app`

---

## 2. **Completed Modules**

### ✅ `config.main_config`
**Status:** Fully strict-typed — 0 errors  
**Changes Applied:**
- Added type annotations to `_get_safe_int()` helper function:
  ```python
  def _get_safe_int(key: str, default: int) -> int:
  ```
- Annotated all empty dict/list initializers:
  ```python
  TG_PROXY: dict[str, str] = {}
  FFMPEG_CMDS: dict[str, str] = {}
  UPLOAD_PATHS: dict[str, str] = {}
  EMAIL_TO_ADDRESSES: list[str] = []
  API_WHITELIST_IPS: list[str] = []
  ```
- Typed all `Config` class methods:
  ```python
  def load(cls) -> None:
  def _get_all_vars(cls) -> dict[str, object]:
  def __getattr__(self, name: str) -> object:
  def get(cls, key: str, default: object = None) -> object:
  ```

**Validation:**
```bash
$ mypy config/main_config.py
Success: no issues found in 1 source file
```

**Impact:**
- **33 strict typing errors** resolved
- All configuration loading logic is now type-safe
- Better IDE autocomplete and error detection
- Prevents type-related bugs in config access

---

### ✅ `config.__init__`
**Status:** Fully strict-typed — 0 errors  
**Validation:**
```bash
$ mypy config/
Success: no issues found in 2 source files
```

---

## 3. **Next Targets**

Based on mypy scan, the following modules have simple fixes (mostly missing return type annotations):

### High-Priority Candidates
1. **`src/bot/helper/ext_utils/links_utils.py`**
   - Missing return types on 7 boolean-returning functions
   - Quick wins: add `-> bool` annotations

2. **`src/bot/helper/ext_utils/bulk_links.py`**
   - Missing annotations on 3 functions
   - Moderate: needs parameter typing + return types

3. **`src/bot/core` modules**
   - Already listed as strict in mypy config
   - Need compliance verification and fixes

---

## 4. **Integration Modules**

Integration wrappers intentionally relaxed due to:
- Third-party API complexity (Rclone, JDownloader, SABnzbd)
- Dynamic typing requirements
- External library dependencies without type stubs

**Strategy:** Keep strict checks disabled; add selective `# type: ignore` comments where needed for maintainability.

---

## 5. **Validation Commands**

```bash
# Check specific module
mypy config/main_config.py

# Check entire package
mypy config/

# Full project scan (with overrides active)
mypy src/ config/ integrations/

# Check strict modules only
mypy --config-file pyproject.toml config/ src/bot/core/
```

---

## Progress Metrics

| Module Set           | Status | Errors Fixed | Remaining |
|----------------------|--------|--------------|-----------|
| `config.*`           | ✅ Done | 33           | 0         |
| `integrations.*`     | 🔕 Relaxed | N/A      | N/A       |
| `src/bot/core.*`     | 📋 Next | TBD          | TBD       |
| `src/bot/helper.*`   | 📋 Next | TBD          | TBD       |

---

## Benefits Achieved

1. **Type Safety:** Configuration errors caught at static analysis time
2. **IDE Support:** Full autocomplete and inline error detection
3. **Refactoring Safety:** Type-checked changes prevent runtime breaks
4. **Documentation:** Type hints serve as inline API documentation
5. **Maintenance:** Easier onboarding for new contributors

---

## Rollout Plan

**Phase 3A (Complete):**
- ✅ Add integration overrides
- ✅ Fix `config.main_config` strict typing

**Phase 3B (Next):**
- Fix `src/bot/helper/ext_utils/` utilities
- Verify `src/bot/core/` modules
- Document common typing patterns

**Phase 3C (Future):**
- Gradually expand strict checking to remaining modules
- Add pre-commit hook for mypy validation
- CI/CD integration for type checking

---

## Technical Notes

### Type Annotation Patterns Used

**1. Function signatures:**
```python
def process_config(key: str, default: int) -> int:
```

**2. Empty collections:**
```python
config: dict[str, str] = {}
items: list[str] = []
```

**3. Generic return types:**
```python
def get(cls, key: str, default: object = None) -> object:
```

**4. Class methods:**
```python
@classmethod
def load(cls) -> None:
```

### Common Pitfalls Avoided
- ❌ Using bare `dict` or `list` (use `dict[K, V]`, `list[T]`)
- ❌ Omitting return types (always specify, even `-> None`)
- ❌ Over-strict integration typing (use overrides for wrappers)

---

## References

- [PEP 484 – Type Hints](https://peps.python.org/pep-0484/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- Project: `pyproject.toml` mypy configuration
