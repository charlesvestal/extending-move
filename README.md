# extending-move

Tips, tricks and tools for extending the Ableton Move.

The code in this repository will run an additional webserver alongside the official one. When run on the move, it is accessible at move.local:666.

![CleanShot 2025-02-09 at 21 17 48](https://github.com/user-attachments/assets/7b010cbb-8b26-4c53-80ed-ada875514aff)


## Current Features

- Create a choke kit from an uploaded .WAV file of up to 16 slices
    - Choose the slice points for each drum pad
    - Download the preset as an `.ablpresetbundle`
    - Or have it generated directly on your device
- Choose a sample and generate a reversed version
- Manually refresh your Move's library (useful when making manual changes to files)

## Installation

### SSH Key

Begin by gaining ssh access to your move: <https://github.com/charlesvestal/extending-move/wiki/00--Accessing-Move>

### Automatic Installation

TL;DR: double click `install-on-move.sh`.

This project includes a number of scripts to aid in installation and updating these tools:

`install-on-move.sh` can be executed to perform the "Manual Installation" steps below.
`updated-on-move.sh` will copy the files from the current directory and restart the webserver on your Move.
`restart-webserver.sh` will restart the webserver on your Move.

`install-on-move.command` and `update-on-move.command` are convenience applications to run the above scripts by double clicking on MacOS or other systems that support .command files.

NOTE: these scripts should be executed from a computer, not your Move itself.

### Manual Installation

First, login as the ableton user, and install pip using the script at <https://bootstrap.pypa.io/get-pip.py>

`wget https://bootstrap.pypa.io/get-pip.py`

We then need to set the system to use a tmpdir on the larger user partition, as it will run out of space downloading packages if using the root one.

```
mkdir -p ~/tmp
export TMPDIR=~/tmp
```

then, install scipy

`pip install --no-cache-dir scipy`

### Script Installation

copy the files in this repository to `/data/UserData/extending-move`

still as the ableton user, navigate to the directory and start the server

```
cd /data/UserData/extending-move
python3 move-webserver.py
```

the server is now accessible at http://move.local:666

# Other tips

Check the Wiki for more information as it is disovered about the Move: <https://github.com/charlesvestal/extending-move/wiki>

# Disclaimer

The information provided on this wiki is intended for educational and informational purposes only. By using any of the techniques or suggestions outlined here, you do so entirely at your own risk. The authors cannot be held responsible for any damage, loss, or other issues that may occur to your devices or data as a result of following this guide. This wiki is not affiliated with, authorized by, or endorsed by Ableton. Always exercise caution and refer to official documentation or support when modifying or using your hardware.

Please use this information responsibly and ensure you understand the potential risks involved.
