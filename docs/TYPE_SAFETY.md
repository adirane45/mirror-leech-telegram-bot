# Type Safety Improvement Strategy

## Overview
This project uses a gradual typing strategy: enforce strict typing in selected core modules first, then expand module-by-module.

## Current Status
### Phase 1 - Foundation ✅
- Enabled core mypy checks in [pyproject.toml](pyproject.toml)
- Enabled `no_implicit_optional`
- Added typed-package marker: [src/py.typed](src/py.typed)
- Added selective external-library `ignore_missing_imports` overrides
- Enabled strict mode for initial core modules

### Phase 2 - Quality Infrastructure ✅
- Updated [pyproject.toml](pyproject.toml) with practical mypy settings and strict per-module overrides
- Added standalone mypy config: [.mypy.ini](.mypy.ini)
- Updated lint/type targets in [Makefile](Makefile)
- Added/updated quality configs:
  - [.pre-commit-config.yaml](.pre-commit-config.yaml)
  - [.pylintrc](.pylintrc)
  - [.flake8](.flake8)
  - [.bandit](.bandit)

## Strict Modules (Current)
- `config`
- `src.bot.core.plugin_manager`
- `src.bot.core.logger_manager`
- `src.bot.core.config_manager`
- `src.bot.core.celery_app`

## Commands
```bash
# Non-strict project-wide typing
make type-check

# Strict checks for selected modules
make type-check-strict

# Local quality gate (pre-commit + mypy + tests)
make quality-gate

# CI-ready command sequence
make ci-check

# Full suite (separate from enforceable CI checks)
make ci-test

# Optional: full pre-commit sweep (legacy backlog may fail)
make precommit-full

# Direct mypy run
python -m mypy src/ config/ --pretty --show-error-codes
```

## CI Command Sequence
Use this sequence in CI jobs after dependencies are installed:

```bash
python -m mypy --config-file pyproject.toml config/main_config.py --pretty --show-error-codes
```

This keeps CI aligned with the gradual typing rollout by enforcing mypy on the current green typed module set while broader strict rollout continues.

## Workflow for New Code
1. Add full type hints on new functions
2. Avoid implicit `Optional`; declare explicitly
3. Prefer built-in generics (`list[str]`, `dict[str, Any]`)
4. Run `make type-check` before commit
5. Keep strictness expansion module-by-module

## Next Phase (Phase 3)
Target utilities and web modules next:
- `src/bot/helper/ext_utils/`
- `src/web/`

Approach:
- Add return/argument annotations first
- Fix `no_implicit_optional` issues
- Add strict overrides for the next stable module set

## Common mypy issues
### `import-untyped`
For third-party libs without stubs, add module override in [pyproject.toml](pyproject.toml).

### `no-untyped-def`
Add full annotations for args and return type.

### `assignment` with `None` defaults
Use explicit optional typing, e.g. `str | None`.

## Goal
Reach global `strict = true` only after all high-traffic modules pass strict checks reliably.