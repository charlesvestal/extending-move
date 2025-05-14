# extending-move

Tools for extending the Ableton Move. This project provides a companion webserver that runs alongside the official Move server, accessible at move.local:909.

![CleanShot 2025-05-11 at 10 56 02](https://github.com/user-attachments/assets/be64a1d8-992a-4a84-bbbf-15095479d11d)


[Demo on YouTube](https://www.youtube.com/watch?v=MCmaCifzgbg)


## Features

- **Move Set Management**
  - Upload and restore Move Sets (.ablbundle)
  - Choose target pad and color

- **Sample Reversal**
  - Create reversed versions of any WAV file
  - Use reversed file in drum kit or sample presets
    
- **Drum Rack Inspector**
  - View all samples in a drum rack preset
  - Download individual samples
  - Create reversed versions directly in the preset

- **Chord Kit Generation**
  - Create chord variations from any WAV file
  - Includes common chord voicings (Cm9, Fm7, AbMaj7, etc.)
  - Automatic pitch-shifting and normalization
  - Download as `.ablpresetbundle` or place directly on device

- **Sliced Choke Kit Creation**
  - Use a visual slicer to create drum kits from WAV files with up to 16 slices
  - Choose custom slice points for each drum pad
  - Download as `.ablpresetbundle` or place directly on device
  - Automatic choke group configuration for one-shot behavior

- **Manual Library Refresh**
  - Accessible via move.local:909/refresh
  - Force refresh of Move's library cache
  - Useful after manual file changes
  - Uses Move's D-Bus interface
    
## Installation

### Prerequisites
1. SSH access to your Move (see [Wiki: Accessing Move](https://github.com/charlesvestal/extending-move/wiki/00--Accessing-Move))
2. Python environment on your Move

Note:
These tools are third-party and require SSH access. That means:

 * There’s a real risk (though unlikely) of breaking things, including potentially bricking a device. You are accessing the Move in ways it was not designed to do.
 * Ableton can’t offer individual support if something goes wrong.
 * If issues do arise, the documented restore procedure is the fallback – you use this at their own risk. Information on this procedure can be found in Center Code under [Documentation](https://ableton.centercode.com/project/article/item.html?cap=ecd3942a1fe3405eb27a806608401a0b&arttypeid={e70be312-f44a-418b-bb74-ed1030e3a49a}&artid={C0A2D9E2-D52F-4DEB-8BEE-356B65C8942E}).

### Quick Install (macOS)
Simply double-click `utility-scripts/install-on-move.command`
Everything that it does can be found in `utility-scritps/install-on-move.sh`

To update, you can use the similar `utility-scripts/update-on-move.command` or `utility-scripts/update-on-move.sh` to copy over the files and restart the webserver.

### Manual Installation

1. Login as the ableton user and install pip:
```bash
ssh ableton@move.local
cd /data/UserData
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
```

2. Configure temporary directory:
```bash
mkdir -p ~/tmp
export TMPDIR=~/tmp
```

3. Install dependencies:
```bash
pip install --no-cache-dir scipy
```

4. Copy files from your computer to your Move at /data/UserData/extending-move via whatever method you want (i.e. SFTP)

5. SSH to the Move and start the server
```bash
ssh ableton@move.local
cd /data/UserData/extending-move
cp -r /opt/move/HttpRoot/fonts /data/UserData/extending-move/static/
python3 move-webserver.py
```

The server will be accessible at http://move.local:909

## Utility Scripts

Note: Execute these scripts from your computer, not the Move.

Located in `utility-scripts/`:
- `install-on-move.sh` / `.command`: Initial setup and installation
- `update-on-move.sh` / `.command`: Update with latest files
- `restart-webserver.sh`: Restart the webserver


## How to Auto-start on Boot

Note: This does not persist through firmware upgrades. Re-run the command and re-enable the script after upgrading.

When logged in as root, create an init.d script with the following command

```bash
cat > /etc/init.d/ableton-startup << 'EOF'
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
EOF
chmod +x /etc/init.d/ableton-startup
```

Enable at boot with 
```bash
update-rc.d ableton-startup defaults
```

## Documentation

Check the [Wiki](https://github.com/charlesvestal/extending-move/wiki) for:
- Detailed Move documentation
- Hardware insights
- Development tips
- Troubleshooting guides

## Contributors

Many thanks to the contributors who have helped discover and document Move's capabilities:
bobbyd, void, deets, djhardrich, fedpep, manuz, poga, void, and many more.

Interested in chatting about more Move hacking? Come talk to us on [Discord](https://discord.gg/yP7SjqDrZG).

## Disclaimer

This project is not affiliated with, authorized by, or endorsed by Ableton. Use at your own risk. The authors cannot be held responsible for any damage or issues that may occur. Always refer to official documentation when modifying hardware.

> These tools are third-party and require SSH access. That means:
> * There’s a real risk (though unlikely) of breaking things, including potentially bricking a device. You are accessing the Move in ways it was not designed to do.
> * Ableton can’t offer individual support if something goes wrong.
> * If issues do arise, the documented restore procedure is the fallback – you use this at your own risk. Information on this procedure can be found in Center Code under [Documentation](https://ableton.centercode.com/project/article/item.html?cap=ecd3942a1fe3405eb27a806608401a0b&arttypeid={e70be312-f44a-418b-bb74-ed1030e3a49a}&artid={C0A2D9E2-D52F-4DEB-8BEE-356B65C8942E}).
