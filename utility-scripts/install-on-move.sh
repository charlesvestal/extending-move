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
echo "*   packages on your Move? This is UNSUPPORTED by Ableton.   *"
echo "*                                                            *"
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

# Port selection
echo "Choose a port for the webserver:" >&2
echo "1) 909 - New school (default)" >&2
echo "2) 808 - Old school" >&2
echo "3) 707 - Backbeat" >&2
echo "4) 606 - Vintage" >&2
echo "5) Custom" >&2
read -p "Selection [1]: " port_choice
case "$port_choice" in
    2) PORT=808 ;;
    3) PORT=707 ;;
    4) PORT=606 ;;
    5)
        read -p "Enter custom port number: " PORT
        ;;
    *) PORT=909 ;;
esac

# Write port to config file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
echo "$PORT" > "${PROJECT_ROOT}/port.conf"

# Remote configuration
REMOTE_USER="ableton"
REMOTE_HOST="move.local"

# Version check: ensure Move version is within tested range
HIGHEST_TESTED_VERSION="1.5.0"
INSTALLED_VERSION=$(ssh "${REMOTE_USER}@${REMOTE_HOST}" "/opt/move/Move -v" | awk '{print $3}')
# Determine if installed version exceeds highest tested
LATEST_VERSION=$(printf "%s\n%s\n" "$HIGHEST_TESTED_VERSION" "$INSTALLED_VERSION" | sort -V | tail -n1)
if [ "$LATEST_VERSION" != "$HIGHEST_TESTED_VERSION" ]; then
    read -p "Warning: Installed Move version ($INSTALLED_VERSION) is newer than highest tested ($HIGHEST_TESTED_VERSION). Continue? [y/N] " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        echo "Aborting installation."
        exit 1
    fi
fi

echo "Running remote setup commands on ${REMOTE_HOST} as ${REMOTE_USER}..."

ssh "${REMOTE_USER}@${REMOTE_HOST}" bash <<'EOF'
set -euo pipefail

# Create the temporary directory and set TMPDIR.
echo "Creating /data/UserData/tmp and setting TMPDIR..."
mkdir -p /data/UserData/tmp
export TMPDIR=/data/UserData/tmp
echo "TMPDIR is set to: $TMPDIR"

# Change to /data/UserData where we want to download get-pip.py.
cd /data/UserData

# Download get-pip.py using wget, overwriting if it exists.
echo "Downloading get-pip.py..."
wget -q -O get-pip.py https://bootstrap.pypa.io/get-pip.py

# Ensure that ~/.bash_profile sources ~/.bashrc so that Bash settings persist on login.
if ! grep -q "\.bashrc" ~/.bash_profile; then
    echo 'if [ -f ~/.bashrc ]; then . ~/.bashrc; fi' >> ~/.bash_profile
fi

# Add /data/UserData/.local/bin to PATH for this session.
export PATH="/data/UserData/.local/bin:$PATH"

# Persist the PATH update in ~/.bashrc if it's not already present.
if ! grep -q "/data/UserData/.local/bin" ~/.bashrc; then
    echo 'export PATH="/data/UserData/.local/bin:$PATH"' >> ~/.bashrc
fi

# Execute get-pip.py with python3 to install pip.
echo "Executing get-pip.py..."
python3 /data/UserData/get-pip.py


echo "Remote setup complete."
EOF

echo "Remote setup finished."

# Now, on the local machine, execute update-on-move.sh using bash explicitly.
echo "Running update-on-move.sh locally..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
if [ ! -f "${SCRIPT_DIR}/update-on-move.sh" ]; then
    echo "Error: update-on-move.sh not found in ${SCRIPT_DIR}"
    exit 1
fi
"${SCRIPT_DIR}/update-on-move.sh"

echo
echo "**************************************************************"
echo "*                                                            *"
echo "*   Deployment and remote setup complete.                    *"
echo "*                                                            *"
echo "*   Your new Move tools are now available at:                *"
echo "*   http://move.local:${PORT}                                    *"
echo "*                                                            *"
echo "**************************************************************"
echo
printf "Would you like to open the tools in your browser? (y/n): "
read -r response
if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
    open "http://move.local:${PORT}"
fi
