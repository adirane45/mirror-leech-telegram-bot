# Runbook: Prometheus

## Scope
Metrics collection on port 9091.

## Health Signals
- http://localhost:9091/-/healthy
- docker compose ps prometheus

## Common Issues
### Scrape errors
- Check targets: http://localhost:9091/targets
- Verify app /metrics is reachable

## Recovery Steps
1. docker compose restart prometheus
2. Validate config file path

## Escalation
- If metrics missing, check app metrics endpoint and network.
