# Runbook: OpenTelemetry Collector

## Scope
OTLP receiver on port 4318.

## Health Signals
- docker compose ps otel-collector

## Common Issues
### No traces
- Verify ENABLE_OTEL_TRACING=true
- Check OTEL_EXPORTER_OTLP_ENDPOINT

## Recovery Steps
1. docker compose restart otel-collector
2. Validate config at deployment/otel-collector-config.yml

## Escalation
- Check app logs for tracing initialization errors.
