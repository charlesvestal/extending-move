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
HIGHEST_TESTED_VERSION="1.5.0"
INSTALLED_VERSION=$(ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "/opt/move/Move -v" | awk '{print $3}')
if ! printf "%s\n%s\n" "$HIGHEST_TESTED_VERSION" "$INSTALLED_VERSION" | sort -V | head -n1 | grep -qx "$HIGHEST_TESTED_VERSION"; then
  read -p "Warning: Installed Move ($INSTALLED_VERSION) > tested ($HIGHEST_TESTED_VERSION). Continue? [y/N] " confirm
  if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Aborting."
    exit 1
  fi
fi

# --- Ensure remote directory exists ---
echo "Creating ${REMOTE_DIR} on ${REMOTE_HOST}…"
ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '${REMOTE_DIR}'"

# --- Archive & copy your project files (excludes .git & utility-scripts) ---
echo "Uploading project files to ${REMOTE_HOST}:${REMOTE_DIR}…"
tar czf - \
  --exclude='.git' \
  --exclude='utility-scripts' \
  core handlers templates_jinja static examples bin \
  move-webserver.py requirements.txt | \
ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "cd '${REMOTE_DIR}' && tar xzf - && cp -r /opt/move/HttpRoot/fonts static/"

echo "Files copied."

# --- Fix permissions remotely (now with proper path expansion) ---
echo "Setting permissions on remote…"
ssh -T "${REMOTE_USER}@${REMOTE_HOST}" <<EOF
chmod +x "${REMOTE_DIR}/move-webserver.py"
chmod -R 755 "${REMOTE_DIR}/static"
chmod -R 755 "${REMOTE_DIR}/bin"
EOF

echo "Installing requirements with pip on remote..."
ssh -T "${REMOTE_USER}@${REMOTE_HOST}" <<EOF
export TMPDIR=/data/UserData/tmp
export PATH="${REMOTE_DIR}/bin/rubberband:\$PATH"
echo "TMPDIR is set to: \$TMPDIR"
pip install --no-cache-dir -r "${REMOTE_DIR}/requirements.txt" | grep -v 'already satisfied'
EOF

# --- Restart the webserver ---
"${SCRIPT_DIR}/restart-webserver.sh"
