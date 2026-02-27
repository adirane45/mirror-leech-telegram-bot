#!/bin/bash
# Script to set qBittorrent password persistently

set -e

CONFIG_DIR="/config/qBittorrent"
CONF_FILE="${CONFIG_DIR}/qBittorrent.conf"
TEMP_PASS_LOG="/tmp/qb_temp_pass.log"

echo "[QB-INIT] Waiting for qBittorrent to start..."
for i in {1..60}; do
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8090/ | grep -q "200\|302\|401"; then
        echo "[QB-INIT] qBittorrent is responding"
        break
    fi
    sleep 1
done

# Wait a bit more for full initialization
sleep 5

# Get the temporary password from docker logs
if [ -f "/proc/1/fd/1" ]; then
    TEMP_PASS=$(cat /proc/1/fd/1 2>/dev/null | grep -o "temporary password is provided for this session: [^ ]*" | tail -1 | awk '{print $NF}' || echo "")
fi

if [ -z "$TEMP_PASS" ]; then
    echo "[QB-INIT] Could not find temporary password, trying default: mltbmltb"
    TEMP_PASS="mltbmltb"
fi

echo "[QB-INIT] Using password: $TEMP_PASS"

# Try to set password and save config
if [ -f "$CONF_FILE" ]; then
    echo "[QB-INIT] Setting credentials in config file"
    
    # Use sed to set the password hash (base64 encoded)
    # For now, set it to empty to allow unauthenticated access from local network
    sed -i 's/^WebUI\\Password_PBKDF2=.*/WebUI\\Password_PBKDF2=/g' "$CONF_FILE"
    
    # Verify it was set
    if grep -q "^WebUI\\\\Password_PBKDF2=$" "$CONF_FILE"; then
        echo "[QB-INIT] ✅ Password cleared successfully"
    fi
fi

echo "[QB-INIT] Complete - qBittorrent should now be accessible"
