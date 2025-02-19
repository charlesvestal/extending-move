# extending-move

Tools for extending the Ableton Move. This project provides a companion webserver that runs alongside the official Move server, accessible at move.local:666.

![CleanShot 2025-02-09 at 21 17 48](https://github.com/user-attachments/assets/7b010cbb-8b26-4c53-80ed-ada875514aff)

## Features

### Sample Management
- **Choke Kit Creation**
  - Create drum kits from WAV files with up to 16 slices
  - Choose custom slice points for each drum pad
  - Download as `.ablpresetbundle` or generate directly on device
  - Automatic choke group configuration for one-shot behavior

- **Chord Kit Generation**
  - Create chord variations from any WAV file
  - Includes common chord voicings (Cm9, Fm7, AbMaj7, etc.)
  - Automatic pitch-shifting and normalization
  - Download as preset bundle or place directly on device

- **Sample Reversal**
  - Create reversed versions of any WAV file
  - Toggle between original and reversed versions
  - Automatic library updates
  - Supports most common WAV formats

### Preset Management
- **Drum Rack Inspector**
  - View all samples in a drum rack preset
  - Download individual samples
  - Create reversed versions directly in the preset
  - Update sample assignments

- **Move Set Management**
  - Upload and restore Move Sets (.ablbundle)
  - Choose target pad and color
  - Automatic library integration
  - Maintains Move's file structure

### Library Management
- **Manual Library Refresh**
  - Force refresh of Move's library cache
  - Useful after manual file changes
  - Uses Move's D-Bus interface

## Installation

### Prerequisites
1. SSH access to your Move (see [Wiki: Accessing Move](https://github.com/charlesvestal/extending-move/wiki/00--Accessing-Move))
2. Python environment on your Move

### Quick Install (macOS)
Simply double-click `utility-scripts/install-on-move.command`

### Manual Installation

1. Login as the ableton user and install pip:
```bash
wget https://bootstrap.pypa.io/get-pip.py
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

4. Copy files and start server:
```bash
cd /data/UserData/extending-move
python3 move-webserver.py
```

The server will be accessible at http://move.local:666

## Utility Scripts

Located in `utility-scripts/`:
- `install-on-move.sh` / `.command`: Initial setup and installation
- `update-on-move.sh` / `.command`: Update with latest files
- `restart-webserver.sh`: Restart the webserver

Note: Execute these scripts from your computer, not the Move.

## Documentation

Check the [Wiki](https://github.com/charlesvestal/extending-move/wiki) for:
- Detailed Move documentation
- Hardware insights
- Development tips
- Troubleshooting guides

## Contributors

Many thanks to the contributors who have helped discover and document Move's capabilities:
bobbyd, charlesv, deets, fedpep, manuz, poga, and void.

## Disclaimer

This project is not affiliated with, authorized by, or endorsed by Ableton. Use at your own risk. The authors cannot be held responsible for any damage or issues that may occur. Always refer to official documentation when modifying hardware.
