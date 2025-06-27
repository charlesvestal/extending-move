#!/usr/bin/env bash
set -euo pipefail

# Check for flags
DEV_MODE=false
OVERWRITE=false
for arg in "$@"; do
  case "$arg" in
    --dev)
      DEV_MODE=true
      ;;
    --overwrite)
      OVERWRITE=true
      ;;
  esac
done

# --- Figure out where we live ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if git rev-parse --show-toplevel > /dev/null 2>&1; then
  PROJECT_ROOT=$(git rev-parse --show-toplevel)
else
  PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "$PROJECT_ROOT"

# Record the current commit SHA on the remote so the web based updater knows
# which version is installed. If git is not available this step is skipped.
CURRENT_SHA=""
CURRENT_BRANCH="main"
if git rev-parse HEAD > /dev/null 2>&1; then
  CURRENT_SHA=$(git rev-parse HEAD)
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi

# --- Remote server configuration ---
REMOTE_USER="ableton"
REMOTE_HOST="move.local"
REMOTE_DIR="/data/UserData/extending-move"

# --- Version check: ensure Move version is within tested range ---
HIGHEST_TESTED_VERSION="1.5.1"
INSTALLED_VERSION=$(ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "/opt/move/Move -v" | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+')
# Determine if installed version exceeds highest tested
LATEST_VERSION=$(printf "%s\n%s\n" "$HIGHEST_TESTED_VERSION" "$INSTALLED_VERSION" | sort -V | tail -n1)
if [ "$LATEST_VERSION" != "$HIGHEST_TESTED_VERSION" ]; then
  read -p "Warning: Installed Move ($INSTALLED_VERSION) > tested ($HIGHEST_TESTED_VERSION). Continue? [y/N] " confirm
  if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Aborting."
    exit 1
  fi
fi

# --- Ensure remote directory exists ---
if [ "$OVERWRITE" = true ]; then
  echo "Overwrite enabled: deleting ${REMOTE_DIR} on ${REMOTE_HOST}…"
  ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "rm -rf '${REMOTE_DIR}'"
fi
echo "Creating ${REMOTE_DIR} on ${REMOTE_HOST}…"
ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '${REMOTE_DIR}'"

# --- Archive & copy your project files (excludes .git & utility-scripts) ---
echo "Uploading project files to ${REMOTE_HOST}:${REMOTE_DIR}…"
tar czf - \
  --exclude='.git' \
  core handlers templates_jinja static examples bin utility-scripts \
  move-webserver.py requirements.txt port.conf | \
ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "cd '${REMOTE_DIR}' && tar xzf - && cp -r /opt/move/HttpRoot/fonts static/"

echo "Files copied."

if [ -n "$CURRENT_SHA" ]; then
  echo "Recording current version ${CURRENT_SHA} (${CURRENT_BRANCH}) on remote..."
  ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "echo '${CURRENT_SHA}' > '${REMOTE_DIR}/last_sha.txt' && echo '${CURRENT_BRANCH}' > '${REMOTE_DIR}/last_branch.txt'"

  echo "Recording current version ${CURRENT_SHA} on remote..."
  ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "echo '${CURRENT_SHA}' > '${REMOTE_DIR}/last_sha.txt'"
fi

# --- Fix permissions remotely (now with proper path expansion) ---
echo "Setting permissions on remote…"
ssh -T "${REMOTE_USER}@${REMOTE_HOST}" <<EOF
chmod +x "${REMOTE_DIR}/move-webserver.py"
chmod -R 755 "${REMOTE_DIR}/static"
chmod -R 755 "${REMOTE_DIR}/bin"
EOF

if [ "$DEV_MODE" = true ]; then
  echo "Dev mode: skipping pip install"
else
  echo "Installing requirements with pip on remote..."
  ssh -T "${REMOTE_USER}@${REMOTE_HOST}" <<EOF
export TMPDIR=/data/UserData/tmp
export PATH="${REMOTE_DIR}/bin/rubberband:\$PATH"
echo "TMPDIR is set to: \$TMPDIR"
pip install --no-cache-dir -r "${REMOTE_DIR}/requirements.txt" | grep -v 'already satisfied'
EOF
fi

# --- Restart the webserver ---
if [ "$DEV_MODE" = true ]; then
  echo "Dev mode: skipping module warm-up"
  SKIP_MODULE_WARMUP=1 "${SCRIPT_DIR}/restart-webserver.sh"
  echo "Tailing remote log..."
  ssh -t "${REMOTE_USER}@${REMOTE_HOST}" "tail -f '${REMOTE_DIR}/move-webserver.log'"
else
  "${SCRIPT_DIR}/restart-webserver.sh"
fi
