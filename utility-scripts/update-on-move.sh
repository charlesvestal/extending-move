#!/usr/bin/env bash
set -euo pipefail

# Check for dev mode
DEV_MODE=false
for arg in "$@"; do
  if [ "$arg" = "--dev" ]; then
    DEV_MODE=true
  fi
done

# --- Figure out where we live ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if git rev-parse --show-toplevel > /dev/null 2>&1; then
  PROJECT_ROOT=$(git rev-parse --show-toplevel)
else
  PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
cd "$PROJECT_ROOT"

# Remote server configuration
REMOTE_USER="ableton"
REMOTE_HOST="move.local"
REMOTE_DIR="/data/UserData/extending-move"

# --- Ensure static git binary is present locally ---
GIT_BIN="${PROJECT_ROOT}/bin/git"
REMOTE_GIT_BIN="/data/UserData/bin/git"

if [ ! -f "$GIT_BIN" ]; then
  if ssh -o BatchMode=yes -o ConnectTimeout=5 "${REMOTE_USER}@${REMOTE_HOST}" "[ -f '${REMOTE_GIT_BIN}' ]" 2>/dev/null; then
    echo "Copying static git from device..."
    mkdir -p "${PROJECT_ROOT}/bin"
    scp "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_GIT_BIN}" "$GIT_BIN" >/dev/null
  else
    echo "Downloading static git binary..."
    mkdir -p "${PROJECT_ROOT}/bin"
    curl -L -o "$GIT_BIN" \
      https://raw.githubusercontent.com/EXALAB/git-static/master/output/amd64/bin/git
  fi
  chmod +x "$GIT_BIN"
fi

# --- Remote server configuration (already defined above) ---

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

# --- Install git on the device if needed ---
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${REMOTE_USER}@${REMOTE_HOST}" "[ -x '${REMOTE_GIT_BIN}' ]" 2>/dev/null; then
  echo "Installing static git on device..."
  ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p \"$(dirname \"${REMOTE_GIT_BIN}\")\""
  scp "$GIT_BIN" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_GIT_BIN}" >/dev/null
  ssh "${REMOTE_USER}@${REMOTE_HOST}" "chmod +x '${REMOTE_GIT_BIN}'"
fi

# --- Ensure destination is a git repository ---
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "${REMOTE_USER}@${REMOTE_HOST}" "[ -d '${REMOTE_DIR}/.git' ]" 2>/dev/null; then
  read -p "${REMOTE_DIR} is not a git repo. Remove existing files and clone fresh? [y/N] " confirm
  if [[ $confirm =~ ^[Yy]$ ]]; then
    echo "Removing existing files on device..."
    ssh -T "${REMOTE_USER}@${REMOTE_HOST}" "rm -rf '${REMOTE_DIR}'"
  else
    echo "Aborting."
    exit 1
  fi
fi

# --- Clone or update repository on the device ---
ssh -T "${REMOTE_USER}@${REMOTE_HOST}" <<'EOF'
set -euo pipefail
mkdir -p ~/extending-move
if ! grep -q "$HOME/bin" ~/.bashrc; then
  echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
fi
export PATH="$HOME/bin:$PATH"
if [ -d ~/extending-move/.git ]; then
  if ! ~/bin/git -C ~/extending-move pull --ff-only; then
    GIT_FAILED=true
  fi
else
  if ! ~/bin/git clone https://github.com/charlesvestal/extending-move.git ~/extending-move; then
    GIT_FAILED=true
  fi
fi

if [ "${GIT_FAILED:-}" = true ]; then
  echo "Git failed, falling back to tarball..."
  TMPDIR=$(mktemp -d)
  TARFILE="$TMPDIR/repo.tar.gz"
  if command -v curl >/dev/null 2>&1; then
    curl -L -o "$TARFILE" https://codeload.github.com/charlesvestal/extending-move/tar.gz/refs/heads/main
  elif command -v wget >/dev/null 2>&1; then
    wget -O "$TARFILE" https://codeload.github.com/charlesvestal/extending-move/tar.gz/refs/heads/main
  else
    echo "Neither curl nor wget found on device"
    exit 1
  fi
  rm -rf ~/extending-move
  mkdir -p ~/extending-move
  tar -xzf "$TARFILE" -C "$TMPDIR"
  mv "$TMPDIR"/extending-move-main/* ~/extending-move/
  rm -rf "$TMPDIR"
fi
cp -r /opt/move/HttpRoot/fonts ~/extending-move/static/
chmod +x ~/extending-move/move-webserver.py
chmod -R 755 ~/extending-move/static
chmod -R 755 ~/extending-move/bin
EOF

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
export PATH="/data/UserData/bin:${REMOTE_DIR}/bin:${REMOTE_DIR}/bin/rubberband:\$PATH"
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
