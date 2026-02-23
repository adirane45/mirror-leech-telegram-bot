# CI/CD Architecture Overview

This document provides a high-level overview of the CI/CD pipeline structure and architecture.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Repository                           │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐ │
│  │ Feature Branch │  │ Main Branch    │  │ Release Tags      │ │
│  │ (with PR)      │  │ (push/merge)   │  │ (v*.*)            │ │
│  └───────┬────────┘  └───────┬────────┘  └────────┬──────────┘ │
│          │                   │                     │            │
└──────────┼───────────────────┼─────────────────────┼────────────┘
           │                   │                     │
           ▼                   ▼                     ▼
      ┌──────────────────────────────────────────────────┐
      │        GitHub Actions Workflows                 │
      │                                                  │
      │  ┌─────────────────────────────────────┐        │
      │  │ build.yml (Smart Trigger)           │        │
      │  │ - When: PR + commits to main branch │        │
      │  │ - Runs: Lint, Test, Build, Scan    │        │
      │  └─────────────────────────────────────┘        │
      │                                                  │
      │  ┌─────────────────────────────────────┐        │
      │  │ quality.yml (Continuous)            │        │
      │  │ - When: PR + push to main/develop   │        │
      │  │ - Runs: Lint, Type Check, Security │        │
      │  └─────────────────────────────────────┘        │
      │                                                  │
      │  ┌─────────────────────────────────────┐        │
      │  │ tests.yml (Comprehensive)           │        │
      │  │ - When: PR + src/tests changes      │        │
      │  │ - Runs: Unit + Integration tests   │        │
      │  └─────────────────────────────────────┘        │
      │                                                  │
      │  ┌─────────────────────────────────────┐        │
      │  │ release.yml (Tag Triggered)         │        │
      │  │ - When: Tag pushed (v*.*)           │        │
      │  │ - Runs: Build, Release, Publish    │        │
      │  └─────────────────────────────────────┘        │
      │                                                  │
      │  ┌─────────────────────────────────────┐        │
      │  │ health-check.yml (Scheduled)        │        │
      │  │ - When: Every 6 hours + manual      │        │
      │  │ - Runs: Service verification       │        │
      │  └─────────────────────────────────────┘        │
      │                                                  │
      └──────────────────────────────────────────────────┘
```

## Workflow Execution Flow

### Pull Request (Feature Branch)

```
Developer creates PR
      ↓
┌─────────────────────────────────────┐
│     GitHub Actions Triggered        │
└─────────────────────────────────────┘
      ↓
┌─── PARALLEL JOBS ───┐
│ ┌──────────────────┐ │
│ │  Lint Check      │ │  ← flake8, pylint, black check
│ └──────────────────┘ │
│ ┌──────────────────┐ │
│ │  Type Check      │ │  ← mypy analysis
│ └──────────────────┘ │
│ ┌──────────────────┐ │
│ │  Security Scan   │ │  ← bandit, TruffleHog
│ └──────────────────┘ │
└─ END PARALLEL ──────┘
      ↓
┌─── UNIT TESTS ───────────────────────┐
│ Matrix across Python 3.10/3.11/3.12  │
│ - pytest fixtures setup              │
│ - Redis + MongoDB services started   │
│ - Coverage reports generated         │
│ - Results uploaded to Codecov        │
└──────────────────────────────────────┘
      ↓
┌─── DOCKER BUILD ─────────────────────┐
│ - Build image from Dockerfile        │
│ - Tag with branch: branch-sha12345    │
│ - Scan with Trivy                    │
│ - Push to GHCR (not yet, PR only)    │
└──────────────────────────────────────┘
      ↓
Branch protection checks pass
      ↓
Ready for review & merge
```

### Main Branch (Merge)

```
PR approved and merged to main
      ↓
      └─ Same as PR + Additional:
           ├─ Docker image tagged 'main'
           ├─ Push to GitHub Container Registry
           ├─ Tag with latest commit SHA
           ├─ Optional: Auto-deploy to staging
           └─ Notify on failure
```

### Release (Version Tag)

```
git tag v3.2.0 && git push origin v3.2.0
      ↓
┌─────────────────────────────────────┐
│  release.yml triggered              │
└─────────────────────────────────────┘
      ├─ Checkout full history
      ├─ Extract version from tag
      ├─ Generate changelog
      ├─ Build distributions (wheel/sdist)
      │
      ├─ Create GitHub Release
      │  ├─ Title: v3.2.0
      │  ├─ Body: auto-generated notes
      │  └─ Artifacts: wheel + sdist
      │
      ├─ Docker build & push
      │  ├─ Tag: ghcr.io/owner/repo:v3.2.0
      │  ├─ Tag: ghcr.io/owner/repo:latest
      │  └─ Push to registry
      │
      └─ GitHub Release published
```

## Parallel Job Execution

```
commit pushed to main branch
      ↓
┌─────────────────────────────────────────────────┐
│         build.yml workflow started              │
└─────────────────────────────────────────────────┘
      ↓
┌─ STAGE 1: Quality (30s) ────────────────────┐
│                                             │
│  Job: lint          [RUNNING] ███░░░░░░░░░░ │
│  Job: typecheck     [RUNNING] ███░░░░░░░░░░ │
│  Job: security      [RUNNING] ███░░░░░░░░░░ │
│                                             │
└─────────────────────────────────────────────┘
      ↓ (all pass)
┌─ STAGE 2: Tests (120s) ─────────────────────┐
│                                             │
│  Job: test (3.10)   [RUNNING] ███░░░░░░░░░░ │
│  Job: test (3.11)   [RUNNING] ███░░░░░░░░░░ │
│  Job: test (3.12)   [RUNNING] ███░░░░░░░░░░ │
│                                             │
└─────────────────────────────────────────────┘
      ↓ (all pass)
┌─ STAGE 3: Build (90s) ──────────────────────┐
│                                             │
│  Job: build         [RUNNING] ███░░░░░░░░░░ │
│  Job: security      [RUNNING] ███░░░░░░░░░░ │
│                                             │
└─────────────────────────────────────────────┘
      ↓ (all pass)
✅ All checks passed
```

## Job Dependencies

```
                    ┌──────────────┐
                    │  Lint Step   │
                    └──────┬───────┘
                           │
                 ┌─────────┴─────────┐
                 │                   │
           ┌─────▼──────┐  ┌────────▼────┐
           │  Tests     │  │  Type Check  │
           └─────┬──────┘  └────────┬────┘
                 │                  │
                 └─────────┬────────┘
                           │
                      ┌────▼────┐
                      │  Build   │
                      └────┬────┘
                           │
                      ┌────▼─────┐
                      │ Security  │
                      └───────────┘

SEQUENTIAL: Lint → (Tests + TypeCheck) → Build → Security
PARALLEL within stage: Tests run on 3 Python versions simultaneously
```

## Status Check Integration

```
GitHub Branch Protection Rules
│
├─ ✅ build - Verifies Docker image builds
├─ ✅ lint - Code style compliance (flake8, black, isort)
├─ ✅ typecheck - Type safety (mypy)
├─ ✅ security - Security scanning (bandit)
├─ ✅ test - Unit tests on Python 3.11
│   ├─ pytest unit tests pass
│   ├─ Coverage threshold met (configurable)
│   └─ Integration tests pass
│
├─ ✅ Requires Reviews - Minimum 1 approval
├─ ✅ Requires Branch to Be Up to Date
└─ ✅ Conversation Resolution Required

Pull Request cannot merge until ALL checks are ✅
```

## Workflow Triggers Summary

| Workflow | Trigger | Branches | Paths | Run Time |
|----------|---------|----------|-------|----------|
| build | push + PR | main, develop | src/**, deployment/ | ~5-10 min |
| quality | push + PR | main, develop | src/** | ~3-5 min |
| tests | push + PR | main, develop | src/**, tests/** | ~10-15 min |
| release | tag push | any | N/A | ~5-8 min |
| health-check | schedule | N/A | N/A | 6h + manual |

## Artifact & Output Flow

```
Tests Phase:
  Output: coverage.xml → Codecov
  Output: junit.xml → GitHub Artifacts
  Output: htmlcov/ → GitHub Artifacts

Build Phase:
  Docker image → GitHub Container Registry
  Tags: latest, branch-sha, version

Release Phase:
  Wheel distribution → GitHub Release
  Sdist distribution → GitHub Release
  Docker image → GHCR with version tag

Health Check Phase:
  Results → GitHub Actions logs
  Failures → Email notification (configurable)
```

## Service Dependencies

```
Workflow Requirements:
  ├─ GitHub Actions Runners (Ubuntu latest)
  ├─ Docker (for image building)
  ├─ Python 3.10, 3.11, 3.12 (from matrix)
  ├─ Redis 7 (test services)
  ├─ MongoDB latest (test services)
  └─ External: Codecov, GitHub Container Registry

Production Requirements:
  ├─ Docker Compose v2
  ├─ 10 services (app, redis, mongo, etc)
  ├─ Ports: 8060 (app), 6379 (redis), 27017 (mongo)
  └─ SSH access for deployment
```

## Success Metrics

```
Build Success indicates:
  ✅ Code quality passes standards
  ✅ All tests pass on 3 Python versions
  ✅ Type checking passes
  ✅ Security scanning finds no critical issues
  ✅ Docker image builds successfully
  ✅ Coverage metrics within threshold

Release Success indicates:
  ✅ All build metrics pass
  ✅ GitHub Release created with notes
  ✅ Docker image tagged and pushed
  ✅ Distribution packages created
  ✅ Version tag properly formatted
```

## Error Handling & Recovery

```
If Build Fails:
1. Check logs in GitHub Actions
2. Review specific job failure
3. Fix locally: make lint, make test
4. Commit and push to trigger rebuild

If Security Scan Fails:
1. Review Trivy report (CRITICAL only blocks)
2. Update dependencies or suppress if false positive
3. Document decision in PR

If Tests Timeout:
1. Increase timeout-minutes in workflow
2. Check for hanging fixtures in conftest.py
3. Verify Redis/MongoDB startup time

If Deploy Fails:
1. Verify SSH credentials in secrets
2. Check production server connectivity
3. Review deployment logs via gh CLI
```

## Performance Optimization

1. **Build Cache**:
   - Docker layer caching via registry
   - Python dependencies cached via actions/setup-python

2. **Parallel Execution**:
   - Quality checks run simultaneously
   - Test matrix runs on 3 Python versions in parallel
   - Reduces total time from 30+ min to ~15 min

3. **Smart Triggers**:
   - Only run on changes to relevant paths
   - Skip docker build if only docs changed
   - Cancel previous runs on new push

## Monitoring & Observability

```
View Workflow Status:
  GitHub UI: Repository → Actions tab
  CLI: gh run list --limit 10

View Detailed Logs:
  GitHub UI: Click workflow run → Select job
  CLI: gh run view <RUN_ID> --log

Coverage Tracking:
  Codecov: https://codecov.io/gh/owner/repo
  Badge: ![Coverage](https://codecov.io/gh/owner/repo/branch/main/graph/badge.svg)

Docker Image Tracking:
  GHCR: https://github.com/owner/repo/pkgs/container/
  Digest: ghcr.io/owner/repo@sha256:...

Security Alerts:
  GitHub: Settings → Security → Code scanning
  Issues: Tagged as `security` priority
```

See [CI_CD_PIPELINE.md](CI_CD_PIPELINE.md) for detailed configuration and [CI_CD_SETUP_CHECKLIST.md](CI_CD_SETUP_CHECKLIST.md) for implementation guide.
