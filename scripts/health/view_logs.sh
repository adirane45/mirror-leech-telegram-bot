#!/bin/bash
# Bot Log Viewer
# Usage: ./scripts/view_logs.sh [lines] [filter]
#   lines: number of lines to show (default: 50)
#   filter: grep pattern to filter logs

CONTAINER_ID="9ea93d6c31a9"
LINES=${1:-50}
FILTER=${2:-""}

LOG_FILE="/app/data/logs/log.txt"

echo "📋 Bot Logs - Last $LINES lines"
echo "================================"
echo

if [ -z "$FILTER" ]; then
    docker exec $CONTAINER_ID tail -n $LINES $LOG_FILE 2>/dev/null
else
    echo "🔍 Filtering for: $FILTER"
    echo
    docker exec $CONTAINER_ID tail -n $LINES $LOG_FILE 2>/dev/null | grep -i "$FILTER"
fi

echo
echo "================================"
echo "💡 Tips:"
echo "   - Show more lines: ./scripts/view_logs.sh 100"
echo "   - Filter errors: ./scripts/view_logs.sh 200 error"
echo "   - Watch live: docker exec $CONTAINER_ID tail -f $LOG_FILE"
