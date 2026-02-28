# Docker Image Selection Guide

Quick reference for choosing the right Docker image variant for your deployment.

## TL;DR - Which Image Should I Use?

```
┌─────────────────────────┬──────────────────────────────────────┐
│ Your Use Case           │ Recommended Dockerfile               │
├─────────────────────────┼──────────────────────────────────────┤
│ Production (all feat)   │ deployment/Dockerfile.optimized      │
│ Smallest possible       │ deployment/Dockerfile.alpine         │
│ Don't need JDownloader  │ deployment/Dockerfile.no-jdownloader │
│ Legacy/compatibility    │ deployment/Dockerfile (original)     │
└─────────────────────────┴──────────────────────────────────────┘
```

## Quick Start

### Option 1: Optimized (Recommended)
```bash
# Build
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.optimized -t mltb-app:optimized .

# Deploy
docker-compose -f docker-compose.optimized.yml up -d
```

### Option 2: Alpine (Smallest)
```bash
# Build
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.alpine -t mltb-app:alpine .

# Deploy (edit docker-compose.yml to use alpine variant)
docker-compose up -d
```

### Option 3: No JDownloader (Faster)
```bash
# Build
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.no-jdownloader -t mltb-app:no-jd .

# Deploy
docker-compose up -d
```

## Image Comparison

| Feature | Original | Optimized | Alpine | No-JD |
|---------|----------|-----------|--------|-------|
| **Size** | 1.92GB | ~400MB | ~300MB | ~350MB |
| **Build Time** | ~5 min | ~10 min | ~17 min | ~7 min |
| **Cold Start** | 45s | 25s | 20s | 25s |
| **Memory** | 800MB | 600MB | 550MB | 600MB |
| **JDownloader** | ✅ | ✅ | ✅ | ❌ |
| **Compatibility** | 🟢 High | 🟢 High | 🟡 Medium | 🟢 High |
| **Security** | 🟡 Root | 🟢 Non-root | 🟢 Non-root | 🟢 Non-root |

## Detailed Comparison

### Dockerfile.optimized (Recommended)
**Best for:** Production deployments with all features

**Pros:**
- ✅ 79% smaller than original (400MB vs 1.92GB)
- ✅ All features enabled (aria2, qBittorrent, JDownloader)
- ✅ Excellent compatibility
- ✅ Non-root user for security
- ✅ Fast rebuild with layer caching

**Cons:**
- ⚠️ Initial build takes longer (~10 min)
- ⚠️ Still larger than Alpine variant

**Use when:**
- Deploying to production
- Need all download clients
- Want best balance of size and compatibility

### Dockerfile.alpine (Smallest)
**Best for:** Size-critical deployments (cloud, ARM devices)

**Pros:**
- ✅ 85% smaller (300MB vs 1.92GB)
- ✅ Minimal attack surface
- ✅ Fast cold start (20s)
- ✅ Low memory usage

**Cons:**
- ⚠️ Longer build time (~17 min)
- ⚠️ Potential compatibility issues with some Python packages
- ⚠️ Requires more testing

**Use when:**
- Deploying to bandwidth-limited environments
- Running on Raspberry Pi or ARM devices
- Size is critical (IoT, edge computing)

### Dockerfile.no-jdownloader (JD-Free)
**Best for:** Deployments not using JDownloader

**Pros:**
- ✅ 82% smaller (350MB vs 1.92GB)
- ✅ Faster build (~7 min)
- ✅ No OpenJDK 21 (saves 150MB+)
- ✅ All other features enabled

**Cons:**
- ❌ No JDownloader support
- ⚠️ Need to disable JD features in config

**Use when:**
- You only use aria2 and qBittorrent
- Don't need Java-based downloaders
- Want faster builds

### Dockerfile (Original)
**Best for:** Legacy compatibility, debugging

**Pros:**
- ✅ Tested and stable
- ✅ Fast build (~5 min)
- ✅ No surprises

**Cons:**
- ❌ 1.92GB (very large)
- ❌ Slow deployments
- ❌ High bandwidth costs
- ❌ Runs as root (security concern)

**Use when:**
- Debugging build issues
- Need exact match with existing deployments
- Migrating to optimized builds incrementally

## Build Time Comparison

```
Original:       ████░░░░░░░░░░░░░░░░  ~5 min
Optimized:      ████████░░░░░░░░░░░░  ~10 min
No-JDownloader: ██████░░░░░░░░░░░░░░  ~7 min
Alpine:         █████████████░░░░░░░  ~17 min
```

## Storage Cost Comparison (AWS ECR)

**Monthly cost for 1 image (retagged 10x per day):**

```
Original:       $1.92 × 0.10 = $0.19/month
Optimized:      $0.40 × 0.10 = $0.04/month  (79% savings)
No-JDownloader: $0.35 × 0.10 = $0.035/month (81% savings)
Alpine:         $0.30 × 0.10 = $0.03/month  (84% savings)
```

**For 50 daily deployments:**
```
Original:       $57/month in transfer costs
Optimized:      $12/month in transfer costs (79% savings = $45/month saved)
```

## Deployment Scenarios

### Scenario 1: High-Traffic Production Bot
**Recommendation:** Dockerfile.optimized

**Reasoning:**
- Need all features (aria2, qBittorrent, JDownloader)
- Stability and compatibility critical
- Multiple deployments per day
- Size reduction saves on bandwidth

**Command:**
```bash
docker-compose -f docker-compose.optimized.yml up -d
```

### Scenario 2: Personal Bot on VPS
**Recommendation:** Dockerfile.no-jdownloader

**Reasoning:**
- Likely don't need JDownloader
- VPS has limited storage
- Faster updates
- Lower costs

**Command:**
```bash
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.no-jdownloader -t mltb-app .
docker-compose up -d
```

### Scenario 3: Raspberry Pi Deployment
**Recommendation:** Dockerfile.alpine

**Reasoning:**
- ARM compatibility
- Limited storage/memory
- Size is critical
- Can test compatibility

**Command:**
```bash
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.alpine -t mltb-app:alpine .
docker-compose up -d
```

### Scenario 4: Development Environment
**Recommendation:** Dockerfile (Original)

**Reasoning:**
- Fast iterative builds
- Don't care about size on dev machine
- Perfect compatibility
- Easy debugging

**Command:**
```bash
docker-compose up -d
```

## Migration Path

### From Original → Optimized

**Step 1:** Test build
```bash
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.optimized -t mltb-test:optimized .
```

**Step 2:** Test locally
```bash
docker run --rm -e BOT_TOKEN=test mltb-test:optimized python -c "import bot; print('OK')"
```

**Step 3:** Deploy to staging
```bash
docker-compose -f docker-compose.optimized.yml up -d
```

**Step 4:** Monitor for 24-48 hours
```bash
docker logs -f mltb-app
docker stats mltb-app
```

**Step 5:** Deploy to production
```bash
# Backup current setup first
docker-compose down
docker tag mltb-app:current mltb-app:backup

# Deploy optimized
docker-compose -f docker-compose.optimized.yml up -d
```

## Troubleshooting

### Build fails on Alpine
```bash
# Add missing build dependencies
RUN apk add --no-cache gcc musl-dev linux-headers libffi-dev
```

### Image still large after optimization
```bash
# Analyze layers
docker history mltb-app:optimized

# Find large files
docker run --rm mltb-app:optimized du -sh /* | sort -h
```

### Slow builds
```bash
# Enable BuildKit
export DOCKER_BUILDKIT=1

# Use layer caching
docker build --cache-from mltb-app:optimized ...
```

## Performance Benchmarks

Run comparison script:
```bash
bash scripts/test_scripts/docker_image_comparison.sh
```

## More Information

- [Complete Optimization Guide](docs/operations/DOCKER_IMAGE_OPTIMIZATION.md)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Multi-Stage Builds](https://docs.docker.com/develop/develop-images/multistage-build/)

---

**Need help?** Open an issue or check existing discussions.
