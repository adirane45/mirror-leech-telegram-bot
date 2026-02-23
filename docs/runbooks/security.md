# Runbook: Security Incidents

## Scope
Guidance for suspected compromise or credential leak.

## Immediate Actions
1. Rotate BOT_TOKEN and API keys
2. Rotate ARIA2_SECRET, QB_PASSWORD, GRAFANA_ADMIN_PASSWORD
3. Restart affected services

## Evidence Collection
- Export logs: docker compose logs > incident.log
- Snapshot configs and env files

## Recovery Steps
- Restore from last known good backup
- Verify services and audit logs

## Escalation
- Conduct postmortem and record actions
