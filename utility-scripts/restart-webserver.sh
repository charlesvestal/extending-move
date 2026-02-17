#!/bin/bash
set -euo pipefail

# Remote configuration
REMOTE_USER="ableton"
REMOTE_HOST="move.local"

# Absolute paths on the remote machine
PID_FILE="/data/UserData/extending-move/move-webserver.pid"
# Define the command to change directory and run the webserver unbuffered.
WEB_SERVER_CMD="cd /data/UserData/extending-move && PYTHONPATH=/data/UserData/extending-move python3 -u move-webserver.py"
LOG_FILE="/data/UserData/extending-move/move-webserver.log"

# Read the port from port.conf if present
CONFIG_FILE="/data/UserData/extending-move/port.conf"
if [ -f "$CONFIG_FILE" ]; then
  PORT=$(cat "$CONFIG_FILE")
else
  PORT=909
fi

echo "Restarting the webserver on ${REMOTE_HOST}..."

if [ -n "${SKIP_MODULE_WARMUP:-}" ]; then
  SSH_CMD="SKIP_MODULE_WARMUP=${SKIP_MODULE_WARMUP} bash -s"
else
  SSH_CMD="bash -s"
fi

ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "$SSH_CMD" <<'EOF'
set -euo pipefail

# Load port configuration on the remote machine
CONFIG_FILE="/data/UserData/extending-move/port.conf"
if [ -f "$CONFIG_FILE" ]; then
  PORT=$(cat "$CONFIG_FILE")
else
  PORT=909
fi

# Use the absolute paths
PID_FILE="/data/UserData/extending-move/move-webserver.pid"
WEB_SERVER_CMD="cd /data/UserData/extending-move && PYTHONPATH=/data/UserData/extending-move python3 -u move-webserver.py"
LOG_FILE="/data/UserData/extending-move/move-webserver.log"

# Kill any existing webserver process using the PID file if available
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    kill "$OLD_PID" || true
    sleep 1
    if kill -0 "$OLD_PID" 2>/dev/null; then
      kill -9 "$OLD_PID" || true
    fi
  fi
  rm -f "$PID_FILE"
else
  pkill -f 'python3 move-webserver.py' || true
fi

# Clean up any old log file
rm -f "$LOG_FILE"

# Start the webserver in the background using nohup for full detachment.
echo "Starting the webserver..."
cd /data/UserData/extending-move
nohup bash -c "$WEB_SERVER_CMD" > "$LOG_FILE" 2>&1 &

# Wait for PID file to be written by the webserver
for i in {1..10}; do
  if [ -f "$PID_FILE" ]; then
    NEW_PID=$(cat "$PID_FILE")
    break
  fi
  sleep 1
done

if [ -z "${NEW_PID:-}" ]; then
  echo "Error: PID file not created. Check logs:"
  cat "$LOG_FILE"
  exit 1
fi

# Confirm the process is running
if ! ps -p "$NEW_PID" > /dev/null; then
    echo "Error: Server failed to start. Check logs:"
    cat "$LOG_FILE"
    exit 1
fi

# Wait for the server to respond on configured port (allow time for warm-up)
# The webserver performs an extensive warm-up that can take close to a minute
# on first start. To avoid false negatives, increase the wait time to three
# minutes (180 seconds) to accommodate slower devices.
for i in {1..180}; do
    if command -v curl >/dev/null 2>&1; then
        if curl -sf http://localhost:${PORT}/ > /dev/null; then
            PORT_READY=true
            break
        fi
    elif command -v ss >/dev/null 2>&1; then
        if ss -tln | grep -q ":${PORT}"; then
            PORT_READY=true
            break
        fi
    else
        if netstat -tln | grep -q ":${PORT}"; then
            PORT_READY=true
            break
        fi
    fi
    sleep 1
done

if [ "${PORT_READY:-}" != "true" ]; then
    echo "Error: Server not listening on port ${PORT}. Check logs:"
    tail -n 20 "$LOG_FILE"
    exit 1
fi

echo "Webserver started successfully with PID: $NEW_PID"
EOF
