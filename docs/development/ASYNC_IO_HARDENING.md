# Async I/O Hardening Documentation

**Date:** 2026-02-28  
**Status:** ✅ Completed  
**Impact:** Event Loop Performance & Responsiveness

---

## Overview

This document details the comprehensive async I/O hardening effort that eliminated event loop blocking across the codebase. The work ensures that all async functions properly offload blocking operations to worker threads, preventing the event loop from freezing during I/O operations.

## Problem Statement

In Python asyncio applications, blocking operations in async functions can freeze the entire event loop, preventing other coroutines from executing. Common blocking operations include:

- Synchronous file I/O (`open()`, `read()`, `write()`)
- OS path operations (`os.path.exists()`, `os.path.getsize()`, etc.)
- File system operations (`shutil.copy()`, `shutil.rmtree()`, etc.)
- Archive operations (`zipfile.ZipFile()`, `tarfile.open()`)
- Subprocess calls (`subprocess.run()`)

## Solution Approach

### 1. Automated Detection

Created an AST-based audit scanner that:
- Parses Python source files
- Identifies async function definitions
- Detects blocking call patterns within async contexts
- Reports file locations and line numbers

### 2. Systematic Remediation

Applied three remediation patterns:

#### Pattern A: Thread Offloading with `asyncio.to_thread()`
```python
# Before (blocks event loop)
async def check_file(path: str) -> bool:
    return os.path.exists(path)

# After (non-blocking)
async def check_file(path: str) -> bool:
    return await asyncio.to_thread(os.path.exists, path)
```

#### Pattern B: Async Subprocess Execution
```python
# Before (blocks event loop)
async def restart_service(service: str):
    subprocess.run(["docker-compose", "restart", service])

# After (non-blocking)
async def restart_service(service: str):
    proc = await asyncio.create_subprocess_exec(
        "docker-compose", "restart", service,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.wait()
```

#### Pattern C: Async File I/O with `aiofiles`
```python
# Before (blocks event loop)
async def read_config(path: str) -> str:
    with open(path) as f:
        return f.read()

# After (non-blocking)
async def read_config(path: str) -> str:
    async with aiofiles.open(path) as f:
        return await f.read()
```

### 3. Helper Method Pattern

For clarity and maintainability, blocking operations were extracted into separate sync helper methods:

```python
class ArchiveManager:
    async def compress_zip(self, source: Path, output: Path):
        """Async entry point"""
        return await asyncio.to_thread(
            self._compress_zip_sync, source, output
        )
    
    def _compress_zip_sync(self, source: Path, output: Path):
        """Synchronous worker method"""
        with zipfile.ZipFile(output, 'w') as zf:
            for file in source.rglob('*'):
                zf.write(file, file.relative_to(source))
```

## Modified Files (20 Total)

### Core Modules
1. **src/bot/__main__.py**
   - Config file existence checks
   - Status: ✅ Fixed

2. **src/bot/core/advanced_dashboard_endpoints.py**
   - Log file reading with `_read_recent_logs_sync` helper
   - Status: ✅ Fixed

3. **src/bot/core/archive_manager.py**
   - ZIP/TAR compression and extraction
   - File counting and size calculation
   - Helpers: `_compress_zip_sync`, `_extract_zip_sync`, etc.
   - Status: ✅ Fixed

4. **src/bot/core/automation_system.py**
   - Docker-compose subprocess calls
   - Status: ✅ Fixed

5. **src/bot/core/backup_manager.py**
   - `shutil.copytree`, `shutil.copy2`, `shutil.rmtree`
   - Status: ✅ Fixed

6. **src/bot/core/config_watcher.py**
   - ENV file parsing with `_parse_env_file_sync` helper
   - Status: ✅ Fixed

7. **src/bot/core/dynamic_config.py**
   - File existence and mtime checks
   - Status: ✅ Fixed

8. **src/bot/core/gitops_updater.py**
   - Migration script existence checks
   - Status: ✅ Fixed

9. **src/bot/core/jdownloader_booter.py**
   - JSON config file writes with `_write_json_file` helper
   - Status: ✅ Fixed

10. **src/bot/core/media_info.py**
    - Thumbnail output file checks
    - Logger reference fix
    - Status: ✅ Fixed

11. **src/bot/core/memory_mapped_files.py**
    - File size checks, file open, mmap creation
    - Preallocate operations
    - Status: ✅ Fixed

12. **src/bot/core/metadata_stripper.py**
    - JSON backup save/load operations
    - Status: ✅ Fixed

13. **src/bot/core/mtproto_parallel_uploader.py**
    - File size checks and chunk reads
    - Helper: `_read_chunk_sync`
    - Status: ✅ Fixed

14. **src/bot/core/recovery_manager.py**
    - Shutil file operations in repair paths
    - Status: ✅ Fixed

15. **src/bot/core/web3_ipfs_storage.py**
    - File hashing with `_hash_file_sync` helper
    - Status: ✅ Fixed

### Helper Modules
16. **src/bot/helper/mirror_leech_utils/rclone_utils/serve.py**
    - Rclone.conf async write with aiofiles
    - Status: ✅ Fixed

### Command Modules
17. **src/bot/modules/archive.py**
    - Path existence and isfile checks
    - Status: ✅ Fixed

18. **src/bot/modules/mediainfo.py**
    - File existence/size checks
    - Status: ✅ Fixed

19. **src/bot/modules/restart.py**
    - `.restartmsg` async read with aiofiles
    - Status: ✅ Fixed

20. **src/bot/modules/services.py**
    - QR image existence checks and file removal
    - Status: ✅ Fixed

## Validation Results

### Compile Validation
```bash
python -m compileall src/bot/
# Result: All files compiled successfully ✅
```

### Error Scan
```bash
# Zero diagnostics on modified files ✅
```

### Blocking Call Re-Audit
```bash
# TOTAL: 0 blocking calls detected ✅
```

### Performance Benchmark

Created `scripts/test_scripts/async_smoke_benchmark.py` to measure event loop responsiveness under load.

#### Test Results
```json
{
  "baseline_idle_2s": {
    "loop_lag_avg_ms": 1.459,
    "loop_lag_p95_ms": 5.085,
    "loop_lag_max_ms": 7.12
  },
  "archive_compress_zip": {
    "duration_s": 9.997,
    "loop_lag_avg_ms": 1.89,
    "loop_lag_p95_ms": 7.359,
    "loop_lag_max_ms": 24.735,
    "payload_size_mb": 96,
    "ok": true
  },
  "archive_extract_zip": {
    "duration_s": 0.524,
    "loop_lag_avg_ms": 0.67,
    "loop_lag_p95_ms": 1.482,
    "loop_lag_max_ms": 7.655,
    "ok": true
  }
}
```

#### Interpretation
- **Baseline:** Event loop wakes up every ~1.5ms when idle
- **Under Load:** Loop lag stays under 2ms average, 8ms p95
- **Max Lag:** 24.7ms during 96MB compression (acceptable for I/O-bound work)
- **Conclusion:** Event loop remains responsive throughout heavy operations ✅

## Best Practices

### When to Use `asyncio.to_thread()`
- File I/O operations (read, write, copy, move)
- OS path checks (exists, getsize, isfile, isdir)
- Archive operations (ZIP, TAR compression/extraction)
- Subprocess calls with `subprocess.run()`
- Any CPU-bound synchronous work

### When to Use `asyncio.create_subprocess_exec()`
- Long-running external commands (ffmpeg, aria2, etc.)
- Need to capture stdout/stderr
- Need to send input to stdin
- Want to monitor process in real-time

### When to Use `aiofiles`
- Sequential file reading/writing
- Streaming large files
- Log file operations
- Config file updates

## Monitoring

### Loop Lag Monitoring
The benchmark script demonstrates loop lag monitoring:

```python
async def monitor_loop_lag(lags: list, stop_event: asyncio.Event):
    """Monitor event loop responsiveness"""
    while not stop_event.is_set():
        start = asyncio.get_event_loop().time()
        await asyncio.sleep(0.02)  # Target: 20ms
        actual_delay = (asyncio.get_event_loop().time() - start) * 1000
        lag = actual_delay - 20
        lags.append(lag)
```

### Production Recommendations
- Add loop lag metrics to Prometheus
- Alert on p95 > 50ms sustained for > 1 minute
- Monitor max lag spikes > 200ms
- Track operations causing high lag

## Future Work

### Potential Improvements
1. **Profile Remaining Sync Code**
   - Audit non-async functions for heavy blocking operations
   - Consider async alternatives for high-traffic paths

2. **Add More Benchmarks**
   - Test concurrent operations (multiple archives + media processing)
   - Stress test with 100+ simultaneous bot commands
   - Measure impact on Telegram API responsiveness

3. **CI/CD Integration**
   - Add AST audit to pre-commit hooks
   - Fail builds on new blocking calls in async functions
   - Run benchmark on every PR

4. **Documentation**
   - Add async best practices to CONTRIBUTING.md
   - Create developer guide for async patterns
   - Document performance SLOs

## References

- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [asyncio.to_thread() PEP](https://www.python.org/dev/peps/pep-0492/)
- [aiofiles library](https://github.com/Tinche/aiofiles)
- Benchmark script: `scripts/test_scripts/async_smoke_benchmark.py`

---

**Maintainer:** GitHub Copilot (AI Assistant)  
**Review Status:** Validated via automated tests and benchmarks  
**Last Verification:** 2026-02-28
