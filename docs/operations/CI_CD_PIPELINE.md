# CI/CD Pipeline Documentation

## Overview

This project uses GitHub Actions for continuous integration and continuous deployment (CI/CD). The workflows automate testing, code quality checks, security scanning, and release management.

## Workflows

### 1. **Build & Push Docker Image** (`.github/workflows/build.yml`)
Runs on every push to `main`/`develop` and PRs. Performs:
- ✅ Code quality checks (linting, formatting, type checking)
- 🧪 Unit tests with coverage reporting
- 🐳 Docker image build and push to GitHub Container Registry
- 🔒 Security scanning with Trivy
- 🚀 (Optional) Auto-deployment to production

**Triggers:**
- Push to `main`, `develop`
- Pull requests (code review)
- Changes to `src/`, `deployment/docker/`, or workflow file

**Outputs:**
- Docker image: `ghcr.io/[owner]/mirror-leech-telegram-bot:[branch/tag]`
- Coverage reports uploaded to Codecov
- Security scan results in GitHub Security tab

---

### 2. **Code Quality Checks** (`.github/workflows/quality.yml`)
Comprehensive code quality analysis:
- 📝 **Linting**: flake8, pylint
- 📐 **Formatting**: black, isort
- 🔍 **Type Checking**: mypy
- 🔒 **Security**: bandit, TruffleHog (secrets detection)

**Runs on:** Push to `main`/`develop`, PRs
**Status:** Non-blocking (warnings allowed, fails only on critical errors)

---

### 3. **Tests** (`.github/workflows/tests.yml`)
Comprehensive test suite:
- 🧪 **Unit Tests**: pytest across Python 3.10, 3.11, 3.12
- 📊 **Coverage Reporting**: HTML reports, Codecov uploads
- 🔌 **Integration Tests**: Docker Compose services validation
- 🗄️ **Service Testing**: Redis, MongoDB connectivity

**Services Started:**
- Redis (port 6379)
- MongoDB (port 27017)
- Docker Compose services
- FastAPI app (port 8060)

**Outputs:**
- JUnit XML test results
- HTML coverage reports
- Codecov badge integration

---

### 4. **Health Check** (`.github/workflows/health-check.yml`)
Scheduled health verification:
- 🔍 Service availability checks
- ⚕️ Endpoint health monitoring
- 📋 Log collection on failures
- 🔔 Notifications on issues

**Schedule:** Every 6 hours + manual trigger
**Services Verified:**
- FastAPI (/health endpoint)
- Redis
- Prometheus

---

### 5. **Create Release** (`.github/workflows/release.yml`)
Automated release process on version tags:
- 📦 Build distributions (wheel/sdist)
- 🏷️ Create GitHub Release with auto-generated changelog
- 🐳 Push Docker image with version tag
- 📝 Update CHANGELOG.md

**Triggers:** `git tag v*` (e.g., `v3.2.0`, `v3.2.0-beta.1`)

**Outputs:**
- GitHub Release with artifacts
- Docker image: `ghcr.io/[owner]/mirror-leech-telegram-bot:v3.2.0`
- Automatic pre-release flag for alpha/beta versions

---

## Environment Variables & Secrets

### GitHub Secrets Required

For deployment to production:

```
DEPLOY_KEY        # SSH private key for production server
DEPLOY_HOST       # Production server hostname
DEPLOY_USER       # SSH username for deployment
```

### Workflow Environment Variables

Set automatically by GitHub Actions:
- `REGISTRY`: `ghcr.io` (GitHub Container Registry)
- `IMAGE_NAME`: Auto-derived from repository name
- `PYTHON_VERSION`: `3.11` (primary), `3.10`, `3.12` (in matrix)

---

## Setup Instructions

### 1. Enable GitHub Container Registry

1. Go to repository **Settings** → **Packages**
2. Enable "Container Registry"
3. Create personal access token (PAT) with `write:packages` scope

### 2. Configure Secrets

```bash
# Add to GitHub repository secrets:
gh secret set DEPLOY_KEY < ~/.ssh/id_rsa
gh secret set DEPLOY_HOST -b "prod.example.com"
gh secret set DEPLOY_USER -b "deploy"
```

### 3. Create Branch Protection Rules

**Settings** → **Branches** → **Add rule** for `main`:

- ✅ Require PR reviews (1 approver)
- ✅ Require status checks:
  - `lint` (Code Quality Checks)
  - `typecheck` (Code Quality Checks)
  - `security` (Code Quality Checks)
  - `test` (Tests)
  - `build` (Build & Push)
- ✅ Require branches to be up to date
- ✅ Dismiss stale reviews

### 4. Create Deployment Environment

**Settings** → **Environments** → **New environment** → `production`

Configure:
- Protection rules (e.g., required reviewers)
- Deployment branches: `main` only
- Production secrets: `DEPLOY_KEY`, `DEPLOY_HOST`, `DEPLOY_USER`

---

## Usage Examples

### Running Tests Locally

```bash
# All tests
make test

# Specific test file
pytest tests/test_api_endpoints.py -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Linting & Formatting

```bash
# Check code quality
make lint

# Auto-format code
make format

# Type check
mypy src/ --ignore-missing-imports
```

### Build Docker Image

```bash
# Build locally
docker build -f deployment/docker/Dockerfile -t mltb:dev .

# Pre-push build (runs all checks)
make build
```

### Release New Version

```bash
# Create and push tag
git tag v3.2.0
git push origin v3.2.0

# Workflow automatically:
# ✅ Runs all tests
# ✅ Builds Docker image
# ✅ Creates GitHub release
# ✅ Pushes to registry with version tag
```

---

## Monitoring & Debugging

### View Workflow Runs

**GitHub UI:** Actions tab → Select workflow → View runs

```bash
# CLI
gh run list --limit 10
gh run view [RUN_ID] --log
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Build fails with import error | Check `PYTHONPATH=/app/src` in Dockerfile |
| Docker push fails | Verify PAT has `write:packages` scope |
| Test flakiness | Check Redis/MongoDB service status |
| Coverage drop | Run `make coverage-report` locally |

---

## Performance Optimization

### Build Cache

- Docker uses registry cache: `ghcr.io/[owner]/[repo]:buildcache`
- Python dependencies cached via `actions/setup-python`
- Multi-stage build reduces final image size

### Parallel Jobs

- Lint, type-check, and security run in parallel
- Tests matrix across 3 Python versions simultaneously
- Build waits for tests (prevents pushing broken images)

---

## Security Best Practices

1. **Secrets Management**
   - Rotate `DEPLOY_KEY` annually
   - Use fine-grained PATs (limit to specific packages)
   - Never commit secrets to repo

2. **Image Scanning**
   - Trivy scans every built image
   - Results visible in Security tab
   - Fails on critical vulnerabilities (configurable)

3. **Code Scanning**
   - TruffleHog detects leaked credentials
   - Bandit identifies security anti-patterns
   - Results integrated into PR checks

4. **Branch Protection**
   - All PRs require passing checks
   - One manual review required
   - Enforced on `main` branch

---

## Scheduled Jobs

| Workflow | Schedule | Purpose |
|----------|----------|---------|
| Health Check | Every 6 hours | Verify services stability |
| (Optional) Nightly Tests | 2 AM UTC | Extended test suite |
| (Optional) Dependency Update | Weekly | Check for library updates |

---

## Integration with Development Workflow

### Local Development

1. **Make changes in feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Test locally**
   ```bash
   make lint format test
   ```

3. **Push and create PR**
   ```bash
   git push origin feature/my-feature
   ```

4. **Workflows automatically run:**
   - ✅ Code quality checks
   - ✅ Tests on 3 Python versions
   - ✅ Docker build
   - ✅ Security scan

5. **Review PR & merge to main**

6. **Production deployment** (auto for `main`):
   - ✅ Image pushed to registry with `latest` tag
   - ✅ (Optional) Auto-deploy via SSH

### Release Process

```bash
# On main branch
git tag v3.2.0
git push origin v3.2.0

# Workflow creates:
✅ GitHub Release
✅ Docker image tagged as v3.2.0
✅ Updated CHANGELOG
```

---

## Troubleshooting

### "Workflow file not found"
- Ensure YAML files are in `.github/workflows/`
- Check YAML syntax: `yamllint .github/workflows/`

### "Docker push fails with 403"
- Verify GitHub token has `write:packages` scope
- Check repository settings allow Actions

### "Tests timeout on Redis/MongoDB"
- Services may need more startup time
- Increase `timeout-minutes` in workflow
- Check Docker daemon availability

### "Build cache not working"
- First build always takes longer
- Enable "buildcache" type in Docker metadata
- Subsequent builds will be faster

---

## See Also

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Documentation](https://docs.github.com/en/actions/publishing-packages/publishing-docker-images)
- [Codecov Integration](https://codecov.io)
- [Trivy Security Scanner](https://aquasecurity.github.io/trivy/)
