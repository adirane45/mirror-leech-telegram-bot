# Runbook: Grafana

## Scope
Dashboard UI on port 3000.

## Health Signals
- http://localhost:3000/api/health
- docker compose ps grafana

## Common Issues
### Login fails
- Verify GF_SECURITY_ADMIN_USER/PASSWORD

## Recovery Steps
1. docker compose restart grafana
2. If stuck, clear grafana-data volume (data loss)

## Escalation
- Check disk usage and volume permissions.
