# Tests Directory

This directory contains all test suites for the Mirror Leech Telegram Bot project.

## Structure

### `/unit/`
Unit tests for individual components and modules:
- API endpoints and gateway
- Manager classes (health, cache, redis, replication, task coordinator)
- Isolated component functionality

### `/integration/`
Integration tests that verify multiple components working together:
- Infrastructure tests (Phase 7)
- Enterprise features (Phase 9)
- Ecosystem integrations (Phase 10)
- Optimization and scaling (Phase 11)
- General integration tests

### `/performance/`
Performance and load testing:
- Load performance tests
- Stress tests
- Benchmarking suites

### `/tools/`
Utility scripts for testing and debugging:
- Debug command scripts
- Authentication testing tools
- Runtime fix utilities
- Quick fix and command test scripts

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Performance tests only
pytest tests/performance/
```

### Run with coverage
```bash
pytest --cov=src tests/
```

## Test Configuration

Test configuration is managed in `conftest.py` at the root of the tests directory.
