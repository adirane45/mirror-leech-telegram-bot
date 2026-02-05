# Fully Containerized Deployment Guide

## Overview

This production deployment containerizes **everything** - no host dependencies required:
- ✅ Bot application
- ✅ aria2 download manager  
- ✅ qBittorrent torrent client
- ✅ Redis cache
- ✅ MongoDB database
- ✅ Prometheus metrics
- ✅ Grafana dashboards
- ✅ Celery worker & beat

## Prerequisites

- Docker Engine 20.10+
- Docker Compose V2 (5.0+)
- 4GB RAM minimum
- 20GB disk space

## Quick Start

### 1. Deploy the entire stack

```bash
docker compose -f docker-compose.production.yml up -d
```

### 2. Check service health

```bash
docker compose -f docker-compose.production.yml ps
```

All services should show `healthy` status.

### 3. Access the bot

The bot will start automatically and connect to Telegram.

## Service Ports

| Service | Port | Access | 
|---------|------|---------|
| Bot Web Dashboard | 8060 | http://localhost:8060 |
| Bot Metrics | 9090 | http://localhost:9090/metrics |
| aria2 RPC | 6800 | Internal |
| qBittorrent WebUI | 8090 | http://localhost:8090 (admin/mltbmltb) |
| Grafana | 3000 | http://localhost:3000 (admin/mltbadmin) |
| Prometheus | 9091 | http://localhost:9091 |
| Redis | 6379 | Internal |
| MongoDB | 27017 | Internal |

## Initial Setup

### 1. Configure qBittorrent (First Time Only)

After first startup, qBittorrent will generate a temporary password in logs:

```bash
docker logs mltb-qbittorrent | grep "temporary password"
```

Login at http://localhost:8090 with:
- Username: `admin`  
- Password: (from logs)

Then change the password to `mltbmltb` in Web UI settings to match bot configuration.

### 2. Configure aria2 (Optional)

aria2 is pre-configured with sane defaults. To customize:

```bash
# Edit aria2 settings
nano ./aria2/config/aria2.conf

# Restart aria2
docker restart mltb-aria2
```

## File Locations

All data is stored in named Docker volumes:

- **downloads** - Shared download directory
- **redis-data** - Redis persistence
- **mongodb-data** - Database storage
- **prometheus-data** - Metrics history
- **grafana-data** - Dashboard configs
- **logs** - Application logs

To backup all volumes:

```bash
docker run --rm \
  -v mltb_downloads:/downloads \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/downloads-$(date +%F).tar.gz /downloads
```

## Deployment to Remote Server

### Option 1: Docker Context (Recommended)

```bash
# Create remote context
docker context create remote --docker "host=ssh://user@server"

# Deploy to remote
docker context use remote
docker compose -f docker-compose.production.yml up -d
```

### Option 2: Copy and Deploy

```bash
# On your machine
tar czf mltb-deploy.tar.gz \
  docker-compose.production.yml \
  Dockerfile \
  bot/ \
  config.py \
  monitoring/ \
  requirements*.txt

# On server
scp mltb-deploy.tar.gz user@server:~
ssh user@server
tar xzf mltb-deploy.tar.gz
cd mltb
docker compose -f docker-compose.production.yml up -d
```

## Scaling

### Increase Celery Workers

```bash
docker compose -f docker-compose.production.yml up -d --scale celery-worker=3
```

### Adjust Resource Limits

Edit `docker-compose.production.yml` and add:

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
```

## Monitoring

### View Logs

```bash
# All services
docker compose -f docker-compose.production.yml logs -f

# Specific service
docker logs -f mltb-app

# Last 100 lines
docker logs --tail 100 mltb-app
```

### Grafana Dashboards

1. Open http://localhost:3000  
2. Login: admin/mltbadmin
3. Navigate to Dashboards → MLTB Overview

### Prometheus Metrics

Raw metrics: http://localhost:9091/targets

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose -f docker-compose.production.yml logs

# Restart all services
docker compose -f docker-compose.production.yml restart

# Rebuild images
docker compose -f docker-compose.production.yml build --no-cache
docker compose -f docker-compose.production.yml up -d
```

### qBittorrent authentication fails

```bash
# Get initial password
docker logs mltb-qbittorrent 2>&1 | grep -i password

# Reset WebUI (deletes settings)
docker exec mltb-qbittorrent rm /config/qBittorrent/config/qBittorrent.conf
docker restart mltb-qbittorrent
```

### Downloads not appearing

```bash
# Check volume mounts
docker inspect mltb-app | grep -A10 Mounts

# Verify download directory permissions  
docker exec mltb-app ls -la /app/downloads

# Test aria2 connection
docker exec mltb-app curl -s http://aria2:6800/
```

### High memory usage

```bash
# Check resource usage
docker stats

# Adjust Celery concurrency (config section above)
# Restart worker with lower concurrency
docker compose -f docker-compose.production.yml up -d --scale celery-worker=2
```

## Maintenance

### Update to Latest

```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d
```

### Clean Up Old Data

```bash
# Remove completed downloads older than 7 days
docker exec mltb-app find /app/downloads -type f -mtime +7 -delete

# Prune unused Docker resources
docker system prune -af --volumes
```

### Backup Configuration

```bash
# Backup config and volumes
tar czf mltb-backup-$(date +%F).tar.gz \
  config.py \
  docker-compose.production.yml \
  monitoring/ \
  aria2/config/ \
  qbittorrent/config/
```

## Security Hardening

### Change Default Passwords

Edit `docker-compose.production.yml`:

```yaml
services:
  grafana:
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your-strong-password
```

Update qBittorrent password via WebUI.

### Restrict Network Access

```yaml
services:
  qbittorrent:
    ports:
      - "127.0.0.1:8090:8090"  # Bind to localhost only
```

### Use Secrets (Docker Swarm)

See `docker-compose.secure.yml` for production-grade secrets management.

## Production Deployment Checklist

- [ ] Updated `config.py` with production bot token
- [ ] Changed Grafana admin password
- [ ] Changed qBittorrent WebUI password  
- [ ] Configured aria2 download limits
- [ ] Set up volume backups
- [ ] Configured firewall rules
- [ ] Set up monitoring alerts
- [ ] Tested full download → upload flow
- [ ] Documented custom configurations

## Environment Variables

Override any setting via environment variables in compose file:

```yaml
services:
  app:
    environment:
      - BOT_TOKEN=your-token
      - OWNER_ID=123456789
      - REDIS_HOST=redis
      - ARIA2_HOST=aria2
      - QB_HOST=qbittorrent
```

## Support

- Bot logs: `docker logs mltb-app`
- Metrics: http://localhost:9090/metrics
- Grafana: http://localhost:3000
- GitHub Issues: [your-repo]/issues

---

**Phase 1 & 2 Complete** ✅  
Fully containerized, production-ready, deploy-anywhere stack.
