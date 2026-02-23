# Runbook: Metrics Endpoint

## Scope
App /metrics endpoint for Prometheus.

## Health Signals
- http://localhost:9090/metrics

## Common Issues
### 404 or empty metrics
- Check ENHANCED_API availability
- Restart app

## Recovery Steps
1. docker compose restart app
2. Verify /metrics

## Escalation
- Inspect bot.core.metrics for exporter errors
