# Changelog

## 2026-02-28
- **Async I/O Hardening**: Offloaded all blocking I/O operations from async functions to prevent event loop blocking
  - Audited 20 files using AST-based scanner, found and fixed 31 blocking call sites
  - Wrapped synchronous file operations (open, os.path.*, shutil.*) with `asyncio.to_thread()`
  - Offloaded archive operations (ZIP/TAR compress/extract) to worker threads
  - Moved subprocess calls (docker-compose, ffmpeg) to async subprocess execution
  - Created async-safe versions of file operations in: archive_manager, backup_manager, config_watcher, media_info, memory_mapped_files, mtproto_parallel_uploader, and others
  - Added smoke benchmark script showing event loop responsiveness: <2ms avg lag, <8ms p95 during 96MB archive operations
  - Validated: Zero remaining blocking calls in async paths, all files compile cleanly

## 2026-02-23
- Added GitHub Actions workflows for build, quality, tests, release, and health checks.
- Added CI/CD documentation: setup checklist, pipeline reference, architecture, and summary.
- Updated project structure documentation to reflect CI/CD workflows and docs.

## 2026-02-20
- Added Telegram file cache manager and cache-aware leech uploads.
- Added file cache configuration settings.
- Added unit tests for file cache hashing.
- Updated documentation for Phase 6.1 progress.
- Added stream link generator endpoints and command scaffolding.
