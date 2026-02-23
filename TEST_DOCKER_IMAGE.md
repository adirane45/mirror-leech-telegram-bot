# Docker Image Testing Guide

## Overview

After the recent restructuring and Dockerfile alignment, verify the Docker image builds and runs correctly with the new `src/` layout.

## Prerequisites

- Docker installed and running
- Terminal access to the project root
- At least 2GB free disk space
- Docker Compose v2+

## Option 1: Build & Test Locally

### Step 1: Build the Docker Image

```bash
# Build using the updated Dockerfile
docker build -f deployment/Dockerfile \
  -t mirror-leech-telegram-bot:latest \
  -t mirror-leech-telegram-bot:3.2.1 \
  .
```

**Expected Output:**
```
[+] Building [image_id]
[+] Exporting to docker image
=> exporting to docker image 632.0 MiB
=> => exporting manifest sha256:...
=> => exporting config sha256:...
[+] Building 123.5s (XX/XX)
Successfully tagged mirror-leech-telegram-bot:latest
Successfully tagged mirror-leech-telegram-bot:3.2.1
```

### Step 2: Verify Image Structure

```bash
# Check image size
docker images mirror-leech-telegram-bot

# Expected output:
# REPOSITORY    TAG      IMAGE ID       SIZE
# mirror-...    latest   abc123def456   1.5GB
# mirror-...    3.2.1    abc123def456   1.5GB
```

**Size Guide:**
- Expected: 1.2 - 1.8 GB (base image + Python venv)
- If larger (>2GB): Image may have unnecessary layers
- If smaller (<1GB): Some dependencies may be missing

### Step 3: Verify PYTHONPATH in Container

```bash
# Check environment variables
docker run --rm mirror-leech-telegram-bot:latest \
  python3 -c "import sys; print('\n'.join(sys.path))"
```

**Expected Output:**
```
/app/src
/app/mltbenv/lib/python3.11/site-packages
...
```

✅ **Success criteria**: `/app/src` appears in the first line

### Step 4: Verify imports work

```bash
# Test that bot can import modules
docker run --rm mirror-leech-telegram-bot:latest \
  python3 -c "from bot.helpers import download; print('✓ bot imports working')"
```

**Expected**: `✓ bot imports working`

### Step 5: Test Full Stack with Docker Compose

```bash
# Start all services
cd /home/kali/mirror-leech-telegram-bot
docker compose -f deployment/compose/docker-compose.yml up -d

# Wait 30 seconds for services to start
sleep 30

# Check health
docker compose -f deployment/compose/docker-compose.yml ps
```

**Expected Status:**
```
CONTAINER           STATUS
mirror-bot          healthy (or running)
redis               healthy
mongodb             healthy
aria2               healthy
qbittorrent         healthy
[... other services ...]
```

### Step 6: Verify Health Endpoint

```bash
# Check health endpoint (once services are ready)
curl -s http://localhost:8060/api/health | python3 -m json.tool
```

**Expected Output:**
```json
{
  "status": "healthy",
  "version": "3.2.1",
  "uptime": "45s",
  "timestamp": "2026-02-23T10:30:00.000Z",
  "services": {
    "redis": "connected",
    "mongodb": "connected",
    "aria2": "connected",
    "qbittorrent": "connected"
  }
}
```

**If service fails to start:**
```bash
# Check logs
docker compose -f deployment/compose/docker-compose.yml logs mirror-bot

# Check for import errors
docker compose -f deployment/compose/docker-compose.yml logs mirror-bot | grep -i "module\|import"
```

---

## Option 2: Test GHCR Image (After GitHub Actions)

> ⏳ **Note**: Available after `build.yml` workflow completes (~5-10 minutes after master push)

### Step 1: Pull from GitHub Container Registry

```bash
# Authenticate with GitHub (if private)
# echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Pull the image
docker pull ghcr.io/adirane45/mirror-leech-telegram-bot:latest
docker pull ghcr.io/adirane45/mirror-leech-telegram-bot:3.2.1
```

### Step 2: Tag for Local Use

```bash
docker tag ghcr.io/adirane45/mirror-leech-telegram-bot:latest mirror-leech-telegram-bot:ghcr-latest
docker tag ghcr.io/adirane45/mirror-leech-telegram-bot:3.2.1 mirror-leech-telegram-bot:ghcr-3.2.1
```

### Step 3: Run Same Verification Tests

```bash
# Verify PYTHONPATH
docker run --rm mirror-leech-telegram-bot:ghcr-latest \
  python3 -c "import sys; print('\n'.join(sys.path))"

# Verify imports
docker run --rm mirror-leech-telegram-bot:ghcr-latest \
  python3 -c "from bot.helpers import download; print('✓ GHCR image working')"
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'bot'"

**Cause**: PYTHONPATH not set to `/app/src`

**Solution**:
```bash
# Verify in Dockerfile
grep "PYTHONPATH" deployment/Dockerfile

# Should output:
# ENV PYTHONPATH="/app/src:$PYTHONPATH"

# If missing, the file wasn't properly updated
```

### Issue: "python3: can't open file '-m': No such file or directory"

**Cause**: Bot startup path is incorrect

**Solution**:
```bash
# Check the CMD line in Dockerfile
grep "CMD" deployment/Dockerfile

# Should show:
# CMD ["/app/mltbenv/bin/python3", "-m", "bot"]
```

### Issue: Services don't become healthy

**Cause**: Dependencies from `requirements/prod.txt` missing

**Solution**:
```bash
# Verify requirements file exists
ls -lh requirements/prod.txt

# Check Dockerfile uses it
grep "requirements/prod.txt" deployment/Dockerfile

# Rebuild image
docker build -f deployment/Dockerfile -t mirror-leech-telegram-bot:latest .
```

### Issue: "cannot connect to Docker daemon"

**Solution**:
```bash
# Start Docker
sudo systemctl start docker

# Or on macOS:
# open --app Docker

# Verify connection
docker ps
```

### Issue: Disk space issues during build

**Solution**:
```bash
# Clean up unused images/containers
docker system prune -a

# Check available space
df -h

# See image size before building
docker images
```

---

## Performance Checks

### Build Time

```bash
# Time the build
time docker build -f deployment/Dockerfile -t mirror-leech-telegram-bot:test .
```

**Expected**: 2-5 minutes (first build), <1 minute (cached)

### Container Size

```bash
# Check image layers
docker history mirror-leech-telegram-bot:latest

# Check final size
docker images mirror-leech-telegram-bot:latest
```

**Expected Size**: <2 GB (optimized multi-stage build)

### Memory Usage

```bash
# Monitor during compose startup
docker compose -f deployment/compose/docker-compose.yml up -d
docker stats

# Should stabilize under 2 GB with 10 services
```

---

## Validation Checklist

- [ ] Docker image builds without errors
- [ ] Image size is reasonable (<2 GB)
- [ ] `/app/src` appears in Python sys.path
- [ ] Bot module imports successfully
- [ ] All services start and become healthy
- [ ] Health endpoint returns valid JSON
- [ ] All core services (redis, mongodb, aria2, etc.) show "connected" or "healthy"
- [ ] No import errors in logs
- [ ] GHCR image pulls successfully (after GitHub Actions)
- [ ] GHCR image has same functionality as local build

---

## Commands Quick Reference

```bash
# Build locally
docker build -f deployment/Dockerfile -t mirror-leech-telegram-bot:latest .

# Test Python path
docker run --rm mirror-leech-telegram-bot:latest python3 -c "import sys; print(sys.path)"

# Test imports
docker run --rm mirror-leech-telegram-bot:latest python3 -c "from bot.helpers import download"

# Start full stack
docker compose -f deployment/compose/docker-compose.yml up -d

# Check status
docker compose -f deployment/compose/docker-compose.yml ps

# Health check
curl http://localhost:8060/api/health

# View logs
docker compose -f deployment/compose/docker-compose.yml logs -f mirror-bot

# Stop all
docker compose -f deployment/compose/docker-compose.yml down

# Clean up
docker system prune -a
```

---

## Success Indicators

✅ **Build succeeds**: No errors during `docker build`  
✅ **PYTHONPATH correct**: `/app/src` in sys.path  
✅ **Imports work**: Bot modules load without errors  
✅ **Services healthy**: All containers transition to healthy status  
✅ **Health endpoint**: Returns JSON with all services connected  
✅ **Logs clean**: No import errors, module warnings, or missing dependency messages  

---

## Next Steps After Testing

- ✅ If tests pass: [Verify GitHub Release](VERIFY_RELEASE.md)
- ❌ If tests fail: Check [CHECK_ACTIONS.md](CHECK_ACTIONS.md) troubleshooting section

---

Generated: 2026-02-23  
Document: Docker Image Testing & Validation  
Target: Post-restructure verification
