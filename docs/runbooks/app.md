# Runbook: App (FastAPI + Bot)

## Scope
Main app container serving dashboard, API, bot runtime.

## Health Signals
- HTTP 200 on http://localhost:8060/
- Metrics: http://localhost:9090/metrics
- Container health: docker compose ps app

## Common Issues
### App not responding
- Check logs: docker compose logs -f app
- Verify port mapping: docker compose ps app
- Restart: docker compose restart app

### High error rate
- Check recent errors: docker compose logs --tail 200 app
- Verify Redis and download clients

## Recovery Steps
1. docker compose restart app
2. If still unhealthy: docker compose up -d --build app
3. Validate endpoints:
   - http://localhost:8060/webstat
   - http://localhost:8060/api/dashboard/stats

## Escalation
- If persistent after rebuild, check Redis, aria2, qBittorrent status.
