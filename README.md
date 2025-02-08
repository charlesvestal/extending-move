# extending-move

Tips, tricks and tools for extending the Ableton Move.

The code in this repository will run an additional webserver alongside the official one. When run on the move, it is accessible at move.local:666.

![CleanShot 2025-02-08 at 22 11 01@2x](https://github.com/user-attachments/assets/ba771ca3-1372-416b-bd5b-e2ec82b66223)


## Current Features

- Create a choke kit from an uploaded .WAV file of up to 16 slices
    - Choose the slice points for each drum pad
    - Download the preset as an `.ablpresetbundle`
    - Or have it generated directly on your device
- Manually refresh your Move's library (useful when making manual changes to files)

## Installation

### Requirements
Begin by gaining ssh access to your move: <https://github.com/charlesvestal/extending-move/wiki/00--Accessing-Move>

First, login as root, and install pip using the script at <https://bootstrap.pypa.io/get-pip.py>

`wget https://bootstrap.pypa.io/get-pip.py`

Login as the ableton user. We then need to set the system to use a tmpdir on the larger user partition, as it will run out of space downloading packages if using the root one.

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
