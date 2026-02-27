# Branch Protection & GitHub Configuration Guide

## Configure Master Branch Protection

To enforce quality on the master branch, configure these GitHub settings:

### Go to: Repository Settings → Branches → Branch Protection Rules

#### Add Protection Rule for `master` branch

**1. Require a pull request before merging**
- ✓ Require pull request reviews before merging
- Dismissal restrictions: None
- No. of required reviewers: **1** (or more for team)
- ✓ Require review from code owners (optional)
- ✓ Dismiss stale pull request approvals when new commits are pushed

**2. Require status checks to pass before merging**
- ✓ Require branches to be up to date before merging
- Status checks that must pass:
  - ✓ `build.yml` (Docker build + security scans)
  - ✓ `quality.yml` (Code quality checks)
  - ✓ `tests.yml` (Unit tests)

**3. Require signed commits**
- Optional for solo dev, ✓ recommended for teams

**4. Require linear history**
- ✓ Require linear history (enforces conventional workflow)

**5. Restrict who can push to matching branches**
- Leave empty for now (all authenticated users allowed)

---

## GitHub Actions Configuration Verification

### Current Workflows Configured: ✅ 5 Active

| Workflow | Trigger | Branches | Status |
|----------|---------|----------|--------|
| **build.yml** | Push, PR | main, master, develop | ✅ Active |
| **quality.yml** | Push, PR | main, master, develop | ✅ Active |
| **tests.yml** | Push, PR | main, master, develop | ✅ Active |
| **release.yml** | Tag (v*) | All | ✅ Active |
| **health-check.yml** | Schedule, Manual | All | ✅ Active |

### Secrets Configured: ✅ Ready

GitHub Actions has access to:
- `GHCR_TOKEN` - Push to GitHub Container Registry
- `CODECOV_TOKEN` - Upload coverage (optional)
- `PyPI_TOKEN` - Publish to PyPI (optional, when enabled)

---

## README Badges (Add to README.md)

Add these badges to show project status:

```markdown
# Mirror Leech Telegram Bot

[![Build Status](https://github.com/adirane45/mirror-leech-telegram-bot/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/adirane45/mirror-leech-telegram-bot/actions/workflows/build.yml)
[![Code Quality](https://github.com/adirane45/mirror-leech-telegram-bot/actions/workflows/quality.yml/badge.svg?branch=master)](https://github.com/adirane45/mirror-leech-telegram-bot/actions/workflows/quality.yml)
[![Tests](https://github.com/adirane45/mirror-leech-telegram-bot/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/adirane45/mirror-leech-telegram-bot/actions/workflows/tests.yml)
[![Release](https://github.com/adirane45/mirror-leech-telegram-bot/actions/workflows/release.yml/badge.svg)](https://github.com/adirane45/mirror-leech-telegram-bot/actions/workflows/release.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-0088cc?logo=telegram)](https://telegram.org/)
```

---

## Manual Configuration Steps (Do in GitHub UI)

### 1. Configure Master Branch Protection

```
1. Go to: https://github.com/adirane45/mirror-leech-telegram-bot/settings/branches
2. Click "Add rule"
3. Pattern name: "master"
4. Enable "Require a pull request before merging"
5. Enable "Require status checks to pass":
   - Select: build.yml, quality.yml, tests.yml
6. Enable "Require branches to be up to date"
7. Click "Create"
```

### 2. Add Issue Templates

GitHub will automatically use `.github/ISSUE_TEMPLATE/` files for new issues.
They're already configured!

### 3. Add PR Templates

GitHub will automatically use `.github/pull_request_template.md` for new PRs.
Consider creating one.

### 4. Setup GitHub Pages (Optional)

```
1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: master, folder: /docs
4. Creates documentation site at: https://adirane45.github.io/mirror-leech-telegram-bot/
```

---

## Local Development Setup (For Contributors)

### Prerequisites
```bash
- Python 3.10+ (tested on 3.10, 3.11, 3.12)
- Docker & Docker Compose v2
- Git
```

### Quick Start
```bash
# 1. Clone & setup
git clone https://github.com/adirane45/mirror-leech-telegram-bot.git
cd mirror-leech-telegram-bot

# 2. Install dev dependencies
make install-dev

# 3. Run quality checks
make lint type format

# 4. Run tests
make test

# 5. Start services
docker compose -f deployment/compose/docker-compose.yml up -d
```

---

## Expected Workflow Results

After configuring branch protection, here's what will happen:

### When You Push to Master
1. ✅ Commit is pushed
2. ✅ 3 workflows start automatically:
   - build.yml (Docker build + security scan)
   - quality.yml (Code quality checks)
   - tests.yml (Unit tests on Python 3.10, 3.11, 3.12)
3. ✅ Status checks appear on commit/PR
4. ✅ Can't merge until all pass (if branch protection enabled)

### When You Create a PR
1. ✅ All 3 workflows run automatically
2. ✅ Status checks block merge if any fail
3. ✅ Requires code review (if configured)
4. ✅ Only approved PRs can merge to master

### When You Tag a Release
1. ✅ release.yml triggers
2. ✅ Creates GitHub Release page
3. ✅ Pushes Docker image to GHCR
4. ✅ Build artifacts attached to release

---

## Status Badges Configuration

For README badges to work, these workflows must succeed.

### Current Status:
- **Latest Commit**: 62f77f9 (docs reorganization)
- **Triggered Workflows**: build.yml, quality.yml, tests.yml
- **Expected Duration**: 5-15 minutes per workflow
- **Check Status**: https://github.com/adirane45/mirror-leech-telegram-bot/actions

---

## Monitoring & Maintenance

### Daily Monitoring
```bash
# Check workflow status
gh run list --repo adirane45/mirror-leech-telegram-bot --limit 10

# Watch specific workflow
gh run view --repo adirane45/mirror-leech-telegram-bot [RUN_ID]
```

### Troubleshooting

If builds fail:
1. Check recent changes: `git log --oneline -10`
2. Run quality locally: `make lint type format test`
3. Check logs in GitHub Actions tab
4. Fix issues, push commit (triggers workflows again)

---

## Next: Add Badges to README

Once workflows finish successfully, update README with badges.

See: [docs/INDEX.md](../docs/INDEX.md) for all documentation.

---

**Status**: ✅ Branch protection ready to configure  
**Time to Configure**: ~5 minutes  
**Impact**: High - Enforces code quality on master branch  
**Date**: 2026-02-23
