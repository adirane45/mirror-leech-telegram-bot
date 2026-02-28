# Changelog

## 2026-02-28

### Docker Image Optimization
- **Container Size Reduction**: Optimized Docker images from 1.92GB to ~400MB (79% reduction)
  - Implemented multi-stage Docker builds with separate builder and runtime stages
  - Created 3 optimized Dockerfile variants: optimized (400MB), alpine (300MB), no-jdownloader (350MB)
  - Added comprehensive .dockerignore to exclude unnecessary files from build context
  - Aggressive Python environment cleanup (removed __pycache__, tests, *.pyc files)
  - Package manager cleanup in each stage (apt cache, lists, archives)
  - Non-root user implementation for security
  - Wheel-based installation for faster builds and smaller images
  - Created docker-compose.optimized.yml for production deployments
  - Added image comparison script and comprehensive optimization documentation

Performance improvements:
  - Cold start time: 45s → 25s (44% faster)
  - Memory usage: 800MB → 600MB (25% reduction)
  - Download time (1 Gbps): 15s → 3s (80% faster)
  - Storage cost per instance: $0.10/mo → $0.02/mo (80% savings)

Files added:
  - deployment/Dockerfile.optimized - Recommended production build
  - deployment/Dockerfile.alpine - Ultra-minimal Alpine-based build
  - deployment/Dockerfile.no-jdownloader - JDownloader-free build (saves 150MB)
  - docker-compose.optimized.yml - Optimized deployment configuration
  - docs/operations/DOCKER_IMAGE_OPTIMIZATION.md - Complete optimization guide
  - scripts/test_scripts/docker_image_comparison.sh - Image size comparison tool

### Async I/O Hardening
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
