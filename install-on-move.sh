#!/bin/bash
set -euo pipefail

# Clear the screen and display a prominent warning message.
clear
echo ""
echo "**************************************************************"
echo "*                                                            *"
echo "*   WARNING:                                                 *"
echo "*                                                            *"
echo "*   Are you sure you want to install the extending-move      *"
echo "*   packages on your Move? This is UNSUPPORTED by Ableton    *"
echo "*   and may cause irreparable damage to your device.         *"
echo "*   The authors of these packages accept no liability for    *"
echo "*   any damage you incur by proceeding.                      *"
echo "*                                                            *"
echo "**************************************************************"
echo ""
echo "Type 'yes' to proceed: "
read -r response
if [ "$response" != "yes" ]; then
    echo "Installation aborted."
    exit 1
fi

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

# Download get-pip.py using wget, overwriting if it exists.
echo "Downloading get-pip.py..."
wget -q -O get-pip.py https://bootstrap.pypa.io/get-pip.py

# Execute get-pip.py with python3 to install pip
echo "Executing get-pip.py..."
python3 /data/UserData/get-pip.py

# Install scipy using pip (without using the cache)
echo "Installing scipy with pip..."
pip install --no-cache-dir scipy
EOF

echo "Remote setup finished."

# Now, on the local machine, execute update-on-move.sh using bash explicitly.
echo "Running update-on-move.sh locally..."
bash ./update-on-move.sh

echo "Deployment and remote setup complete."