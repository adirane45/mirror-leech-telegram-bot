# Release Workflow Verification Guide (v3.2.1)

## What We Released

**Version**: 3.2.1
**Release Type**: Patch (bug fixes + CI/CD improvements)
**Date**: 2026-02-23

### Release Contents

#### Code Changes
- ✅ Professional project restructuring (completed in v3.2.0)
- ✅ CI/CD pipeline implementation (5 workflows)
- ✅ Workflow alignment to `master` branch
- ✅ Runtime artifact exclusions (.gitignore updates)

#### New in This Release
- ✅ Build workflow: Smart Docker building with code quality checks
- ✅ Quality workflow: Lint, format, type checking
- ✅ Tests workflow: Python 3.10, 3.11, 3.12 matrix
- ✅ Health-check workflow: Scheduled service monitoring
- ✅ Release workflow: Automated GitHub releases + Docker push

#### Documentation Added
- ✅ CI_CD_IMPLEMENTATION_SUMMARY.md (13 KB)
- ✅ CI_CD_SETUP_CHECKLIST.md (12 KB)
- ✅ CI_CD_PIPELINE.md (8.4 KB)
- ✅ CI_CD_ARCHITECTURE.md (16 KB)
- ✅ Updated PROJECT_STRUCTURE.md for new workflows

### Release Artifacts

#### Expected Files (dist/)
```
dist/
├── mirror_leech_telegram_bot-3.2.1.tar.gz    (563 KB - source distribution)
└── mirror_leech_telegram_bot-3.2.1-py3-none-any.whl  (639 KB - wheel)
```

#### Docker Image Tags
```
ghcr.io/adirane45/mirror-leech-telegram-bot:v3.2.1
ghcr.io/adirane45/mirror-leech-telegram-bot:latest
ghcr.io/adirane45/mirror-leech-telegram-bot:3.2.1
```

---

## How to Verify Release Workflow

### Option 1: Check GitHub Release Page
**URL**: https://github.com/adirane45/mirror-leech-telegram-bot/releases

Look for `v3.2.1` with:
- ✅ Release title: "v3.2.1" or similar
- ✅ Release notes with CI/CD improvements
- ✅ Artifacts section showing wheel + sdist
- ✅ Date and author information

### Option 2: Check Container Registry
**URL**: https://github.com/adirane45/mirror-leech-telegram-bot/pkgs/container

Look for:
- ✅ Image: `adirane45/mirror-leech-telegram-bot`
- ✅ Tags: `v3.2.1`, `latest`, `3.2.1`
- ✅ Pushed by: GitHub Actions (automated)
- ✅ Digest: sha256:... (immutable)

### Option 3: Pull and Test Docker Image
```bash
# Login if needed (private registry)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull the image
docker pull ghcr.io/adirane45/mirror-leech-telegram-bot:v3.2.1

# Check image
docker inspect ghcr.io/adirane45/mirror-leech-telegram-bot:v3.2.1

# Run container
docker run --rm \
  -e BOT_TOKEN="your_token" \
  -e TELEGRAM_API="your_api" \
  ghcr.io/adirane45/mirror-leech-telegram-bot:v3.2.1 \
  python -c "import sys; print(f'Python {sys.version}')"
```

### Option 4: Use GitHub CLI
```bash
# List releases
gh release list --repo adirane45/mirror-leech-telegram-bot

# View v3.2.1 release
gh release view v3.2.1 --repo adirane45/mirror-leech-telegram-bot

# Download artifacts
gh release download v3.2.1 \
  --repo adirane45/mirror-leech-telegram-bot \
  --dir ./release-artifacts

# List downloaded files
ls -lh release-artifacts/
```

---

## Release Workflow Output

### Expected Workflow Steps
```
✅ Checkout repository (full history)
✅ Extract version from tag (v3.2.1 → 3.2.1)
✅ Generate release notes from commits
✅ Build Python distributions
   ├─ setup.py discovered from pyproject.toml
   ├─ Building sdist: mirror_leech_telegram_bot-3.2.1.tar.gz
   └─ Building wheel: mirror_leech_telegram_bot-3.2.1-py3-none-any.whl
✅ Create GitHub Release
   ├─ Title: v3.2.1
   ├─ Body: Auto-generated from commits
   ├─ Artifacts: Both sdist and wheel
   └─ Draft: false, Pre-release: false
✅ Setup Docker Buildx
✅ Login to GitHub Container Registry
✅ Build and push Docker image
   ├─ Tag: ghcr.io/adirane45/mirror-leech-telegram-bot:v3.2.1
   ├─ Tag: ghcr.io/adirane45/mirror-leech-telegram-bot:latest
   └─ Registry: ghcr.io (GitHub Container Registry)
```

### Success Indicators
- ✅ Release page shows v3.2.1
- ✅ Artifacts (wheel + sdist) available for download
- ✅ Docker image pushed with correct tags
- ✅ Workflow completed without errors
- ✅ No manual intervention required

---

## Verifying Changelog Integration

### Check CHANGELOG.md
```bash
head -20 CHANGELOG.md
```

Should show:
```markdown
## 2026-02-23
- Added GitHub Actions workflows for build, quality, tests, release, and health checks.
- Added CI/CD documentation: setup checklist, pipeline reference, architecture, and summary.
- Updated project structure documentation to reflect CI/CD workflows and docs.

## 2026-02-20
- Added Telegram file cache manager...
```

### Check pyproject.toml Version
```bash
grep "^version" pyproject.toml
```

Should show:
```toml
version = "3.2.1"
```

---

## Install from Release

### From PyPI (if published)
```bash
pip install mirror-leech-telegram-bot==3.2.1
```

### From GitHub Release (wheel)
```bash
cd release-artifacts
pip install mirror_leech_telegram_bot-3.2.1-py3-none-any.whl
```

### From GitHub Release (source)
```bash
cd release-artifacts
pip install mirror_leech_telegram_bot-3.2.1.tar.gz
```

### From Docker
```bash
docker run ghcr.io/adirane45/mirror-leech-telegram-bot:v3.2.1 --version
```

---

## Troubleshooting Release Issues

### Release Doesn't Appear
1. **Check tag format**: Must match `v*` (e.g., `v3.2.1`)
   ```bash
   git tag -l | grep v3.2.1
   ```

2. **Verify tag pushed**:
   ```bash
   git ls-remote origin refs/tags/v3.2.1
   ```

3. **Check workflow status**: https://github.com/adirane45/mirror-leech-telegram-bot/actions
   - Look for "Create Release" workflow
   - Check logs for errors

### Docker Image Not Found
1. **Verify push succeeded**:
   ```bash
   docker inspect ghcr.io/adirane45/mirror-leech-telegram-bot:v3.2.1
   ```

2. **Check registry permissions**: Settings → Packages → Change Package Visibility

3. **Check GitHub token**: Must have `write:packages` scope

### Artifacts Missing
1. **Verify build tools installed**: `python -m build`
2. **Check setuptools version**: `pip install --upgrade setuptools wheel build`
3. **Review workflow logs**: Click workflow run → expand "Build distributions" step

---

## Next Steps After Release

1. ✅ **Communicate**: Update team about v3.2.1 release
2. ⏳ **Test in production**: Deploy from v3.2.1 image
3. ⏳ **Monitor**: Watch health checks and metrics
4. ⏳ **Plan v3.3.0**: New minor features/improvements

---

## Rollback Instructions (if needed)

### To Previous Version
```bash
# Pull previous image
docker pull ghcr.io/adirane45/mirror-leech-telegram-bot:v3.2.0

# Or from source
git checkout v3.2.0
pip install -e .
```

### To Previous Release
```bash
# Using GitHub release
gh release download v3.2.0 \
  --repo adirane45/mirror-leech-telegram-bot
```

---

**Status**: ⏳ Awaiting GitHub to process release workflow
**Release URL**: https://github.com/adirane45/mirror-leech-telegram-bot/releases/tag/v3.2.1
**Container Registry**: https://github.com/adirane45/mirror-leech-telegram-bot/pkgs/container

---

*For updates, check GitHub Actions tab or release page.*
