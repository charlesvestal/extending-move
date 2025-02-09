#!/bin/bash
set -euo pipefail

# Remote configuration
REMOTE_USER="ableton"
REMOTE_HOST="move.local"

echo "Running remote setup commands on ${REMOTE_HOST} as ${REMOTE_USER}..."

ssh "${REMOTE_USER}@${REMOTE_HOST}" bash <<'EOF'
set -euo pipefail
# Create the temporary directory and set TMPDIR
echo "Creating /data/UserData/tmp and setting TMPDIR..."
mkdir -p /data/UserData/tmp
export TMPDIR=/data/UserData/tmp
echo "TMPDIR is set to: $TMPDIR"

# Change to /data/UserData where we want to download get-pip.py
cd /data/UserData

# Download get-pip.py using wget
echo "Downloading get-pip.py..."
wget -q https://bootstrap.pypa.io/get-pip.py

# Execute get-pip.py with python3 to install pip
echo "Executing get-pip.py..."
python3 /data/UserData/get-pip.py
rm /data/UserData/get-pip.py

# Install scipy using pip (without using the cache)
echo "Installing scipy with pip..."
pip install --no-cache-dir scipy

echo "Remote setup complete."
EOF

echo "Remote setup finished."

# Now, on the local machine, execute update-on-move.sh
echo "Running update-on-move.sh locally..."
sh update-on-move.sh

echo "Deployment and remote setup complete."