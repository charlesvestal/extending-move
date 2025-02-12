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

# Check if the PID file exists and attempt to stop the process
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Found webserver PID: $PID. Attempting to stop it gracefully..."
    
    # Send SIGTERM
    kill "$PID" || echo "Warning: Failed to send SIGTERM to process $PID."
    
    # Wait up to 10 seconds for graceful shutdown
    TIMEOUT=10
    while kill -0 "$PID" 2>/dev/null && [ $TIMEOUT -gt 0 ]; do
        sleep 1
        TIMEOUT=$((TIMEOUT - 1))
    done
    
    # If still running, force kill it
    if kill -0 "$PID" 2>/dev/null; then
        echo "Process did not terminate gracefully; forcing termination."
        kill -9 "$PID"
    else
        echo "Webserver process $PID terminated gracefully."
    fi
    
    # Remove the PID file.
    rm -f "$PID_FILE"
else
    echo "No PID file found; webserver may not be running."
fi

# Start the webserver in the background using nohup and setsid for full detachment.
echo "Starting the webserver..."
nohup setsid bash -c "$WEB_SERVER_CMD" > "$LOG_FILE" 2>&1 &
NEW_PID=$!
echo "Webserver started with PID: $NEW_PID"
EOF
