#!/bin/bash
set -euo pipefail

# Remote configuration
REMOTE_USER="ableton"
REMOTE_HOST="move.local"

# Absolute paths on the remote machine
PID_FILE="/data/UserData/extending-move/move-webserver.pid"
# Define the command to change directory and run the webserver.
WEB_SERVER_CMD="cd /data/UserData/extending-move && PYTHONPATH=/data/UserData/extending-move python3 move-webserver.py"
LOG_FILE="/data/UserData/extending-move/move-webserver.log"

echo "Restarting the webserver on ${REMOTE_HOST}..."

ssh "${REMOTE_USER}@${REMOTE_HOST}" bash <<'EOF'
set -euo pipefail

# Use the absolute paths
PID_FILE="/data/UserData/extending-move/move-webserver.pid"
WEB_SERVER_CMD="cd /data/UserData/extending-move && PYTHONPATH=/data/UserData/extending-move python3 move-webserver.py"
LOG_FILE="/data/UserData/extending-move/move-webserver.log"

# Kill any existing webserver processes
pkill -f 'python3 move-webserver.py' || true
rm -f "$PID_FILE"

# Clean up any old log file
rm -f "$LOG_FILE"

# Start the webserver in the background using nohup and setsid for full detachment.
echo "Starting the webserver..."
cd /data/UserData/extending-move
nohup setsid bash -c "$WEB_SERVER_CMD" > "$LOG_FILE" 2>&1 &
NEW_PID=$!

# Wait a moment for the server to start
sleep 2

# Check if the server started successfully
if ! ps -p $NEW_PID > /dev/null; then
    echo "Error: Server failed to start. Check logs:"
    cat "$LOG_FILE"
    exit 1
fi

# Verify the server is listening
if ! netstat -tln | grep -q ':666'; then
    echo "Error: Server not listening on port 666. Check logs:"
    cat "$LOG_FILE"
    exit 1
fi

echo "Webserver started successfully with PID: $NEW_PID"
EOF
