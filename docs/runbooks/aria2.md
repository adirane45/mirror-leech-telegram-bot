# Runbook: aria2

## Scope
Download engine for direct and torrent downloads.

## Health Signals
- HTTP 200 on RPC: http://localhost:6800/jsonrpc
- Container health: docker compose ps aria2

## Common Issues
### Unauthorized RPC
- Ensure RPC_SECRET matches ARIA2_SECRET in env
- Verify healthcheck passes

## Recovery Steps
1. docker compose restart aria2
2. Validate RPC:
   curl -f -X POST -H 'Content-Type: application/json' \
     --data '{"jsonrpc":"2.0","id":"mltb","method":"aria2.getVersion","params":["token:'"$RPC_SECRET"'"]}' \
     http://localhost:6800/jsonrpc

## Escalation
- If RPC remains unauthorized, rotate secret and restart app.
