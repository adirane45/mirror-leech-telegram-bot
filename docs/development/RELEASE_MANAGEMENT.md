# Release Management & Version Control

This document provides comprehensive guidance on creating releases, managing versions, and deployment procedures.

---

## 📋 Release Process Overview

### Release Types

1. **Alpha** (v3.1.0-alpha.1): Unstable, early features
2. **Beta** (v3.1.0-beta.1): Feature-complete, testing phase
3. **Release Candidate** (v3.1.0-rc.1): Final testing before release
4. **Stable** (v3.1.0): Production-ready release

### Release Workflow

```
Feature Development
    ↓
Create Release Branch (release/v3.2.0)
    ↓
Update Version Numbers
    ↓
Update CHANGELOG.md
    ↓
Create Release Commit
    ↓
Create Git Tag (v3.2.0)
    ↓
Push Tag → GitHub Actions Release Workflow
    ↓
GitHub Release Created + Docker Image Pushed
    ↓
Deploy to Production (optional)
```

---

## 🚀 Creating Your First Release

### Step 1: Prepare Release Branch

```bash
# Update to main and pull latest
git checkout main
git pull origin main

# Create release branch
git checkout -b release/v3.2.0
```

### Step 2: Update Version Information

#### In `pyproject.toml`:
```toml
[project]
version = "3.2.0"  # Update version
```

#### In `deployment/docker/Dockerfile`:
```dockerfile
LABEL version="3.2.0"
```

#### Check current version:
```bash
grep version pyproject.toml
grep "^__version__" src/bot/__init__.py  # if exists
```

### Step 3: Update CHANGELOG.md

Add entry at the top:

```markdown
## [3.2.0] - 2026-02-23

### Added
- Complete CI/CD pipeline setup with 5 workflows
- Professional project restructuring
- Automated health monitoring
- Comprehensive documentation (49 KB)

### Changed
- Improved Docker build performance with layer caching
- Optimized test execution (50-65% faster with parallelization)
- Enhanced type checking with mypy

### Fixed
- Fixed qBittorrent authentication (admin → mltb)
- Updated PYTHONPATH for new src/ structure
- Improved health check endpoint

### Security
- Added Trivy vulnerability scanning
- Implemented Bandit security analysis
- Enabled TruffleHog secrets detection
- Enforced branch protection rules

### Migration
- See RESTRUCTURING_COMPLETE.md for migration details
- Professional structure: docs/PROJECT_STRUCTURE.md
```

### Step 4: Commit Release Changes

```bash
git add -A
git commit -m "release: v3.2.0

Updates to version numbers, documentation, and production deployment configs.
See CHANGELOG.md for detailed changes."
```

### Step 5: Create Release Tag

```bash
# Create annotated tag with message
git tag -a v3.2.0 -m "Release v3.2.0: Production-ready CI/CD pipeline

Features:
- 5 GitHub Actions workflows
- Professional project structure
- Comprehensive CI/CD automation
- Complete documentation

See CHANGELOG.md for full details."

# Or use simple tag:
git tag v3.2.0
```

### Step 6: Push Release

```bash
# Push commits
git push origin release/v3.2.0

# Push tag (triggers GitHub Actions)
git push origin v3.2.0

# Verify tag pushed
git tag -l v3.2.0 --format='%(refname) %(taggerdate)'
```

### Step 7: Monitor GitHub Actions

Go to your repository:
1. Click **Actions** tab
2. Find "Create Release" workflow
3. Watch it execute:
   - ✅ Extract version
   - ✅ Generate release notes
   - ✅ Create GitHub Release
   - ✅ Build Docker image
   - ✅ Push to GHCR
   - ✅ Tag as latest

Expected time: 5-8 minutes

### Step 8: Verify Release

```bash
# Check GitHub Release created
gh release list

# View specific release
gh release view v3.2.0

# Check Docker image pushed
docker pull ghcr.io/YOUR-ORG/mirror-leech-telegram-bot:v3.2.0
```

### Step 9: Merge Release Branch

```bash
# Create PR from release branch
git push origin release/v3.2.0
gh pr create --title "Release: v3.2.0" --body "Production release

See CHANGELOG.md for changes."

# Or merge manually:
git checkout main
git merge --no-ff release/v3.2.0 -m "Merge release/v3.2.0"
git push origin main
```

### Step 10: Cleanup

```bash
# Delete local release branch
git branch -d release/v3.2.0

# Delete remote release branch
git push origin --delete release/v3.2.0
```

---

## 📝 Version Numbering

### Semantic Versioning (SemVer)

Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes
  - Example: v2.0.0 (from v1.x.x)
  - Breaking changes in CLI, config, or API

- **MINOR**: New functionality, backward compatible
  - Example: v3.2.0 (from v3.1.0)
  - New features, optional changes

- **PATCH**: Bug fixes, backward compatible
  - Example: v3.1.5 (from v3.1.0)
  - Security patches, bug fixes

### Pre-release Versions

Append before version:
- **Alpha**: v3.2.0-alpha.1 (unstable, early)
- **Beta**: v3.2.0-beta.1 (feature-complete, testing)
- **Release Candidate**: v3.2.0-rc.1 (final testing)

Example progression:
```
v3.1.0-alpha.1
v3.1.0-alpha.2
v3.1.0-beta.1
v3.1.0-rc.1
v3.1.0           ← Stable release
```

---

## 🔄 Patch Release (Hotfix)

### For Critical Bugs

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/v3.1.5

# Fix the issue
# ... make changes ...

# Update version in pyproject.toml: v3.1.5
# Update CHANGELOG.md

# Commit and tag
git add -A
git commit -m "fix: critical bug in..."
git tag v3.1.5
git push origin hotfix/v3.1.5
git push origin v3.1.5

# Merge back to main AND develop
git checkout main
git merge hotfix/v3.1.5
git push origin main
```

---

## 📊 Release Checklist

Before creating a release, verify:

```
Pre-Release Testing
  ☐ All tests pass: make test
  ☐ Code quality checks pass: make lint
  ☐ Type checking passes: make type-check
  ☐ Docker builds successfully: make build
  ☐ Services start: make up && sleep 10 && make health-check

Documentation
  ☐ CHANGELOG.md updated with all changes
  ☐ README.md reflects current state
  ☐ API documentation updated (if applicable)
  ☐ Migration guide created (if breaking changes)

Version Numbers
  ☐ pyproject.toml updated
  ☐ Version follows SemVer
  ☐ Pre-release suffix correct (alpha/beta/rc)

Git Hygiene
  ☐ Commits are clean and descriptive
  ☐ Release branch created from latest main
  ☐ No uncommitted changes
  ☐ Tags are annotated with message

CI/CD Ready
  ☐ build.yml workflow passes
  ☐ quality.yml workflow passes
  ☐ tests.yml workflow passes
  ☐ GitHub secrets configured (DEPLOY_*)

Post-Release
  ☐ GitHub Release created with notes
  ☐ Docker image pushed to GHCR
  ☐ Release announcement sent
  ☐ Deployment to production (if ready)
```

---

## 🐳 Docker Image Releases

### Image Tags

The following tags are created automatically:

```
ghcr.io/owner/repo:latest              # Latest stable release
ghcr.io/owner/repo:v3.2.0              # Specific version
ghcr.io/owner/repo:main                # Latest from main branch
ghcr.io/owner/repo:develop             # Latest from develop branch
ghcr.io/owner/repo:main-abc12345       # Main with commit SHA
```

### Using Released Images

```bash
# Pull latest stable
docker pull ghcr.io/owner/repo:latest

# Pull specific version
docker pull ghcr.io/owner/repo:v3.2.0

# Pull specific branch
docker pull ghcr.io/owner/repo:main

# Run the image
docker run -d \
  --name mltb-app \
  -p 8060:8060 \
  -e API_KEY=your_key \
  ghcr.io/owner/repo:v3.2.0
```

---

## 🚀 Deployment After Release

### To Production

After release is created and Docker image pushed:

```bash
# Connect to production server
ssh deploy@production.host.com

# Update docker-compose.yml
# Change: ghcr.io/owner/repo:main
# To:     ghcr.io/owner/repo:v3.2.0

# Pull new image
docker pull ghcr.io/owner/repo:v3.2.0

# Stop current services
docker-compose down

# Start new release
docker-compose up -d

# Verify health
curl http://localhost:8060/health
```

### Automated Deployment

If you configured `DEPLOY_KEY`, `DEPLOY_HOST`, `DEPLOY_USER` secrets:

The release.yml workflow will automatically:
1. Build Docker image with version tag
2. Push to GHCR
3. SSH to production server
4. Pull new image
5. Restart services

(via `docker-compose pull && docker-compose up -d`)

---

## 🔍 Monitoring Releases

### Check Release Status

```bash
# List all releases
gh release list

# View specific release
gh release view v3.2.0

# Get release notes
gh release view v3.2.0 --json body

# List Docker images
docker images | grep mirror-leech
gh api repos/owner/repo/packages/container
```

### View Release Artifacts

GitHub Release page shows:
- Release notes (auto-generated from commits)
- Wheel distribution (.whl)
- Source distribution (.tar.gz)
- Attached files

### Docker Image Tracking

```bash
# List images in GHCR
docker search ghcr.io/owner/repo

# Inspect image metadata
docker inspect ghcr.io/owner/repo:v3.2.0

# Check image size
docker images ghcr.io/owner/repo:v3.2.0
```

---

## 📚 CHANGELOG Best Practices

### Format

Use [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [3.2.0] - 2026-02-23

### Added
- New feature 1
- New feature 2

### Changed
- Changed behavior 1
- Changed behavior 2

### Deprecated
- Deprecated feature 1

### Removed
- Removed feature 1

### Fixed
- Bug fix 1
- Bug fix 2

### Security
- Security fix 1
```

### Writing Guidelines

✅ **DO**:
- Use past tense ("Added", "Fixed", "Removed")
- Be specific ("Added new `/health` endpoint" not "Added stuff")
- Group related changes
- Include issue/PR numbers (#123)
- Mention breaking changes prominently

❌ **DON'T**:
- Use technical jargon without explanation
- Write vague entries ("Updates", "Improvements")
- List every commit
- Include internal refactoring unless impactful
- Change old release notes

### Example Entry

```markdown
## [3.2.0] - 2026-02-23

### Added
- Complete CI/CD pipeline with 5 GitHub Actions workflows (#45)
- Health check endpoint at `/health` (#46)
- Professional project structure with src/ directory (#44)
- Comprehensive documentation suite (49 KB)

### Changed
- Improved Docker build performance (50-65% faster) (#47)
- Updated Python dependencies to latest stable
- Enhanced test coverage across 3 Python versions

### Fixed
- Fixed qBittorrent authentication credentials (#48)
- Corrected PYTHONPATH for new project structure (#49)
- Improved health check timeout handling (#50)

### Security
- Added Trivy vulnerability scanning for Docker images (#51)
- Implemented Bandit Python security analysis (#52)
- Enabled TruffleHog secrets detection (#53)

### Migration
- See [RESTRUCTURING_COMPLETE.md](RESTRUCTURING_COMPLETE.md) for migration guide
- New project structure documented in [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
```

---

## 🔗 Release Links

After creating a release, users can reference:

```markdown
# Installation

Install the latest stable release:

```bash
docker pull ghcr.io/owner/mirror-leech-telegram-bot:latest
```

Or install a specific version:

```bash
docker pull ghcr.io/owner/mirror-leech-telegram-bot:v3.2.0
```

See [Releases](https://github.com/owner/mirror-leech-telegram-bot/releases)
for all available versions.
```

---

## ⚡ Quick Release Commands

```bash
# Complete release workflow (manual):
git checkout main && git pull origin main
git checkout -b release/v3.2.0
# ... update files ...
git add -A && git commit -m "release: v3.2.0"
git tag -a v3.2.0 -m "Release v3.2.0"
git push origin release/v3.2.0 v3.2.0
# Watch GitHub Actions for auto-release

# Verify release:
gh release list
gh release view v3.2.0
docker pull ghcr.io/owner/mirror-leech-telegram-bot:v3.2.0

# Cleanup:
git checkout main
git merge --no-ff release/v3.2.0
git push origin main
git branch -d release/v3.2.0
git push origin --delete release/v3.2.0
```

---

## 🆘 Troubleshooting

### Release Workflow Fails

**Problem**: "Release workflow failed in GitHub Actions"

**Solution**:
```bash
# Check logs
gh run list --workflow release.yml --limit 1

# View failed run
gh run view <RUN_ID> --log

# Common fixes:
# 1. Wrong tag format (must be v*.*)
# 2. Missing CHANGELOG.md
# 3. Docker build failed
```

### Docker Image Not Pushed

**Problem**: "Docker image not found in GHCR"

**Solution**:
```bash
# Check GitHub token permissions
gh auth status

# Verify token has write:packages scope
# Go to Settings → Developer settings → Tokens

# Test GHCR login
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Manually push image
docker build -t ghcr.io/owner/repo:v3.2.0 .
docker push ghcr.io/owner/repo:v3.2.0
```

### Tag Already Exists

**Problem**: "Tag v3.2.0 already exists"

**Solution**:
```bash
# Delete and recreate
git tag -d v3.2.0
git push origin :v3.2.0  # Delete remote tag

# Then create new tag
git tag -a v3.2.0 -m "Release v3.2.0"
git push origin v3.2.0
```

---

## 📞 Support

For release questions:
1. Check this guide
2. Review GitHub Actions logs
3. Consult [CI_CD_PIPELINE.md](../CI_CD_PIPELINE.md)
4. See [CI_CD_SETUP_CHECKLIST.md](../CI_CD_SETUP_CHECKLIST.md#troubleshooting-guide)

---

## ✅ Next Release Checklist

For your next release after v3.2.0:

- [ ] Update version in pyproject.toml
- [ ] Add CHANGELOG.md entry
- [ ] Run full test suite: `make test`
- [ ] Create release tag: `git tag v[VERSION]`
- [ ] Push tag: `git push origin v[VERSION]`
- [ ] Monitor GitHub Actions workflow
- [ ] Verify Docker image in GHCR
- [ ] Deploy to production (optional)
- [ ] Announce release to team
