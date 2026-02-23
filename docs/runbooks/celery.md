# Runbook: Celery Worker/Beat

## Scope
Background job processing and scheduled tasks.

## Health Signals
- docker compose ps celery-worker celery-beat
- Worker inspect: docker compose exec -T celery-worker /app/mltbenv/bin/celery -A bot.core.celery_app inspect active

## Common Issues
### Tasks not running
- Check logs: docker compose logs --tail 200 celery-worker
- Verify Redis is healthy

## Recovery Steps
1. docker compose restart celery-worker celery-beat
2. If stuck: docker compose up -d --build celery-worker celery-beat

## Escalation
- Check task queue length and Redis memory.
