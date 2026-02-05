source mltbenv/bin/activate
if [ -z "$SKIP_UPDATE" ]; then
    python3 update.py
else
    echo "Skipping update.py (SKIP_UPDATE set)"
fi
python3 -m bot
