# Runbook: Alertmanager

## Scope
Alert routing on port 9093.

## Health Signals
- http://localhost:9093/-/healthy
- docker compose ps alertmanager

## Common Issues
### Config parse errors
- Check logs: docker compose logs --tail 200 alertmanager
- Validate YAML formatting

## Recovery Steps
1. docker compose restart alertmanager
2. Re-validate alertmanager.yml

## Escalation
- If alerts are not delivered, verify receiver credentials.
