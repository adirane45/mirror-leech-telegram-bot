# On-Call Guide

## Primary Checks
1. docker compose ps
2. docker compose logs --tail 200 app
3. curl -f http://localhost:8060/webstat
4. curl -f http://localhost:9091/-/healthy

## Escalation
- If app unhealthy after restart, check Redis and download clients.
- If alerts are flapping, verify Alertmanager config and receivers.

## Common Commands
- Restart app: docker compose restart app
- Full restart: docker compose down && docker compose up -d
- View logs: docker compose logs -f
