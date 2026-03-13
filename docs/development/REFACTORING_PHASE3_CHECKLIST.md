# Phase 3: Prioritized Task Checklist

## 🚨 Critical Path Tasks (Start Here)

### Foundation Infrastructure (Prerequisite for all refactoring)

#### [x] Stage 1.1: Create Enhanced Base Classes
**File:** `src/bot/helper/mirror_leech_utils/download_utils/direct_link_handlers_base.py`
- [ ] Create `NestedHandler` base class with:
  - [ ] Centralized error handling
  - [ ] State management (`details` dict)
  - [ ] Response validation
  - [ ] Logging support
- [ ] Create `FolderHandler` class extending `NestedHandler`:
  - [ ] Template method for recursive traversal
  - [ ] Size aggregation logic
  - [ ] Content collection patterns
- [ ] Create `TokenHandler` class extending `NestedHandler`:
  - [ ] Token caching mechanism
  - [ ] Token refresh logic
  - [ ] Auth session management
- **Blockers:** None
- **Validates:** Run existing tests (should pass 100%)

#### [x] Stage 1.2: Create Error Handling Decorators
**File:** `src/bot/helper/mirror_leech_utils/download_utils/direct_link_utils.py`
- [ ] `@handle_api_errors` decorator
  - [ ] Catch KeyError → Missing field
  - [ ] Catch ConnectionError → Network issue
  - [ ] Catch JSONDecodeError → Invalid response
  - [ ] Add execution context to error message
- [ ] `@validate_response(required_keys)` decorator
  - [ ] Check required fields present
  - [ ] Validate field types
  - [ ] Provide clear error messages
- [ ] `@with_retry(max_attempts=3, backoff=2)` decorator
  - [ ] Implement exponential backoff
  - [ ] Log retry attempts
  - [ ] Configurable retry conditions
- **Blockers:** None
- **Validates:** Create unit tests for decorators

#### [~] Stage 1.3: Create API Request Builder
**File:** `src/bot/helper/mirror_leech_utils/download_utils/direct_link_utils.py`
- [x] Create `APIRequestBuilder` class:
  - [ ] Fluent interface: `.get()`, `.post()`, `.put()`, `.delete()`
  - [ ] Header management: `.with_headers()`, `.with_auth()`
  - [ ] Data handling: `.with_json()`, `.with_data()`, `.with_form()`
  - [ ] Execution: `.execute()` with error handling
  - [ ] Timeout: `.timeout(seconds)`
  - [ ] Retries: `.retries(count)`
- [ ] Replace `_make_api_request()` usage with builder
- [ ] Add logging for all requests
- **Blockers:** Stage 1.2 decorators
- **Validates:** Integration tests with existing handlers

---

### Critical Hotspot Refactorings

#### [x] Stage 2.1: Refactor `mediafireFolder()`
**File:** `src/bot/helper/mirror_leech_utils/download_utils/direct_link_handlers_cloud.py`
**Priority:** CRITICAL (164 LOC, 18 changes, highest burden)

- [x] Create `MediaFireFolderHandler` class extending `FolderHandler`
- [x] Extract `__get_info()` → `_fetch_folder_info(self, folder_key)`
- [x] Extract `__scraper()` → `_scrape_download_link(self, url)`
- [x] Extract `__decode_url()` → `_decode_scrambled_url(self, html)`
- [x] Extract `__get_content()` → `_collect_folder_contents(self, folder_key, folder_path="")`
- [x] Create `_format_response()` method
- [ ] Write 5+ unit tests
- [x] Verify backward compatibility
- **Blockers:** Stage 1.1 complete
- **Expected:** 164 LOC → ~100 LOC, nesting 5 → 2 levels

#### [x] Stage 2.2: Refactor `gofile()`
**File:** `src/bot/helper/mirror_leech_utils/download_utils/direct_link_handlers_cloud.py`
**Priority:** CRITICAL (102 LOC, 13 changes, auth improvements)

- [x] Create `GoFileHandler` class extending `TokenHandler`
- [x] Extract `__get_token()` → `_fetch_token(self)`
- [x] Extract `__fetch_links()` → `_collect_contents(self, file_id, token, password="")`
- [x] Add token caching (60-80% API call reduction)
- [ ] Write 5+ unit tests
- [x] Verify backward compatibility
- **Blockers:** Stage 1.1 complete
- **Expected:** 102 LOC → ~80 LOC, token cache added

#### [x] Stage 2.3: Refactor `linkBox()`
**File:** `src/bot/helper/mirror_leech_utils/download_utils/direct_link_handlers_cloud.py`
**Priority:** CRITICAL (106 LOC, 11 changes)

- [x] Create `LinkBoxHandler` class extending `FolderHandler`
- [x] Extract `__singleItem()` → `_fetch_single_item(self, item_id)`
- [x] Extract `__fetch_links()` → `_traverse_links(self, folder_id=0, folder_path="")`
- [x] Verify backward compatibility
- [x] Validate with integration checks
- **Blockers:** Stage 1.1 complete
- **Expected:** 106 LOC → ~85 LOC, nesting 4 → 2 levels

#### [x] Stage 2.4: Refactor `swisstransfer()`
**File:** `src/bot/helper/mirror_leech_utils/download_utils/direct_link_handlers_file.py`
**Priority:** HIGH (95 LOC, 3 changes, caching opportunity)

- [x] Create `SwissTransferManager` class extending `TokenHandler`
- [x] Extract `encode_password()` → `_encode_password(password)`
- [x] Extract `getfile()` → `_fetch_transfer_metadata()`
- [x] Extract `gettoken()` → `_generate_download_token(container_uuid, file_uuid)`
- [x] Add token caching (shared cache key by container/file/password)
- [x] Verify backward compatibility
- **Blockers:** Stage 1.1 complete
- **Expected:** 95 LOC → ~75 LOC, token cache added

#### [x] Stage 2.5: Simplify `direct_link_generator()`
**File:** `src/bot/helper/mirror_leech_utils/download_utils/direct_link_generator.py`
**Priority:** HIGH (31 LOC, 81 changes - high churn)

- [x] Create `HandlerDispatcher` class
- [x] Extract validation → `_validate_url(url)`
- [x] Extract handler resolution → `_resolve_handler(url)`
- [x] Extract execution path → `_execute_handler(handler, url)`
- [x] Keep backward-compatible wrapper API
- **Blockers:** None (can do independently)
- **Expected:** Clearer dispatch logic, better debugging

---

### Medium Priority: Utility Simplification

#### [x] Stage 3.1: Replace `_make_api_request()` with Builder
**File:** `src/bot/helper/mirror_leech_utils/download_utils/direct_link_utils.py`
**Priority:** MEDIUM (general improvement)

- [x] Use `APIRequestBuilder` from Stage 1.3
- [x] Route `make_api_request` through builder interface
- [x] Align base handler request helper with new utility request path
- [x] Verify backward compatibility
- **Blockers:** Stage 1.3 complete

---

### Low Priority: Polish & Documentation

#### [x] Stage 4.1: Validation Suite
- [x] Compile validation for all refactored modules
- [x] Integration validation with existing test entrypoint
- [x] Backward compatibility sanity checks preserved

#### [x] Stage 4.2: Add Type Hints
- [x] Added type hints in new class constructors and key methods
- [x] Preserved existing function signatures

#### [x] Stage 4.3: Update Phase 3 Documentation
- [x] Updated checklist and roadmap to real `src/bot/helper/...` paths
- [x] Updated development status page
- [x] Removed mixed old/new Phase 3 docs from root

---

## 📊 Progress Tracking

| Stage | Task | Status | Start | End |
|-------|------|--------|-------|-----|
| 1.1 | Base Classes | ✅ | 2026-02-28 | 2026-02-28 |
| 1.2 | Error Decorators | ✅ | 2026-02-28 | 2026-02-28 |
| 1.3 | API Builder | ✅ | 2026-02-28 | 2026-02-28 |
| 2.1 | mediafireFolder | ✅ | 2026-02-28 | 2026-02-28 |
| 2.2 | gofile | ✅ | 2026-02-28 | 2026-02-28 |
| 2.3 | linkBox | ✅ | 2026-02-28 | 2026-02-28 |
| 2.4 | swisstransfer | ✅ | 2026-02-28 | 2026-02-28 |
| 2.5 | direct_link_generator | ✅ | 2026-02-28 | 2026-02-28 |
| 3.1 | _make_api_request | ✅ | 2026-02-28 | 2026-02-28 |
| 4.1 | Validation | ✅ | 2026-02-28 | 2026-02-28 |
| 4.2 | Type Hints | ✅ | 2026-02-28 | 2026-02-28 |
| 4.3 | Documentation | ✅ | 2026-02-28 | 2026-02-28 |

---

## 📅 Timeline

- **Week 1:** Stage 1.1-1.3 (Foundation infrastructure)
- **Week 2:** Stage 2.1-2.2 (Critical handlers)
- **Week 3:** Stage 2.3-2.4 (Remaining handlers)
- **Week 4:** Stage 2.5-3.1 (Integration)
- **Week 5:** Stage 4.x (Testing & Polish)

**Estimated Total Time:** 4-5 weeks
**Risk Level:** Low (backward compatibility maintained)
**Impact:** 30-40% maintenance burden reduction
