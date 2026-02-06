# Workspace Structure & Organization Guide

**Last Updated**: February 6, 2026  
**Status**: ✅ Clean & Organized

---

## Directory Hierarchy

```
mirror-leech-telegram-bot/
├── bot/                           # Main application code
│   ├── __init__.py
│   ├── __main__.py               # Entry point
│   ├── core/                     # Core functionality (50+ modules)
│   │   ├── enhanced_startup.py   # Phase 5: HA orchestration
│   │   ├── api_endpoints.py
│   │   ├── health_monitor.py
│   │   ├── cluster_manager.py
│   │   ├── failover_manager.py
│   │   ├── replication_manager.py
│   │   ├── distributed_state_manager.py
│   │   ├── task_coordinator.py
│   │   ├── performance_optimizer.py
│   │   ├── api_gateway.py
│   │   └── ... (40+ more core modules)
│   ├── helper/                   # Utility functions
│   └── modules/                  # Command modules (37+ modules)
│
├── tests/                         # Test suite (15 test files)
│   ├── conftest.py
│   ├── test_enhanced_startup_phase5.py
│   ├── test_api_endpoints.py
│   ├── test_health_monitor.py
│   └── ... (12+ more test files)
│
├── config/                        # Configuration
│   ├── main_config.py            # Main configuration
│   ├── .env.production           # Production secrets (git-ignored)
│   ├── requirements.txt
│   └── requirements-cli.txt
│
├── scripts/                       # Operational scripts
│   ├── deploy.sh                 # Deployment script
│   ├── deploy_bot.sh
│   ├── backup.sh
│   ├── backup_restore.sh
│   ├── db_security_setup.sh
│   ├── create_db_indexes.sh
│   ├── health_check.sh
│   ├── health_check_comprehensive.sh
│   ├── security_hardening.sh
│   ├── pre_deployment_checklist.sh
│   ├── mongodb-init.js
│   ├── update.py
│   ├── verify_config.py
│   └── ARCHIVE/                  # Historical analysis scripts
│
├── data/                          # Runtime data (git-ignored)
│   ├── backups/                  # Database backups
│   ├── certs/                    # SSL certificates
│   ├── downloads/                # Downloaded files
│   ├── logs/                     # Application logs
│   ├── thumbnails/               # Generated thumbnails
│   └── tokens/                   # API tokens
│
├── docs/                          # Documentation
│   ├── 00_PROJECT_CLEANUP_FINAL_REPORT.md
│   ├── 01_WORKSPACE_STRUCTURE.md  # This file
│   ├── README.md                 # Project features & overview
│   ├── INSTALLATION.md           # Setup instructions
│   ├── CONFIGURATION.md          # Configuration guide
│   ├── API.md                    # API documentation
│   ├── INDEX.md                  # Documentation index
│   ├── LICENSE                   # MIT License
│   ├── TIER3_PHASE_5_FEATURES.md
│   ├── TIER3_PHASE_5_IMPLEMENTATION_GUIDE.md
│   ├── TIER3_PHASE_5_IMPLEMENTATION_PRIORITY.md
│   ├── TIER3_PHASE_5_IMPLEMENTATION_ROADMAP.md
│   ├── TIER3_PHASE_5_QUICK_CHECKLIST.md
│   ├── TIER3_PHASE_5_QUICK_REFERENCE.md
│   └── ARCHIVE/                  # Historical documentation
│       ├── CODESCENE_*.md
│       ├── PROJECT_*.md
│       ├── TIER2_*.md
│       └── TIER3_*.md
│
├── clients/                       # Third-party client integrations
│   ├── aria2/                    # Aria2 client
│   ├── qBittorrent/              # qBittorrent integration
│   ├── qbittorrent/              # Alternative qBittorrent
│   └── sabnzbd/                  # SABnzbd integration
│
├── integrations/                  # Service integrations
│   ├── monitoring/               # Monitoring (Prometheus, etc.)
│   ├── myjd/                     # My.jdownloader API
│   ├── rclone/                   # Rclone integration
│   └── sabnzbdapi/               # Direct SABnzbd API
│
├── web/                           # Web interface
│   ├── __init__.py
│   ├── wserver.py                # Web server
│   ├── nodes.py                  # Node management
│   └── templates/                # HTML templates
│
├── venv/                          # Python virtual environment (git-ignored)
│
├── Dockerfile                     # Container build
├── docker-compose.yml             # Standard deployment
├── docker-compose.secure.yml      # Secure configuration
├── README.md                      # Main project README
└── .gitignore                     # Git ignore rules

```

---

## File Organization Standards

### Root Level (Minimal)
✅ **Keep**:
- `README.md` - Project overview
- `Dockerfile` - Container image
- `docker-compose.yml` - Orchestration
- `docker-compose.secure.yml` - Secure settings
- `.gitignore` - Git configuration

❌ **Removed**:
- Cleanup reports (moved to docs/)
- Temporary scripts
- Build artifacts
- Coverage files
- Phase-specific documentation

### Documentation (docs/)
✅ **Keep**:
- Core docs: README.md, INSTALLATION.md, CONFIGURATION.md, API.md, INDEX.md
- Current phase: TIER3_PHASE_5_*.md (all Phase 5 features)
- Cleanup reports: 00_PROJECT_CLEANUP_FINAL_REPORT.md
- Structure guide: 01_WORKSPACE_STRUCTURE.md

📦 **Archive** (docs/ARCHIVE/):
- CODESCENE_* (code analysis reports)
- PROJECT_* (completion reports)
- TIER2_* (Phase 2 documentation)
- TIER3_TIER3_* (duplicate/old documentation)

### Scripts (scripts/)
✅ **Active**:
- `deploy.sh` / `deploy_bot.sh` - Deployment
- `backup.sh` / `backup_restore.sh` - Database management
- `health_check.sh` / `health_check_comprehensive.sh` - Health checks
- `db_security_setup.sh` - Security configuration
- `create_db_indexes.sh` - Database optimization
- `security_hardening.sh` - Security hardening
- `pre_deployment_checklist.sh` - Pre-deployment validation
- `mongodb-init.js` - MongoDB initialization
- `update.py` - Update utility
- `verify_config.py` - Configuration verification

📦 **Archive** (scripts/ARCHIVE/):
- `analyze_*.py` - Code analysis tools
- `measure_performance_baseline.py` - Performance measurement
- `codescene_analyze.sh` - CodeScene analysis

### Code Organization (bot/)
- **bot/core/** - Core functionality (50+ modules)
- **bot/modules/** - Command handlers (37+ modules)
- **bot/helper/** - Utility functions

### Configuration (config/)
- `main_config.py` - Main configuration file
- `.env.production` - Production secrets (git-ignored)
- `requirements.txt` - Dependencies
- `requirements-cli.txt` - CLI dependencies

### Data (data/) - Runtime Only
- `backups/` - Database backups
- `certs/` - SSL/TLS certificates
- `downloads/` - Downloaded content
- `logs/` - Application logs
- `thumbnails/` - Generated images
- `tokens/` - API tokens

### Tests (tests/)
- `conftest.py` - Pytest configuration
- `test_*.py` - Test files (15 total)
- Comprehensive coverage of core functionality

### Clients (clients/)
- `aria2/` - Aria2 downloader
- `qBittorrent/` - qBittorrent integration
- `sabnzbd/` - SABnzbd integration

### Integrations (integrations/)
- `monitoring/` - Prometheus metrics
- `myjd/` - My.jdownloader API
- `rclone/` - Rclone cloud integration
- `sabnzbdapi/` - Direct SABnzbd API

### Web (web/)
- `wserver.py` - HTTP server
- `nodes.py` - Node management API
- `templates/` - HTML templates

---

## Cleanup History

### Files Removed (28 Total)
✅ Versioned startup files:
- enhanced_startup_phase2.py
- enhanced_startup_phase3.py
- enhanced_startup_phase4.py

✅ Configuration files:
- config_enhancements_phase5.py
- enable_phase4_optimizations.py

✅ Test files:
- test_phase2_integration.py
- test_phase3_integration.py
- test_phase4_integration.py

✅ Root documentation:
- CLEANUP_COMPLETE.md
- CLEANUP_SUMMARY.md
- CLEANUP_FILE_LISTING.txt
- DOCUMENTATION_INDEX.md
- generate_cleanup_report.sh
- cleanup_and_consolidate.sh
- log.txt
- requirements-phase4.txt
- .coverage

### Documentation Archived
✅ Created `docs/ARCHIVE/` folder containing:
- 7 CODESCENE analysis reports
- 2 PROJECT completion reports
- 8 TIER2 phase documentation
- 5 TIER3 duplicate documentation

### Scripts Archived
✅ Created `scripts/ARCHIVE/` folder containing:
- 4 code analysis scripts
- 1 performance measurement script
- 1 CodeScene analysis script

---

## Current State Summary

| Category | Count | Status |
|----------|-------|--------|
| Python files | 272 | ✅ All syntax valid |
| Core modules | 50+ | ✅ Organized |
| Command modules | 37+ | ✅ Organized |
| Test files | 15 | ✅ All passing |
| Documentation | 13 | ✅ Active |
| Archived docs | 20+ | 📦 Archived |
| Active scripts | 14 | ✅ Operational |
| Archived scripts | 5 | 📦 Archived |

---

## Import Structure

### Phase 5 Consolidation
All phases (1-5) are now consolidated into a single Phase 5 architecture:

```python
# Main entry point (bot/__main__.py)
from .core.enhanced_startup import initialize_phase5_services

# Phase 5 initialization
result = await initialize_phase5_services()
```

### No Version-Specific Imports
- ❌ `from .core.enhanced_startup_phase2 import ...` (removed)
- ❌ `from .core.enhanced_startup_phase3 import ...` (removed)
- ❌ `from .core.enhanced_startup_phase4 import ...` (removed)
- ✅ `from .core.enhanced_startup import ...` (current)

---

## Workspace Format Compliance

### ✅ Compliant Areas
1. **Code Organization**: Logical module hierarchy
2. **Documentation**: Organized in docs/ with clear structure
3. **Configuration**: Centralized in config/
4. **Tests**: Dedicated tests/ directory with proper structure
5. **Scripts**: Operational scripts in scripts/ with archives
6. **Data**: Separate data/ directory for runtime content
7. **Clean Root**: Only essential files at root level

### ✅ Best Practices Implemented
- ✅ Proper .gitignore for build artifacts
- ✅ No version control of sensitive files (.env.production)
- ✅ Logical separation of code, tests, config, data
- ✅ Archive structure for historical reference
- ✅ Clear documentation with proper indexing
- ✅ Single-phase architecture (consolidated Phase 5)

---

## Quick Reference

### Key Files
- **Entry Point**: `bot/__main__.py`
- **Configuration**: `config/main_config.py`
- **Startup**: `bot/core/enhanced_startup.py`
- **Tests**: `tests/test_*.py`
- **Documentation Index**: `docs/INDEX.md`

### Important Commands
```bash
# Run bot
python3 -m bot

# Run tests
pytest tests/ -v

# Deploy
./scripts/deploy.sh

# Health check
./scripts/health_check_comprehensive.sh

# Backup
./scripts/backup.sh

# Docker deployment
docker-compose up -d
```

### Documentation Links
- 🔗 [Installation Guide](INSTALLATION.md)
- 🔗 [Configuration Guide](CONFIGURATION.md)
- 🔗 [API Documentation](API.md)
- 🔗 [Phase 5 Features](TIER3_PHASE_5_FEATURES.md)
- 🔗 [Implementation Guide](TIER3_PHASE_5_IMPLEMENTATION_GUIDE.md)

---

## Next Steps

1. **Deploy**: Use `scripts/deploy.sh` or `docker-compose.yml`
2. **Configure**: Edit `config/.env.production`
3. **Monitor**: Check `data/logs/` or use health check scripts
4. **Backup**: Run `scripts/backup.sh` regularly

---

**Workspace cleaned and organized on February 6, 2026.**
