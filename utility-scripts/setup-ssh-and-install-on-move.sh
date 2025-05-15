#!/bin/bash
set -euo pipefail

# Configuration
MOVE_KEY_PATH="$HOME/.ssh/move_key"
REMOTE_USER_ABLETON="ableton"
REMOTE_USER_ROOT="root" # For autostart
REMOTE_HOST="move.local"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo "Starting SSH key setup and installation for Ableton Move (macOS)..."
echo "This script will guide you through:"
echo "1. Generating an SSH key for your Move."
echo "2. Configuring your local SSH to use this key for move.local."
echo "3. Adding the public key to your Move."
echo "4. Running the main 'extending-move' installation."
echo "5. Setting up auto-start for the 'extending-move' server on your Move."
echo ""

# --- 1. Generate SSH Key ---
if [ -f "$MOVE_KEY_PATH" ]; then
    echo "SSH key $MOVE_KEY_PATH already exists."
    read -p "Do you want to overwrite it? (y/N): " overwrite_key
    if [[ ! "$overwrite_key" =~ ^[Yy]$ ]]; then
        echo "Using existing key $MOVE_KEY_PATH."
    else
        echo "Overwriting existing key $MOVE_KEY_PATH..."
        ssh-keygen -t ed25519 -f "$MOVE_KEY_PATH" -N "" -C "move_key_for_ableton_move"
        echo "New SSH key generated at $MOVE_KEY_PATH and $MOVE_KEY_PATH.pub."
    fi
else
    echo "Generating new SSH key for Move at $MOVE_KEY_PATH..."
    ssh-keygen -t ed25519 -f "$MOVE_KEY_PATH" -N "" -C "move_key_for_ableton_move" # -N "" for no passphrase
    echo "SSH key generated: $MOVE_KEY_PATH and $MOVE_KEY_PATH.pub."
fi
echo ""

# --- 2. Add SSH key to ssh-agent and configure ~/.ssh/config ---
echo "Configuring local SSH settings..."

# Start ssh-agent if not already running (output an informational message)
if ! pgrep -u "$USER" ssh-agent > /dev/null; then
    echo "Starting ssh-agent..."
    eval "$(ssh-agent -s)" > /dev/null
else
    echo "ssh-agent is already running."
fi

# Ensure ~/.ssh directory exists
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# Configure ~/.ssh/config for move.local
CONFIG_FILE="$HOME/.ssh/config"
TEMP_CONFIG=$(mktemp)

if [ ! -f "$CONFIG_FILE" ]; then
    touch "$CONFIG_FILE"
    chmod 600 "$CONFIG_FILE"
fi

# Backup original config
cp "$CONFIG_FILE" "${CONFIG_FILE}.bak_move_setup_$(date +%Y%m%d_%H%M%S)"
echo "Backed up existing SSH config to ${CONFIG_FILE}.bak_move_setup_..."

# Use awk to rebuild, removing old `move.local` block and adding ours at the end.
awk -v host_to_process="${REMOTE_HOST}" '
    BEGIN { in_host_block = 0 }
    # Check if the line starts with "Host" possibly preceded by whitespace
    /^[ \t]*Host[ \t]+/ {
        if ($2 == host_to_process) {
            in_host_block = 1 # Entering the block for our host
        } else {
            in_host_block = 0 # Entering a block for a different host
        }
    }
    # If we are in the block for our host, skip printing the line
    # Otherwise, print the line
    !in_host_block { print }
' "$CONFIG_FILE" > "$TEMP_CONFIG"

# Append our new/updated configuration block
{
    echo "" # Ensure it starts on a new line if TEMP_CONFIG was not empty
    echo "Host ${REMOTE_HOST}"
    echo "  AddKeysToAgent yes"
    echo "  IdentityFile ${MOVE_KEY_PATH}"
    echo "  HostName ${REMOTE_HOST}" # Explicitly set HostName
} >> "$TEMP_CONFIG"

mv "$TEMP_CONFIG" "$CONFIG_FILE"
chmod 600 "$CONFIG_FILE"
echo "Updated SSH config ($CONFIG_FILE) for ${REMOTE_HOST} to use ${MOVE_KEY_PATH} (user not defaulted)."

# Add key to ssh-agent.
# Since we used -N "" for no passphrase, --apple-use-keychain is not strictly needed
# for storing passphrase, but AddKeysToAgent yes + ssh-add handles loading.
# Check if key is already added to avoid "duplicate" errors/messages.
if ! ssh-add -l | grep -q "$MOVE_KEY_PATH"; then
    ssh-add "$MOVE_KEY_PATH"
    echo "SSH key $MOVE_KEY_PATH added to ssh-agent."
else
    echo "SSH key $MOVE_KEY_PATH is already added to ssh-agent."
fi
echo ""

# --- 3. Display Public Key and Instructions ---
echo "--------------------------------------------------------------------------"
echo "ACTION REQUIRED: Add the Public Key to Your Ableton Move"
echo "--------------------------------------------------------------------------"
echo "Your Ableton Move public SSH key ($MOVE_KEY_PATH.pub) is:"
echo ""
cat "$MOVE_KEY_PATH.pub"
echo ""
echo "--------------------------------------------------------------------------"
echo "Please perform the following steps:"
echo "1. Copy the entire public key above (it starts with 'ssh-ed25519...')."
echo "2. Open your web browser and go to: http://${REMOTE_HOST}/development/ssh"
echo "3. Paste the public key into the text area on that page."
echo "4. Click 'Save' (or the equivalent button) to store the key on your Move."
echo "5. Ensure the key is successfully added before proceeding."
echo "--------------------------------------------------------------------------"
echo ""

# --- 4. Wait for user confirmation ---
read -p "Have you added the public key to your Move via http://${REMOTE_HOST}/development/ssh and are ready to proceed? (y/N): " user_ready
if [[ ! "$user_ready" =~ ^[Yy]$ ]]; then
    echo "Installation aborted by user."
    exit 1
fi
echo ""

# --- 5. Test SSH connection to ableton@move.local ---
echo "Testing SSH connection to ${REMOTE_USER_ABLETON}@${REMOTE_HOST}..."
echo "You may be asked to verify the host fingerprint if this is the first time."
if ssh -o ConnectTimeout=10 -o PasswordAuthentication=no -q "${REMOTE_USER_ABLETON}@${REMOTE_HOST}" exit; then
    echo "SSH connection to ${REMOTE_USER_ABLETON}@${REMOTE_HOST} successful."
else
    echo "ERROR: SSH connection to ${REMOTE_USER_ABLETON}@${REMOTE_HOST} failed."
    echo "Please double-check:"
    echo "  - The public key was correctly pasted and saved on http://${REMOTE_HOST}/development/ssh."
    echo "  - Your Move is connected to the network and reachable at ${REMOTE_HOST}."
    echo "  - You accepted the host fingerprint if prompted."
    echo "You can try connecting manually: ssh ${REMOTE_USER_ABLETON}@${REMOTE_HOST}"
    exit 1
fi
echo ""

# --- 6. Call install-on-move.sh ---
INSTALL_SCRIPT_PATH="${SCRIPT_DIR}/install-on-move.sh"
if [ ! -f "$INSTALL_SCRIPT_PATH" ]; then
    echo "Error: The main installation script ${INSTALL_SCRIPT_PATH} was not found."
    exit 1
fi

echo "Proceeding with 'extending-move' installation using ${INSTALL_SCRIPT_PATH}..."
# The install-on-move.sh script is interactive.
if bash "$INSTALL_SCRIPT_PATH"; then
    echo "'extending-move' installation script completed successfully."
else
    echo "Error: 'extending-move' installation script failed or was aborted."
    echo "Auto-start setup will be skipped."
    exit 1
fi
echo ""

# --- 7. Set up auto-start functionality ---
echo "--------------------------------------------------------------------------"
echo "Setup Auto-Start for 'extending-move' Webserver"
echo "--------------------------------------------------------------------------"
echo "This step will configure the 'extending-move' webserver to start automatically"
echo "when your Ableton Move boots up."
echo ""
echo "The auto-start configuration may not persist through Move firmware upgrades."
echo "--------------------------------------------------------------------------"
echo ""

read -p "Do you want to attempt to set up auto-start now? (y/N): " setup_autostart
if [[ ! "$setup_autostart" =~ ^[Yy]$ ]]; then
    echo "Auto-start setup skipped by user."
    echo ""
    echo "Script finished. 'extending-move' should be installed."
    echo "You may need to start the server manually: ssh ${REMOTE_USER_ABLETON}@${REMOTE_HOST} 'cd /data/UserData/extending-move && python3 move-webserver.py'"
    exit 0
fi

echo "Connecting to ${REMOTE_HOST} as root to set up auto-start..."
echo "Attempting to use key: ${MOVE_KEY_PATH}"

# Save init script content to a temporary file instead of using a variable
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
    # adjust this to whatever directory your code lives in:
    cd /data/UserData/extending-move
    # run as the 'ableton' user (drops privileges)
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

# Name of the init script as per README.md
INIT_SCRIPT_NAME="ableton-startup"

# Upload the init script from the temp file to the remote host
echo "Uploading init script to ${REMOTE_HOST}..."
scp -i "${MOVE_KEY_PATH}" "$TEMP_INIT_SCRIPT" "${REMOTE_USER_ROOT}@${REMOTE_HOST}:/tmp/${INIT_SCRIPT_NAME}"

# Remove temporary file after upload
rm "$TEMP_INIT_SCRIPT"

# Execute setup commands on the remote host
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
echo "1. Checking http://${REMOTE_HOST}:909 in your browser."
echo "2. Rebooting your Move and then checking the link again."
echo ""
echo "Remember, this auto-start configuration may not persist through Move firmware upgrades."
echo "--------------------------------------------------------------------------"
echo ""
echo "All operations finished. Enjoy your extended Move!"

exit 0 