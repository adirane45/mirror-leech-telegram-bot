#!/bin/bash
# Auto-Cleanup Service for Bot Downloads
# Runs continuously and cleans old files

CONTAINER_ID="9ea93d6c31a9"
DOWNLOAD_DIR="/app/downloads"
DAYS_OLD=1
CHECK_INTERVAL=3600  # 1 hour

echo "🧹 Starting auto-cleanup service..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Container: $CONTAINER_ID"
echo "   Directory: $DOWNLOAD_DIR"
echo "   Remove files older than: $DAYS_OLD day(s)"
echo "   Check interval: $CHECK_INTERVAL seconds (1 hour)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start cleanup service in container
docker exec -d $CONTAINER_ID sh -c "
while true; do
    echo \"\$(date): Cleaning old downloads...\"
    find $DOWNLOAD_DIR -type f -mtime +$DAYS_OLD -delete 2>/dev/null
    find $DOWNLOAD_DIR -type d -empty -delete 2>/dev/null
    sleep $CHECK_INTERVAL
done
"

if [ $? -eq 0 ]; then
    echo "✅ Auto-cleanup service started successfully!"
    echo
    echo "📊 Service Details:"
    echo "   - Runs in background inside container"
    echo "   - Checks every hour"
    echo "   - Removes files older than $DAYS_OLD day"
    echo "   - Also removes empty directories"
    echo
    echo "🔍 To check if running:"
    echo "   docker exec $CONTAINER_ID ps aux | grep 'find $DOWNLOAD_DIR'"
    echo
    echo "⚠️  To stop (if needed):"
    echo "   docker exec $CONTAINER_ID pkill -f 'find $DOWNLOAD_DIR'"
else
    echo "❌ Failed to start auto-cleanup service"
    exit 1
fi
