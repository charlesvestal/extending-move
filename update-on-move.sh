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
# (Tracked files are output by 'git ls-files'.
#  Untracked-but-not-ignored files are output by 'git ls-files --others --exclude-standard'.)
tracked=$(git ls-files -z)
untracked=$(git ls-files --others --exclude-standard -z)
if [ -z "$tracked" ] && [ -z "$untracked" ]; then
    echo "No files found to copy."
    exit 0
fi

echo "Copying working files (excluding ignored and Git history) to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}..."
# Create a tar archive of the files (using null-delimited file names) and stream it via SSH.
( git ls-files -z && git ls-files --others --exclude-standard -z ) | \
    tar --null -T - -czf - | \
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "tar -xz -C '${REMOTE_DIR}'"

echo "Files copied successfully."

# Restart the webserver
sh restart-webserver.sh