# Runbook: qBittorrent

## Scope
Torrent engine with WebUI on port 8090.

## Health Signals
- HTTP 200 on http://localhost:8090/
- Container health: docker compose ps qbittorrent

## Common Issues
### Login fails
- Verify WEBUI_USERNAME/WEBUI_PASSWORD in env
- Check logs for temporary password on first boot

## Recovery Steps
1. docker compose restart qbittorrent
2. Reset credentials in config volume if needed

## Escalation
- If WebUI fails, verify port 8090 is free.
