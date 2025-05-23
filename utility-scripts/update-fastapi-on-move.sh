#!/usr/bin/env bash
set -euo pipefail

# --- Figure out where we live ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if git rev-parse --show-toplevel > /dev/null 2>&1; then
  PROJECT_ROOT=$(git rev-parse --show-toplevel)
else
  PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "$PROJECT_ROOT"

# --- Remote server configuration ---
REMOTE_USER="ableton"
REMOTE_HOST="move.local"
REMOTE_DIR="/data/UserData/extending-move"

# --- Version check: ensure Move version is within tested range ---
HIGHEST_TESTED_VERSION="1.5.0b5"
INSTALLED_VERSION=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "/opt/move/Move -v" | awk '{print $3}')
if ! printf "%s\n%s\n" "$HIGHEST_TESTED_VERSION" "$INSTALLED_VERSION" | sort -V | head -n1 | grep -qx "$HIGHEST_TESTED_VERSION"; then
  read -p "Warning: Installed Move ($INSTALLED_VERSION) > tested ($HIGHEST_TESTED_VERSION). Continue? [y/N] " confirm
  if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Aborting."
    exit 1
  fi
fi

# --- Ensure remote directory exists ---
echo "Creating ${REMOTE_DIR} on ${REMOTE_HOST}…"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '${REMOTE_DIR}'"

# --- Archive & copy FastAPI project files ---
echo "Uploading FastAPI project files to ${REMOTE_HOST}:${REMOTE_DIR}…"
tar czf - \
  --exclude='.git' \
  --exclude='utility-scripts' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='uploads' \
  core handlers templates static app main.py start_fastapi.py requirements_new.txt | \
ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd '${REMOTE_DIR}' && tar xzf - && cp -r /opt/move/HttpRoot/fonts static/"

echo "FastAPI files copied."

# --- Fix permissions remotely ---
echo "Setting permissions on remote…"
ssh "${REMOTE_USER}@${REMOTE_HOST}" <<EOF
chmod +x "${REMOTE_DIR}/main.py"
chmod +x "${REMOTE_DIR}/start_fastapi.py"
chmod -R 755 "${REMOTE_DIR}/static"
chmod -R 755 "${REMOTE_DIR}/templates"
chmod -R 755 "${REMOTE_DIR}/app"
EOF

echo "Installing FastAPI requirements with pip on remote..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" <<EOF
export TMPDIR=/data/UserData/tmp
echo "TMPDIR is set to: \$TMPDIR"
pip install --no-cache-dir -r "${REMOTE_DIR}/requirements_new.txt"
EOF

# --- Stop any existing webserver ---
echo "Stopping existing webserver..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "pkill -f 'move-webserver.py' || true"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "pkill -f 'uvicorn main:app' || true"

# --- Start the FastAPI webserver ---
echo "Starting FastAPI webserver..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" <<EOF
cd "${REMOTE_DIR}"
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 909 > /tmp/fastapi-webserver.log 2>&1 &
echo "FastAPI webserver started on port 909"
EOF

echo "FastAPI deployment complete!"
echo "The server should be available at http://move.local:909"
echo "Check logs with: ssh ${REMOTE_USER}@${REMOTE_HOST} 'tail -f /tmp/fastapi-webserver.log'"
