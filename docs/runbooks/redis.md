# Runbook: Redis

## Scope
Cache and queue backend for app and Celery.

## Health Signals
- redis-cli ping
- docker compose ps redis

## Common Issues
### Redis not responding
- docker compose logs --tail 200 redis
- Check disk usage

## Recovery Steps
1. docker compose restart redis
2. If data corruption suspected: stop, move data volume, restart
3. Verify app reconnects

## Escalation
- If Redis fails repeatedly, inspect host disk and memory.
