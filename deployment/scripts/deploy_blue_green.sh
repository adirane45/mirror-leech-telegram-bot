#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

COMPOSE=(docker compose -f "$PROJECT_ROOT/docker-compose.yml" -f "$PROJECT_ROOT/docker-compose.bluegreen.yml")
ACTIVE_FILE="$PROJECT_ROOT/.bluegreen_active"

if [[ -f "$ACTIVE_FILE" ]]; then
    CURRENT_COLOR="$(cat "$ACTIVE_FILE")"
else
    CURRENT_COLOR="blue"
fi

if [[ "$CURRENT_COLOR" == "blue" ]]; then
    TARGET_COLOR="green"
else
    TARGET_COLOR="blue"
fi

echo "Deploying new version to $TARGET_COLOR..."

# Stop legacy single app service to free ports
(docker compose -f "$PROJECT_ROOT/docker-compose.yml" stop app >/dev/null 2>&1) || true

"${COMPOSE[@]}" up -d "app-$TARGET_COLOR"

# Wait for app health
HEALTHY="false"
for i in $(seq 1 30); do
    if "${COMPOSE[@]}" exec -T "app-$TARGET_COLOR" curl -fsS http://localhost:8060/ >/dev/null 2>&1; then
        HEALTHY="true"
        break
    fi
    sleep 2
done

if [[ "$HEALTHY" != "true" ]]; then
    echo "New app ($TARGET_COLOR) failed health check. Keeping $CURRENT_COLOR active."
    exit 1
fi

echo "Switching traffic to $TARGET_COLOR..."
ACTIVE_COLOR="$TARGET_COLOR" "${COMPOSE[@]}" up -d web

# Verify proxy is serving traffic
PROXY_OK="false"
for i in $(seq 1 15); do
    if curl -fsS http://localhost:8060/ >/dev/null 2>&1; then
        PROXY_OK="true"
        break
    fi
    sleep 2
done

if [[ "$PROXY_OK" != "true" ]]; then
    echo "Proxy failed after switch. Rolling back to $CURRENT_COLOR."
    ACTIVE_COLOR="$CURRENT_COLOR" "${COMPOSE[@]}" up -d web
    exit 1
fi

# Stop old color after successful switch
"${COMPOSE[@]}" stop "app-$CURRENT_COLOR" >/dev/null 2>&1 || true

echo "$TARGET_COLOR" > "$ACTIVE_FILE"

echo "Blue/green deploy complete. Active: $TARGET_COLOR"
