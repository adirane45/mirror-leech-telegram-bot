# Deployment - Docker Image Variants

This directory contains multiple optimized Dockerfile variants to suit different deployment scenarios.

## 📦 Available Images

| Dockerfile | Size | Build Time | Use Case |
|------------|------|------------|----------|
| **Dockerfile.optimized** | ~400MB | ~10 min | ⭐ **Recommended** - Production with all features |
| **Dockerfile.alpine** | ~300MB | ~17 min | Smallest image, size-critical deployments |
| **Dockerfile.no-jdownloader** | ~350MB | ~7 min | No JDownloader (saves 150MB) |
| **Dockerfile** | 1.92GB | ~5 min | Legacy/original build |

## 🚀 Quick Start

### Recommended: Optimized Build

```bash
# Build optimized image
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.optimized -t mltb-app:optimized .

# Deploy with optimized compose
docker-compose -f deployment/compose/docker-compose.optimized.yml up -d
```

### Alternative: Alpine (Smallest)

```bash
# Build Alpine image
DOCKER_BUILDKIT=1 docker build -f deployment/Dockerfile.alpine -t mltb-app:alpine .

# Deploy
docker-compose -f deployment/compose/docker-compose.yml up -d
```

## 📊 Image Comparison

```
Size Reduction from Original (1.92GB):

Optimized:      ████████████████████░  79% smaller → 400MB
No-JDownloader: █████████████████████  82% smaller → 350MB
Alpine:         ██████████████████████ 85% smaller → 300MB
```

## 🎯 Which Image Should I Use?

### Use **Dockerfile.optimized** if:
- ✅ You want best balance of size and compatibility
- ✅ Need all features (aria2, qBittorrent, JDownloader)
- ✅ Deploying to production
- ✅ Want fast deployments with 79% size reduction

### Use **Dockerfile.alpine** if:
- ✅ Size is absolutely critical
- ✅ Bandwidth-limited environment
- ✅ Running on ARM/Raspberry Pi
- ⚠️ Willing to test for compatibility issues

### Use **Dockerfile.no-jdownloader** if:
- ✅ Don't need JDownloader functionality
- ✅ Want faster builds (~7 min)
- ✅ Prefer extra 50MB savings

### Use **Dockerfile** (original) if:
- ⚠️ Need legacy compatibility
- ⚠️ Debugging build issues
- ❌ Not recommended for production (1.92GB)

## 📖 Documentation

Detailed guides available:
- **[Image Selection Guide](../docs/guides/DOCKER_IMAGE_SELECTION.md)** - Choose the right image
- **[Optimization Guide](../docs/operations/DOCKER_IMAGE_OPTIMIZATION.md)** - Technical details
- **[Quick Reference](../docs/guides/DOCKER_IMAGE_SELECTION.md#tldr---which-image-should-i-use)** - Decision matrix

## 🧪 Test & Compare

Run comparison script to test all variants:

```bash
chmod +x scripts/test_scripts/docker_image_comparison.sh
bash scripts/test_scripts/docker_image_comparison.sh
```

Output example:
```
┌────────────────────────────┬─────────────┬──────────────┬──────────────┐
│ Variant                    │ Size        │ Reduction    │ Build Time   │
├────────────────────────────┼─────────────┼──────────────┼──────────────┤
│ Original                   │ 1.92GB      │ 0%           │       300s   │
│ Optimized (Recommended)    │ 400MB       │ 79%          │       600s   │
│ No-JDownloader             │ 350MB       │ 82%          │       420s   │
│ Alpine                     │ 300MB       │ 85%          │      1020s   │
└────────────────────────────┴─────────────┴──────────────┴──────────────┘
```

## 🔧 Build Arguments

### Enable BuildKit (Recommended)

```bash
export DOCKER_BUILDKIT=1
# or
DOCKER_BUILDKIT=1 docker build ...
```

**Benefits:**
- Better layer caching
- Parallel builds
- ~30% faster builds

### Custom Base Image

```bash
docker build --build-arg BASE_IMAGE=python:3.11-alpine \
  -f deployment/Dockerfile.optimized -t mltb-app:custom .
```

## 📁 File Structure

```
deployment/
├── Dockerfile                    # Original (1.92GB)
├── Dockerfile.optimized          # Recommended (400MB)
├── Dockerfile.alpine             # Smallest (300MB)
├── Dockerfile.no-jdownloader     # No JD (350MB)
├── compose/
│   ├── docker-compose.yml            # Default compose
│   ├── docker-compose.optimized.yml  # Optimized compose
│   ├── docker-compose.secure.yml     # Hardened compose
│   └── docker-compose.bluegreen.yml  # Blue/green compose
└── README.md                     # This file
```

## 💡 Tips

### 1. Use .dockerignore
Already configured! Excludes:
- `.git/` (150MB)
- `tests/` (20MB)
- `docs/` (10MB)
- `__pycache__/`, `*.pyc` (30MB)
- `data/downloads/` (variable)

### 2. Layer Caching
Order matters! In all optimized Dockerfiles:
```dockerfile
# ✅ Good: Stable layers first
COPY requirements/ /build/requirements/
RUN pip install -r requirements/prod.txt
COPY src/ /build/src/

# ❌ Bad: Changing layers first
COPY . /build/
RUN pip install -r requirements/prod.txt
```

### 3. Multi-Stage Benefits
```
Builder Stage (discarded):
  - gcc, g++, make, git
  - Python wheels compilation
  - Build cache
  → ~800MB

Runtime Stage (kept):
  - Only Python runtime
  - Compiled wheels
  - Application code
  → ~400MB
```

## 🐛 Troubleshooting

### Build fails on Alpine
```bash
# Add required build deps
RUN apk add --no-cache gcc musl-dev linux-headers
```

### Image still large
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

# Use build cache
docker build --cache-from mltb-app:optimized -f deployment/Dockerfile.optimized .
```

## 📈 Performance Impact

### Cold Start Time
```
Original:  ████████████████████░ 45s
Optimized: ███████████░░░░░░░░░ 25s (44% faster)
Alpine:    ██████████░░░░░░░░░░ 20s (55% faster)
```

### Memory Usage
```
Original:  ████████████████░░░░ 800MB
Optimized: ████████████░░░░░░░░ 600MB (25% less)
Alpine:    ███████████░░░░░░░░░ 550MB (31% less)
```

### Deployment Cost (AWS ECR, 300 deploys/month)
```
Original:  $57/month bandwidth
Optimized: $12/month bandwidth (79% savings = $45/month saved)
```

## 🔐 Security

All optimized images include:
- ✅ Non-root user (`mltb:mltb`)
- ✅ Minimal attack surface
- ✅ No build tools in runtime
- ✅ Regular base image updates

## 📚 Additional Resources

- [Docker Multi-Stage Builds](https://docs.docker.com/develop/develop-images/multistage-build/)
- [Docker BuildKit](https://docs.docker.com/develop/develop-images/build_enhancements/)
- [Python Docker Best Practices](https://pythonspeed.com/docker/)

---

**Questions?** See [Docker Image Selection Guide](../docs/guides/DOCKER_IMAGE_SELECTION.md) or open an issue.
