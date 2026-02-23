# Professional Project Structure Guide

This document explains the reorganized project structure and rationale.

## 📦 Directory Organization

### `src/` - Application Source Code

All application code is organized under `src/` for clean package management:

```
src/
├── bot/                   # Telegram bot implementation
│   ├── __init__.py
│   ├── __main__.py       # Entry point
│   ├── core/             # Core functionality
│   │   ├── config_manager.py
│   │   ├── telegram_manager.py
│   │   ├── redis_manager.py
│   │   ├── metrics.py
│   │   ├── handlers.py   # Message handlers
│   │   ├── torrent_manager.py
│   │   └── ...
│   ├── modules/          # Command handlers
│   │   ├── mirror.py
│   │   ├── leech.py
│   │   ├── search.py
│   │   ├── settings.py
│   │   └── ...
│   ├── helper/           # Utilities & helpers
│   │   ├── ext_utils/
│   │   ├── telegram_helper/
│   │   ├── listeners/
│   │   └── mirror_leech_utils/
│   └── __pycache__/
│
├── web/                   # FastAPI web server
│   ├── __init__.py
│   ├── wserver.py        # Main FastAPI app
│   ├── stream_handler.py # File streaming
│   ├── admin_logs.py     # Admin API
│   ├── nodes.py          # Node management
│   ├── templates/        # HTML templates
│   └── __pycache__/
│
└── api/                   # Future: Dedicated API layer
    ├── __init__.py
    ├── v1/               # API v1 endpoints
    └── schemas/          # Pydantic models
```

**Rationale**: Centralizing code under `src/` is a Python best practice (PEP 517/518) that improves packaging, testing, and import management.

---

### `deployment/` - All Deployment Artifacts

```
deployment/
├── compose/              # Docker Compose variations
│   ├── docker-compose.yml        # Development (default)
│   ├── docker-compose.prod.yml   # Production optimized
│   └── docker-compose.secure.yml # SSL/TLS enabled
│
├── docker/               # Docker build files
│   ├── Dockerfile        # Multi-stage Dockerfile
│   └── .dockerignore
│
├── scripts/              # Deployment automation
│   ├── deploy_blue_green.sh      # Zero-downtime deployment
│   ├── release.sh                # Git tag & release
│   └── health_check.sh
│
├── bluegreen/            # Blue/green setup
│   ├── nginx.conf.template       # Traffic router
│   └── health_check.sh
│
└── otel-collector-config.yml     # OpenTelemetry
```

**Rationale**: Separating deployment from source code enables:
- Clear DevOps/SRE concerns
- Multiple deployment strategies (Docker, K8s, Terraform-ready)
- Easy environment-specific configurations

---

### `config/` - Configuration Management

```
config/
├── main_config.py        # Central config loader
├── .env.production       # Production secrets (git-ignored)
├── .env.development      # Dev environment (git-ignored)
├── requirements.txt      # Runtime dependencies
└── requirements-cli.txt  # CLI tool dependencies
```

**Rationale**: Centralized config with environment-specific files enables:
- Easy secret management
- Multi-environment support
- Single source of truth for configuration

---

### `requirements/` - Dependency Management

```
requirements/
├── base.txt          # Core dependencies (all environments)
├── prod.txt          # Production-only packages
├── dev.txt           # Development tools (testing, linting, docs)
└── test.txt          # Testing-specific packages
```

**Usage**:
```bash
pip install -r requirements/base.txt      # Minimal
pip install -r requirements/prod.txt      # Production
pip install -r requirements/dev.txt       # Full development
```

**Rationale**: Separated dependency files:
- Faster production installations (no test/lint overhead)
- Clear visibility of what's needed for each environment
- Easier to manage version conflicts

---

### `tests/` - Test Suite

```
tests/
├── __init__.py
├── conftest.py                   # Pytest fixtures & config
├── test_api_endpoints.py
├── test_bot_commands.py
├── test_integration.py
└── unit/
    ├── test_config.py
    └── test_utils.py
```

**Rationale**: Maintaining tests separate from source allows:
- Clean separation of concerns
- Easy CI/CD integration
- Clear testing strategy documentation

---

### `docs/` - Documentation

```
docs/
├── README.md                     # Documentation index
├── ARCHITECTURE.md               # System design
├── API_REFERENCE.md              # API documentation
├── INSTALLATION.md               # Setup guide
├── DEPLOYMENT_CHECKLIST.md       # Pre-deployment checks
├── PRODUCTION_DEPLOYMENT_GUIDE.md # Production setup
│
├── runbooks/                     # Operations documentation
│   ├── README.md                 # Operations index
│   ├── app.md                    # Bot application
│   ├── aria2.md                  # Aria2 client
│   ├── qbittorrent.md            # qBittorrent
│   ├── redis.md                  # Redis cache
│   ├── mongodb.md                # Database
│   ├── prometheus.md             # Monitoring
│   ├── grafana.md                # Dashboards
│   ├── security.md               # Security & hardening
│   ├── backup_restore.md         # Backup procedures
│   ├── oncall.md                 # On-call procedures
│   ├── postmortem_template.md    # Incident postmortems
│   └── runbook_template.md       # Runbook template
│
└── ARCHIVE/                      # Deprecated/reference docs
    ├── DEPLOYMENT_SUMMARY.md
    └── ...
```

**Rationale**: Comprehensive documentation:
- Helps new team members onboard quickly
- Runbooks provide operational procedures
- Reduces knowledge silos

---

### `scripts/` - Utility Scripts

```
scripts/
├── deploy.sh                    # Main deployment script
├── backup.sh                    # Backup automation
├── restore.sh                   # Restore from backup
├── health_check.sh              # Health verification
├── health_check_comprehensive.sh # Detailed health check
│
├── deploy/                      # Deployment helpers
├── health/                      # Health check scripts
├── monitoring/                  # Monitoring utilities
│
└── test_scripts/                # Testing utilities
    └── test_integration.sh
```

**Rationale**: Centralized scripts for common operations improve consistency.

---

### `data/` - Runtime Data (Volumes)

```
data/
├── downloads/       # Downloaded files
├── logs/           # Application logs
│   ├── log.txt
│   ├── security-audit.log
│   └── backup.log
├── backups/        # Database backups
├── certs/          # SSL/TLS certificates
├── thumbnails/     # Cached thumbnail images
└── tokens/         # OAuth tokens, sessions
```

**Rationale**: Separating data enables:
- Easy Docker volume mapping
- Clear data persistence strategy
- Simple backup/restore

---

### `integrations/` - External Services

```
integrations/
├── monitoring/      # Prometheus, Grafana configs
├── myjd/           # MyJDownloader integration
├── rclone/         # Rclone cloud storage
├── sabnzbdapi/     # SABnzbd NZB client
└── logging/        # Structured logging setup
```

**Rationale**: Modular integrations allow:
- Optional feature enablement
- Clear dependency management
- Easy swapping of implementations

---

### `clients/` - Download Client Configurations

```
clients/
├── aria2/          # Aria2 configuration
│   └── config/     # aria.conf
├── qbittorrent/    # qBittorrent config
│   └── config/     # qBittorrent.conf
└── sabnzbd/        # SABnzbd configuration
    └── config/     # SABnzbd.ini
```

**Rationale**: Grouped client configs enable:
- Easy container volume mounting
- Clear client dependencies
- Simple multi-client orchestration

---

### `.github/` - GitHub Configuration

```
.github/
├── workflows/
│   ├── ci-cd-pipeline.yml       # CI/CD on push
│   ├── release.yml              # Release on tag
│   └── security-scan.yml        # Security checks
│
└── FUNDING.yml                  # Sponsorship info
```

**Rationale**: GitHub workflows enable:
- Automated testing on PR
- Automated releases on tags
- Security scanning

---

### Root Level Files

```
Makefile
├── Quick development commands
└── Consistent task runners

pyproject.toml
├── Project metadata (PEP 517/518)
├── Build system config
├── Tool configurations (black, isort, pytest)
└── Dependency declarations

.env.example
├── Environment template
└── Documentation of all variables

.gitignore
├── Node modules, venv, .env files
└── IDE/OS generated files

CONTRIBUTING.md
├── Contribution guidelines
└── Development workflow

CHANGELOG.md
├── Version history
└── Breaking changes log

LICENSE
└── GPL-3.0 license text

README.md
└── Project overview & quick start
```

---

## 🎯 Development Workflow with New Structure

### 1. Adding a New Feature

```
1. Create feature branch
   git checkout -b feature/new-feature

2. Make changes in src/
   src/bot/modules/new_feature.py
   tests/test_new_feature.py

3. Test locally
   make test

4. Format code
   make format
   make lint

5. Commit & push
   git commit -m "feat: add new feature"
   git push origin feature/new-feature

6. Create PR
```

### 2. Deployment

```
1. Code review & merge to main

2. Tag release
   git tag v3.2.0

3. GitHub Actions builds & pushes image

4. Deploy with Compose
   docker compose -f deployment/compose/docker-compose.prod.yml up -d

5. Verify health
   make health-check
```

### 3. Troubleshooting

```
1. Check logs
   make logs-app

2. Review runbook
   cat docs/runbooks/app.md

3. Check health endpoints
   curl http://localhost:8060/health

4. Inspect containers
   docker compose ps
   docker logs mltb-app
```

---

## 📋 Migration Checklist

Your workspace has been restructured with:

- ✅ **src/** - Application code organized
- ✅ **deployment/** - All deployment files centralized
- ✅ **requirements/** - Separated dependency files
- ✅ **Makefile** - Developer convenience commands
- ✅ **pyproject.toml** - Professional project metadata
- ✅ **.env.example** - Configuration template
- ✅ **CONTRIBUTING.md** - Contribution guidelines
- ✅ **docs/runbooks/** - Operations documentation

### Next Steps

1. **Review structure**: `tree -L 2 -I '__pycache__'`
2. **Test imports**: `python -c "import sys; sys.path.insert(0, 'src'); from bot import LOGGER"`
3. **Run tests**: `make test`
4. **Update CI/CD**: Review `.github/workflows/`
5. **Update documentation**: Link new structure in docs
6. **Commit changes**: `git add -A && git commit -m "refactor: reorganize to professional structure"`

---

## 🔄 Import Path Updates

Old imports:
```python
from bot.core.config_manager import Config
from web.wserver import app
```

Are NOW:
```python
# Imports should still work the same because src/bot/ exists
# If issues, add to PYTHONPATH or sys.path:
import sys
sys.path.insert(0, 'src')
from bot.core.config_manager import Config
```

---

## 📚 Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PEP 517 - Build System](https://peps.python.org/pep-0517/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**This project is now structured as a professional, maintainable Python application!** 🎉
