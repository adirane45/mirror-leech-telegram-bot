# CI/CD Pipeline Setup Checklist

This checklist guides you through setting up the complete CI/CD pipeline for this project.

## ✅ Phase 1: Repository Setup (5 minutes)

- [ ] Repository is public OR GitHub Actions enabled in Settings → Actions
- [ ] Branch protection enabled for `main` branch
- [ ] `.github/workflows/` directory exists with all `.yml` files
- [ ] YAML syntax is valid (no formatting errors)

**Verify:**
```bash
# Check workflows exist
ls -la .github/workflows/

# Validate YAML (optional, requires yamllint)
yamllint .github/workflows/
```

---

## ✅ Phase 2: GitHub Container Registry Setup (5 minutes)

### Enable Container Registry
1. Go to repository **Settings**
2. Scroll to **Code, planning, and automation** section
3. Click **Packages and publishing**
4. Ensure "Container Registry" is visible and enabled

### Create Personal Access Token (PAT)
1. Go to GitHub **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **Generate new token**
3. Name: `CI_CD_DEPLOY` or similar
4. Scopes required:
   - ✅ `write:packages` (push Docker images)
   - ✅ `read:packages` (pull Docker images)
   - ✅ `repo` (access repository)
5. Click **Generate** and copy token immediately

### Test Container Registry Access
```bash
# Login to GHCR with your token
echo $GHCR_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Test push (replace USERNAME and REPO)
docker build -f deployment/docker/Dockerfile -t ghcr.io/USERNAME/REPO:test .
docker push ghcr.io/USERNAME/REPO:test
```

---

## ✅ Phase 3: GitHub Secrets Configuration (5 minutes)

### For Build Workflow (Required)
The build workflow uses GitHub's automatic `GITHUB_TOKEN` - no manual setup needed!

**Verify automatic token:**
- Go to repository **Settings** → **Actions** → **General**
- Check "Workflow permissions"
- ✅ "Read and write permissions" enabled
- ✅ "Allow GitHub Actions to create and approve pull requests" (optional)

### For Deployment to Production (Optional)
Skip this if you don't need auto-deployment.

1. Generate SSH key on your production server:
   ```bash
   ssh-keygen -t ed25519 -f deploy_key -N ""
   # Or use existing key: ~/.ssh/id_rsa
   ```

2. Add public key to production server:
   ```bash
   cat deploy_key.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

3. Add secrets to GitHub repository:
   - Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   
   Create these secrets:
   | Secret Name | Value | Example |
   |------------|-------|---------|
   | `DEPLOY_KEY` | Private SSH key content | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
   | `DEPLOY_HOST` | Production server hostname | `prod.example.com` |
   | `DEPLOY_USER` | SSH username | `deploy` or `ubuntu` |

   ```bash
   # CLI method (using gh)
   gh secret set DEPLOY_KEY < deploy_key
   gh secret set DEPLOY_HOST -b "prod.example.com"
   gh secret set DEPLOY_USER -b "deploy"
   ```

---

## ✅ Phase 4: Branch Protection Rules (5 minutes)

### Setup Main Branch Protection
1. Go to **Settings** → **Branches** → **Add rule**
2. Branch name pattern: `main`
3. Enable these protections:

   - [ ] **Require a pull request before merging**
     - ✅ Require approval from 1 reviewer
     - ✅ Require approval of the most recent reviewers
     - ✅ Dismiss stale pull request approvals when new commits are pushed

   - [ ] **Require status checks to pass before merging**
     - Search for and select:
       - `build` (Build & Push Docker Image)
       - `lint` (Code Quality Checks)
       - `typecheck` (Code Quality Checks)
       - `security` (Code Quality Checks)
       - `test` (Tests - all 3 Python versions)
     
   - [ ] **Require branches to be up to date before merging**
   
   - [ ] **Require code reviews**
     - ✅ Require 1 approvals
   
   - [ ] **Require conversation resolution before merging**
   
   - [ ] **Restrict who can push to matching branches** (optional for admins)
   
   - [ ] **Allow force pushes** → ❌ Do not allow

4. Click **Create**

**Verify:**
```bash
# CLI - list branch rules
gh repo rules list --branch main
```

---

## ✅ Phase 5: Deployment Environment Setup (Optional, 5 minutes)

Skip if not deploying to production automatically.

### Create Production Environment
1. Go to **Settings** → **Environments** → **New environment**
2. Name: `production`
3. Add protection rules:

   - [ ] **Required reviewers**: Add your team members
   - [ ] **Deployment branches**: Only `main`
   - [ ] **Environment secrets**: Same as above
     - `DEPLOY_KEY`
     - `DEPLOY_HOST`
     - `DEPLOY_USER`

4. Click **Create**

---

## ✅ Phase 6: Local Development Setup (10 minutes)

### Install Dependencies
```bash
# Install Python development requirements
make install-dev

# Or manually
pip install -r requirements/dev.txt
```

### Test Workflow Locally
```bash
# Run linting
make lint
# or
flake8 src/ --max-line-length=120
pylint src/ --disable=duplicate-code

# Run type checking
mypy src/ --ignore-missing-imports

# Format code
make format
# or
black src/ tests/
isort src/ tests/

# Run all tests
make test
# or
pytest tests/ -v --cov=src

# Check build
make build-image
# or
docker build -f deployment/docker/Dockerfile --no-cache -t mltb:test .
```

---

## ✅ Phase 7: Verify Pipeline Execution (10 minutes)

### Trigger First Build
```bash
# Create feature branch and PR
git checkout -b feature/ci-cd-test
echo "# Test CI/CD" >> README.md
git add README.md
git commit -m "test: trigger ci pipeline"
git push origin feature/ci-cd-test

# Create PR on GitHub
# Or use: gh pr create --title "Test CI/CD"
```

### Monitor Workflow
1. Go to repository **Actions** tab
2. Watch workflow execution:
   - ✅ `Build & Push Docker Image` starts
   - ✅ Sub-jobs run in parallel: `lint`, `typecheck`
   - ✅ `test` job waits for sub-jobs
   - ✅ `build` job runs Docker build
   - ✅ `security` job scans image

3. Check for any failures:
   ```bash
   gh run list --branch feature/ci-cd-test
   gh run view <RUN_ID> --log
   ```

### Expected Results
- ✅ All jobs pass (green checkmarks)
- ✅ Code coverage report generated
- ✅ Docker image pushed (if push branch)
- ✅ Security scan completes
- ✅ Branch protection check passes

---

## ✅ Phase 8: Test Release Process (5 minutes)

### Create Test Release Tag
```bash
# Ensure all tests passing first
git checkout main
git pull origin main

# Create version tag
git tag v3.2.0-test
git push origin v3.2.0-test

# Alternative with gh CLI
gh release create v3.2.0-test --generate-notes
```

### Verify Release Workflow
1. Go to **Actions** → `Create Release` workflow
2. Watch for:
   - ✅ Checkout with full history
   - ✅ Python setup
   - ✅ GitHub Release creation
   - ✅ Docker image build and push
   - ✅ Image tagged with version

3. Check releases:
   ```bash
   gh release list
   gh release view v3.2.0-test
   ```

4. Verify Docker image:
   ```bash
   docker pull ghcr.io/USERNAME/REPO:v3.2.0-test
   ```

### Cleanup
```bash
# Delete test tag and release
git tag -d v3.2.0-test
git push origin --delete v3.2.0-test
gh release delete v3.2.0-test
```

---

## ✅ Phase 9: Configure Scheduled Jobs (5 minutes)

### Daily Health Checks
The health check workflow runs automatically every 6 hours.

**To customize:**
1. Edit `.github/workflows/health-check.yml`
2. Change `cron: '0 */6 * * *'` to desired schedule
   - `0 2 * * *` = Daily at 2 AM UTC
   - `0 */4 * * *` = Every 4 hours
   - [Cron syntax reference](https://crontab.guru/)

---

## ✅ Phase 10: Team Communication (5 minutes)

### Update Team
Inform your team about:
1. **New development workflow**:
   ```markdown
   - Create feature branch: `git checkout -b feature/NAME`
   - Make changes and commit: `git commit -m "feat: description"`
   - Run local tests: `make test && make lint`
   - Push and create PR: `git push origin feature/NAME`
   - Await CI/CD checks and review
   - Merge when approved and all checks pass
   ```

2. **Release process**:
   ```markdown
   - Create version tag: `git tag v3.2.0`
   - Push tag: `git push origin v3.2.0`
   - GitHub Actions automatically creates release
   - Docker image pushed to registry
   ```

3. **Troubleshooting**:
   - Check Actions tab for failures
   - Review logs: `gh run view <RUN_ID> --log`
   - Common issues are documented in CI_CD_PIPELINE.md

---

## ✅ Troubleshooting Guide

### Problem: "Workflow not found"
**Solution:**
```bash
# Verify YAML files exist
ls -la .github/workflows/

# Check YAML syntax
yamllint .github/workflows/ || echo "Install: pip install yamllint"

# Verify workflow is on the branch
git branch -a
git show origin/main:.github/workflows/build.yml
```

---

### Problem: "Docker push fails with 403"
**Solution:**
```bash
# Verify GitHub token has correct permissions
gh auth status

# Test container registry access directly
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Re-create token if needed with write:packages scope
```

---

### Problem: "Tests timeout or fail intermittently"
**Solution:**
- Increase timeout in workflow: edit `timeout-minutes: 10`
- Check fixture setup in `tests/conftest.py`
- Verify Redis/MongoDB services startup time
- Add debug output: `--tb=short` in pytest

---

### Problem: "Build succeeds but PR checks still pending"
**Solution:**
```bash
# May just be GitHub UI delay (refresh page)
# Or check if branch protection rule mismatch:
gh repo rules list --branch main

# Verify status check names match exactly:
gh run list --limit 1 | grep check
```

---

### Problem: "Cannot access production server during deploy"
**Solution:**
- Verify `DEPLOY_KEY` is added and is private key (not public)
- Test SSH manually: `ssh -i deploy_key deploy@DEPLOY_HOST`
- Check firewall rules on production server
- Verify SSH key permissions: `chmod 600 deploy_key`

---

## ✅ Success Indicators

After completing this checklist, you should see:

✅ Workflows appearing in **Actions** tab  
✅ All status checks passing on PRs  
✅ Docker images pushed to GHCR  
✅ Coverage reports on Codecov  
✅ Security scans showing no critical issues  
✅ Releases created automatically on tags  
✅ Health checks running every 6 hours  
✅ Team running `make` commands locally  

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Codecov Integration](https://codecov.io/docs/getting-started)
- [Trivy Security Scanner](https://aquasecurity.github.io/trivy/latest/)
- [pyproject.toml Reference](https://packaging.python.org/en/latest/pyproject_toml/)
- [Pytest Documentation](https://docs.pytest.org/)
- [The Twelve-Factor App](https://12factor.net/)

---

## 🎯 Next Steps

After setup completes:

1. **For Developers**:
   - Run `make help` to see available commands
   - Review CONTRIBUTING.md for development guidelines
   - Test with: `make lint`, `make format`, `make test`

2. **For DevOps/Releases**:
   - Monitor health checks via GitHub Actions
   - Track releases on GitHub Releases page
   - Pull production images: `docker pull ghcr.io/[repo]:latest`

3. **For Management**:
   - Track deployment status in GitHub Actions
   - Review code coverage trends on Codecov
   - Create GitHub Milestones for sprint planning

