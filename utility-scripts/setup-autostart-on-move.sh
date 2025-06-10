#!/bin/bash
set -euo pipefail

MOVE_KEY_PATH="$HOME/.ssh/move_key"
REMOTE_USER_ROOT="root"
REMOTE_USER_ABLETON="ableton"
REMOTE_HOST="move.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
if [ -f "${PROJECT_ROOT}/port.conf" ]; then
    PORT=$(cat "${PROJECT_ROOT}/port.conf")
else
    PORT=909
fi

# --- Set up auto-start functionality ---
echo "--------------------------------------------------------------------------"
echo "Setup Auto-Start for 'extending-move' Webserver"
echo "--------------------------------------------------------------------------"
echo "This step will configure the 'extending-move' webserver to start automatically"
echo "when your Ableton Move boots up."
echo ""
echo "The auto-start configuration may not persist through Move firmware upgrades."
echo ""
echo "NOTE: This script will perform commands as the ROOT user on your Move."
echo ""
echo "--------------------------------------------------------------------------"
echo ""

echo "Connecting to ${REMOTE_HOST} as root to set up auto-start..."
echo "Attempting to use key: ${MOVE_KEY_PATH}"

# Save init script content to a temporary file
TEMP_INIT_SCRIPT=$(mktemp)
cat > "$TEMP_INIT_SCRIPT" << 'EOINITSCRIPT'
#!/bin/sh
### BEGIN INIT INFO
# Provides:          ableton-startup
# Required-Start:    $local_fs $network
# Required-Stop:     $local_fs
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Start Ableton Python script at boot
### END INIT INFO

case "$1" in
  start)
    cd /data/UserData/extending-move
    su - ableton -s /bin/sh -c "cd /data/UserData/extending-move ; python3 move-webserver.py >> startup.log 2>&1 &"
    ;;
  stop)
    pkill -u ableton -f move-webserver.py
    ;;
  restart)
    $0 stop
    sleep 1
    $0 start
    ;;
  status)
    if pgrep -u ableton -f move-webserver.py >/dev/null; then
      echo "Running"
    else
      echo "Not running"
      exit 1
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 2
    ;;
esac

exit 0
EOINITSCRIPT

INIT_SCRIPT_NAME="ableton-startup"

echo "Uploading init script to ${REMOTE_HOST}..."
scp -i "${MOVE_KEY_PATH}" "$TEMP_INIT_SCRIPT" "${REMOTE_USER_ROOT}@${REMOTE_HOST}:/tmp/${INIT_SCRIPT_NAME}"

rm "$TEMP_INIT_SCRIPT"

ssh -i "${MOVE_KEY_PATH}" "${REMOTE_USER_ROOT}@${REMOTE_HOST}" << EOF
set -e
echo "Moving init script to /etc/init.d/${INIT_SCRIPT_NAME}..."
mv "/tmp/${INIT_SCRIPT_NAME}" "/etc/init.d/${INIT_SCRIPT_NAME}"
chmod +x "/etc/init.d/${INIT_SCRIPT_NAME}"

echo "Enabling ${INIT_SCRIPT_NAME} service..."
if command -v update-rc.d > /dev/null; then
    update-rc.d -f ableton-startup-extending-move remove >/dev/null 2>&1 || true
    update-rc.d -f extending-move-startup remove >/dev/null 2>&1 || true
    update-rc.d -f "${INIT_SCRIPT_NAME}" remove >/dev/null 2>&1 || true
    update-rc.d "${INIT_SCRIPT_NAME}" defaults
    echo "Service ${INIT_SCRIPT_NAME} enabled using update-rc.d."
else
    echo "WARNING: 'update-rc.d' command not found."
    echo "Auto-start might not be enabled."
fi

echo "Starting the service..."
if "/etc/init.d/${INIT_SCRIPT_NAME}" start; then
    echo "Service ${INIT_SCRIPT_NAME} started successfully."
else
    echo "Failed to start the service. Check logs: /data/UserData/extending-move/startup.log"
fi
EOF

echo ""
echo "--------------------------------------------------------------------------"
echo "Auto-start Setup Complete"
echo "--------------------------------------------------------------------------"
echo "If all went well, the 'extending-move' webserver should now be running and"
echo "configured to start automatically when your Ableton Move boots up."
echo "You can verify by:"
echo "1. Checking http://${REMOTE_HOST}:${PORT} in your browser."
echo "2. Rebooting your Move and then checking the link again."
echo ""
echo "Remember, this auto-start configuration may not persist through Move firmware upgrades."
echo "--------------------------------------------------------------------------"
echo ""
echo "All operations finished. Enjoy your extended Move!"

exit 0
