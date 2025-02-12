#!/bin/bash
set -euo pipefail

# Ensure we are running inside a Git repository.
if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
    echo "Error: This script must be run inside a Git repository."
    exit 1
fi

# Remote server configuration
REMOTE_USER="ableton"
REMOTE_HOST="move.local"
REMOTE_DIR="/data/UserData/extending-move"

echo "Ensuring remote directory '${REMOTE_DIR}' exists on ${REMOTE_HOST}..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '${REMOTE_DIR}'" || {
    echo "Error: Failed to create or access remote directory '${REMOTE_DIR}'."
    exit 1
}

# Check for files to copy.
# Use non-null separated output here to avoid warnings.
tracked=$(git ls-files)
untracked=$(git ls-files --others --exclude-standard)
if [ -z "$tracked" ] && [ -z "$untracked" ]; then
    echo "No files found to copy."
    exit 0
fi

echo "Copying working files (excluding ignored and Git history) to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}..."
# Get the repository root directory and script directory
REPO_ROOT=$(git rev-parse --show-toplevel)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# Change to the repository root
cd "${REPO_ROOT}"

echo "Creating project files archive..."
# Create a tar archive of the project files and stream it via SSH
tar -czf - \
    --exclude='.git' \
    --exclude='utility-scripts' \
    core handlers templates static move-webserver.py | \
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd '${REMOTE_DIR}' && tar -xzf -"

echo "Files copied successfully."

# Set proper permissions on the remote machine
echo "Setting proper permissions..."
ssh "${REMOTE_USER}@${REMOTE_HOST}" "chmod +x '${REMOTE_DIR}/move-webserver.py' && chmod -R 755 '${REMOTE_DIR}/static'"

# Restart the webserver using the utility script
"${SCRIPT_DIR}/restart-webserver.sh"
