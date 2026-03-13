# Week 1 Action List (Generated from Baseline Reports)

Date: 2026-03-08
Source reports:
- docs/audit_reports/largest_files_20260308_140502.txt
- docs/audit_reports/complexity_baseline_20260308_140502.txt
- docs/audit_reports/type_check_baseline_20260308_140502.txt

## 1) Immediate Priorities (This Week)

### P1 — Contain type-check debt in highest-impact modules
Goal: Reduce mypy errors quickly by targeting the files with the largest error counts and repeated patterns.

Top type-check hotspots:
1. integrations/sabnzbdapi/job_functions.py (59)
2. src/web/scheduled_downloads.py (40)
3. src/bot/core/logger_manager.py (28)
4. src/bot/core/memory_mapped_files.py (26)
5. src/bot/core/smart_retry.py (25)
6. src/bot/core/lazy_imports.py (24)
7. src/bot/core/alert_manager.py (24)
8. src/web/nodes.py (23)

Most frequent error classes:
- no-untyped-def (252)
- type-arg (141)
- no-untyped-call (121)
- attr-defined (39)
- assignment (33)

Execution plan:
- Add explicit return and parameter annotations to public and async functions first.
- Replace bare generics (list, dict, Callable, Task, Queue) with typed versions.
- Introduce Protocols or TypedDict only where they remove repeated attr-defined errors.
- For third-party untyped boundaries, isolate with small typed wrapper functions.

Definition of done (Week 1 target):
- 20-30% reduction in total type errors on baseline run.
- Top 3 hotspot files reduced by at least 40% each.

---

### P2 — Break up highest complexity functions (F/E only)
Goal: Reduce maintenance risk in large orchestration methods before broad refactoring.

Top complexity targets:
1. src/bot/modules/mirror_leech.py :: Mirror.new_event (115, F)
2. src/bot/modules/bot_settings.py :: edit_bot_settings (91, F)
3. src/bot/helper/listeners/task_listener.py :: TaskListener.on_download_complete (59, F)
4. src/bot/helper/mirror_leech_utils/download_utils/jd_download.py :: add_jd_download (57, F)
5. src/bot/modules/rss.py :: rss_monitor (54, F)
6. src/bot/helper/mirror_leech_utils/telegram_uploader.py :: TelegramUploader._upload_file (53, F)
7. src/web/admin_download_handler.py :: AdminDownloadHandler._process_download (53, F)
8. src/bot/helper/mirror_leech_utils/download_utils/qbit_download.py :: add_qb_torrent (51, F)

Execution plan:
- Split each target into pure helper functions with single responsibility.
- Keep behavior unchanged; add regression tests before/after extraction if available.
- Limit each PR to 1-2 functions to avoid review risk.

Definition of done (Week 1 target):
- Bring top 2 functions down from F to D/C.
- No test regressions on existing pytest suite.

---

### P3 — Start architecture consolidation from largest files
Goal: Reduce bloat and improve navigability by choosing first merge/extract candidates.

Largest core files snapshot:
- src/bot/core/handlers.py (820)
- src/bot/core/ml_anomaly_detection.py (644)
- src/bot/core/memory_mapped_files.py (617)
- src/bot/core/stream_weaver.py (616)
- src/bot/core/zombie_reaper.py (596)

Execution plan:
- For each file >600 lines, map responsibilities and identify extractable submodules.
- Prioritize files that are also type or complexity hotspots (memory_mapped_files.py first).
- Create one consolidation design note before moving code.

Definition of done (Week 1 target):
- One approved extraction plan for the first 2 large files.
- At least one file reduced by 15%+ lines through extraction.

---

## 2) Suggested Daily Sequence (Week 1)

Day 1:
- Fix no-untyped-def and type-arg in integrations/sabnzbdapi/job_functions.py.
- Run targeted mypy on that file.

Day 2:
- Fix src/web/scheduled_downloads.py and src/web/nodes.py signatures and generics.

Day 3:
- Refactor Mirror.new_event into helper methods with unchanged behavior.

Day 4:
- Refactor edit_bot_settings and add/update focused tests.

Day 5:
- Draft extraction proposal for handlers.py and memory_mapped_files.py.
- Re-run baseline script and compare report deltas.

---

## 3) Tracking Checklist

- [ ] Capture before/after error counts for each edited file.
- [ ] Track complexity score deltas for refactored functions.
- [ ] Record every accepted Copilot suggestion in session-log.md.
- [ ] Keep each change set small and CI-green.
- [ ] Re-run docs/audit_reports baseline at end of week.

## 4) Copilot Prompt Starters for This Action List

Type fixes:
"Add full Python 3.11 type annotations to this file to reduce mypy no-untyped-def and type-arg errors. Keep behavior unchanged and prefer minimal diffs."

Complexity reduction:
"Refactor this high-complexity function into smaller private helpers, preserve exact behavior, and keep public API unchanged. Suggest a commit-sized patch."

Consolidation planning:
"Analyze this 600+ line module and propose extraction candidates by responsibility. Return a 2-phase migration plan with minimal import breakage."

---

## 5) Status Update + Next Actions (as of 2026-03-08)

Completed in focused complexity pass:
- YtDlp.new_event: C(15) -> A(5)
- TelegramUploader._upload_single_file: C(16) -> B(8)
- Clone.new_event: C(11) -> A(4)
- Official radon line: M 485:4 TaskListener.on_download_complete - A (3)
	- Command: `./venv/bin/radon cc src/bot/helper/listeners/task_listener.py -s | grep -F "TaskListener.on_download_complete"`
- CI check: pass (`make ci-check`)

### Next Action List (ordered)

1. Continue F/E reduction from P2 top list:
	- Mirror.new_event (F)
	- edit_bot_settings (F)

2. Keep C-target momentum (highest C only, one function per PR):
	- src/bot/core/media_info.py :: format_info (C20)
	- src/bot/helper/listeners/aria2_listener.py :: _on_bt_download_complete (C20)
	- src/bot/helper/listeners/jdownloader_listener.py :: _jd_listener (C20)

3. Type hotspot sprint (P1):
	- integrations/sabnzbdapi/job_functions.py
	- src/web/scheduled_downloads.py
	- src/bot/core/logger_manager.py

4. End-of-day cadence:
	- Track before/after radon + mypy deltas in session log
	- Keep PRs small and CI-green

### Option C — Architecture Consolidation (P3 kickoff)

Scope locked for first extraction-planning cycle:
- src/bot/core/handlers.py (820)
- src/bot/core/ml_anomaly_detection.py (644)
- src/bot/core/memory_mapped_files.py (617; type hotspot)

#### A) handlers.py — responsibility map and extraction candidates

Current responsibilities mixed in one `add_handlers()` block:
- Global command audit pre-handler (`_command_audit` + regex `/`).
- Core command registrations (auth/admin, mirror/leech, queue, status, users, settings, archives, media, enhanced dashboard).
- Optional/feature-bucket registrations in nested `try` blocks (command health handlers, Category B handlers).
- Bootstrap logging and global error boundary for all registration.

Extraction candidates:
- `src/bot/core/handler_registry.py`
	- `register_message(...)`, `register_callback(...)`, `register_edited(...)` thin helpers.
	- Optional `HandlerSpec` dataclass for declarative mapping.
- `src/bot/core/handler_groups/` package:
	- `core_admin.py`
	- `mirror_leech.py`
	- `status_dashboard.py`
	- `queue_controls.py`
	- `archive_media.py`
	- `optional_features.py` (command health + Category B safe registration)
- Keep `handlers.py` as bootstrap/orchestrator only (call group-level `register(bot)` functions in deterministic order).

Migration plan:
1. Introduce registry helpers and one small group module; keep existing `add_handlers()` behavior unchanged.
2. Move handler registrations group-by-group with no filter changes and no command alias changes.
3. Move optional nested `try` blocks into `optional_features.py` with same warning logs.
4. Final pass: shrink `handlers.py` to orchestration + audit handler + top-level error boundary.

Safety constraints:
- Preserve registration order and `group` values exactly.
- Preserve `CustomFilters` combinations exactly.
- Validate by smoke-running command list and callback handlers after each PR.

#### B) ml_anomaly_detection.py — responsibility map and extraction candidates

Current responsibilities in one service class:
- Types/config (`AnomalyDetectionConfig`, `Anomaly`, `PredictionResult`).
- State/config lifecycle (`configs`, `data`, `anomalies`, cooldown tracking).
- Detection algorithms (`_detect_zscore`, `_detect_iqr`, `_detect_trend_anomaly`).
- Prediction + scaling recommendation.
- Pattern recognition + statistics/reporting + singleton factory.

Extraction candidates:
- `src/bot/core/anomaly/types.py` (all dataclasses / type aliases).
- `src/bot/core/anomaly/detection.py` (z-score, iqr, trend, severity).
- `src/bot/core/anomaly/prediction.py` (linear regression + scaling recommendation).
- `src/bot/core/anomaly/patterns.py` (time/value recurrence detection).
- `src/bot/core/anomaly/service.py` (stateful orchestrator class only).
- `src/bot/core/anomaly/__init__.py` (singleton accessor API).

Migration plan:
1. Move dataclasses/types first; keep imports backward compatible in original module.
2. Extract pure algorithm helpers (detection/prediction/patterns) without state mutation.
3. Refactor `MLAnomalyDetector` to delegate to helpers while keeping public methods identical.
4. Keep `get_anomaly_detector()` API stable to avoid import breakage.

Typing alignment during extraction:
- Add explicit return types for constructors / mutating methods.
- Replace broad `Dict[str, Any]` where practical with typed aliases for report payloads.

#### C) memory_mapped_files.py — responsibility map, extraction candidates, type-hotspot plan

Current responsibilities combined:
- Low-level map lifecycle (`MemoryMappedFile`).
- Chunk pipeline orchestration (`MMapProcessor`).
- Feature services (`MMapHasher`, `MMapCopier`, `MMapSearcher`).
- Shared utilities duplicated in multiple classes (`_preallocate_file_sync`).
- Convenience API functions for external callers.

Extraction candidates:
- `src/bot/core/mmap/types.py` (`MMapMode`, `MMapInfo`, `ProcessStats`).
- `src/bot/core/mmap/file_map.py` (`MemoryMappedFile` only).
- `src/bot/core/mmap/processor.py` (`MMapProcessor`).
- `src/bot/core/mmap/operations.py` (`MMapHasher`, `MMapCopier`, `MMapSearcher`).
- `src/bot/core/mmap/utils.py` (single preallocation helper + shared file sizing helpers).
- `src/bot/core/mmap/api.py` (convenience async functions).

Migration plan:
1. Extract `types.py` and `utils.py` first (dedupe preallocation helper).
2. Move `MemoryMappedFile` next and enforce non-optional mapped state before read/write via guard methods.
3. Move processor + operations classes to dedicated modules.
4. Keep a compatibility facade in original module (re-export symbols) for one release cycle.

Type-hotspot mitigation integrated with extraction:
- Replace `Any`-typed file handles with concrete IO protocols/types.
- Eliminate nullable `mmap_obj` access errors by private `_require_mmap()` guard returning `mmap.mmap`.
- Add missing `-> None` and concrete `Callable` return signatures in async helpers.
- Normalize arithmetic using non-optional `map_length` post-open invariant.

#### Phase sequencing for week execution

PR-1 (scaffold only):
- Create target packages/modules and compatibility exports; zero behavior changes.

PR-2 (handlers split):
- Extract one handler group + registry helper; verify command/callback parity.

PR-3 (mmap split + typing):
- Extract `types/file_map/utils` first and close highest-frequency mypy errors.

PR-4 (anomaly split):
- Extract dataclasses + pure algorithms; keep singleton API stable.

Done criteria for Option C cycle:
- `handlers.py` reduced to orchestration-focused file.
- `memory_mapped_files.py` type errors materially reduced (target: >=40% in that module).
- No import-path breakage due to compatibility re-exports.

#### Option C implementation status (completed)

Implemented architecture extraction and compatibility facades:
- `src/bot/core/handlers.py` -> thin backward-compatible facade (`add_handlers` re-export).
- `src/bot/core/core_handlers.py` -> extracted large handler registration implementation.
- `src/bot/core/ml_anomaly_detection.py` -> facade to new `src/bot/core/anomaly/` package.
- `src/bot/core/memory_mapped_files.py` -> facade to new `src/bot/core/mmap/` package.

New extracted packages/modules:
- `src/bot/core/anomaly/`: `types.py`, `detection.py`, `prediction.py`, `patterns.py`, `service.py`, `__init__.py`
- `src/bot/core/mmap/`: `types.py`, `file_map.py`, `processor.py`, `operations.py`, `utils.py`, `api.py`, `__init__.py`
- Handler support modules: `src/bot/core/handler_registry.py`, `src/bot/core/handler_groups/optional_features.py`

Measured size outcome for the three P3 target files:
- `src/bot/core/handlers.py`: 820 -> 5 lines
- `src/bot/core/ml_anomaly_detection.py`: 644 -> 17 lines
- `src/bot/core/memory_mapped_files.py`: 617 -> 31 lines

Validation executed:
- `python -m py_compile` on all Option C extracted/facade modules completed successfully.

Follow-up cleanup pass completed:
- Removed duplicate legacy tail from `src/bot/core/core_handlers.py`.
- Split handler registration responsibilities into focused group modules:
	- `src/bot/core/handler_groups/core_admin.py`
	- `src/bot/core/handler_groups/queue_controls.py`
	- `src/bot/core/handler_groups/status_dashboard.py`
- Wired `core_handlers.py` to call these extracted group registrars.
- Current sizes:
	- `src/bot/core/core_handlers.py`: 298 lines
	- `src/bot/core/handlers.py`: 5 lines
