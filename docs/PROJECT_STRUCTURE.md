# Project Structure

This document describes the organization of the Mirror Leech Telegram Bot project.

## Root Directory

```
mirror-leech-telegram-bot/
├── README.md                    # Main project documentation
├── Makefile                     # Build and automation tasks
├── pyproject.toml              # Python project configuration
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── .pre-commit-config.yaml     # Pre-commit hooks configuration
└── requirements-dev.txt        # Development dependencies
```

## Source Code (`/src/`)

Application source code organized by component:
- `/src/api/` - API implementations
- `/src/bot/` - Telegram bot logic
- `/src/web/` - Web interface

## Configuration (`/config/`)

Configuration files and templates:
- `main_config.py` - Main application configuration
- `requirements.txt` - Production dependencies
- `requirements-cli.txt` - CLI tool dependencies

## Documentation (`/docs/`)

All project documentation:
- `/docs/api/` - API documentation
- `/docs/development/` - Development guides
- `/docs/guides/` - User and admin guides
- `/docs/operations/` - Operational procedures
- `/docs/runbooks/` - Incident response guides
- `/docs/project/` - Project reports and status
- `/docs/archived/` - Archived documentation
- `CODE_OF_CONDUCT.md` - Community guidelines
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policies and reporting

## Tests (`/tests/`)

Test suites organized by type:
- `/tests/unit/` - Unit tests for individual components
- `/tests/integration/` - Integration and system tests
- `/tests/performance/` - Performance and load tests
- `/tests/tools/` - Testing utilities and debug scripts
- `conftest.py` - Pytest configuration

## Deployment (`/deployment/`)

Deployment configurations and scripts:
- Dockerfiles (main, alpine, optimized, no-jdownloader)
- Docker Compose files (main, secure, bluegreen, optimized)
- `/deployment/bot/` - Bot deployment configs
- `/deployment/clients/` - Client configurations
- `/deployment/compose/` - Compose templates
- `/deployment/scripts/` - Deployment automation
- `/deployment/web/` - Web deployment configs
- `otel-collector-config.yml` - OpenTelemetry configuration

## Kubernetes (`/kubernetes/`)

Kubernetes manifests and configurations:
- Deployments, services, and config maps
- Secret management
- Monitoring setup
- CronJobs and maintenance tasks

## Scripts (`/scripts/`)

Automation and utility scripts:
- `/scripts/backup/` - Backup and restore scripts
- `/scripts/database/` - Database management
- `/scripts/deploy/` - Deployment automation
- `/scripts/health/` - Health check scripts
- `/scripts/test_scripts/` - Test automation
- `/scripts/ARCHIVE/` - Archived scripts
- `dev_setup.sh` - Development environment setup
- `security_hardening.sh` - Security hardening
- `optimize_performance.sh` - Performance optimization

## Integrations (`/integrations/`)

Third-party service integrations:
- `/integrations/monitoring/` - Monitoring integrations
- `/integrations/myjd/` - MyJDownloader integration
- `/integrations/rclone/` - Rclone integration
- `/integrations/sabnzbdapi/` - SABnzbd integration

## Clients (`/clients/`)

Download client configurations:
- `/clients/aria2/` - Aria2 configuration
- `/clients/qbittorrent/` - qBittorrent configuration
- `/clients/sabnzbd/` - SABnzbd configuration

## Data Directories (`/data/`)

Runtime data (gitignored):
- `/data/backups/` - Backup files
- `/data/certs/` - SSL certificates
- `/data/downloads/` - Downloaded files
- `/data/logs/` - Application logs
- `/data/thumbnails/` - Thumbnail cache
- `/data/tokens/` - Authentication tokens

## Docker (`/docker/`)

Docker-related utilities:
- `setup-secrets.sh` - Docker secrets setup

## Requirements (`/requirements/`)

Python dependencies organized by environment:
- `base.txt` - Base dependencies
- `prod.txt` - Production dependencies
- `dev.txt` - Development dependencies
- `test.txt` - Testing dependencies

## CI/CD (`.github/`)

GitHub Actions workflows and CI/CD configuration

## Metrics and Analysis

- `/.codescene/` - CodeScene analysis
- `/.metrics/` - Project metrics

## Design Principles

1. **Separation of Concerns**: Code, tests, docs, and configs are clearly separated
2. **Logical Grouping**: Related files are grouped together
3. **Clear Hierarchy**: Subdirectories have clear purposes
4. **Documentation**: Each major directory has a README
5. **Consistency**: Naming conventions are consistent throughout
