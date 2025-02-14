import os
import zipfile
import re
import subprocess
import uuid
import logging
import urllib.parse
from datetime import datetime, timezone
from core.list_msets_handler import list_msets_free
from core.config import MSETS_DIRECTORY, MSET_INDEX_RANGE, MSET_COLOR_RANGE, MSET_SAMPLE_PATH, MSET_ABLETON_URI


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        # logging.FileHandler("restore_ablbundle.log"),
        logging.StreamHandler()
    ]
)

def restore_ablbundle(ablbundle_path, mset_restoreid, mset_restorecolor):
    """
    Restores an Ableton Move set (.ablbundle) to a specified pad.
    
    Args:
        ablbundle_path (str): Path to the uploaded .ablbundle file.
        mset_restoreid (int): Pad index where the set should be restored.
        mset_restorecolor (int): Color index (1-26) assigned to the set.

    Returns:
        dict: Result of the operation, including success status and message.
    """
    if not os.path.exists(ablbundle_path):
        return {"success": False, "message": f"Error: {ablbundle_path} does not exist."}

    # Get available IDS
    free_ids = list_msets_free()

    # Validate if the ID is within the allowed range
    if not (MSET_INDEX_RANGE[0] <= mset_restoreid <= MSET_INDEX_RANGE[1]):
        return {"success": False, "message": f"Invalid set index {mset_restoreid}. Must be between {MSET_INDEX_RANGE[0]} and {MSET_INDEX_RANGE[1]}."}

    # Validate if the ID is actually free
    if mset_restoreid not in free_ids:
        return {"success": False, "message": f"Invalid set index {mset_restoreid}. ID already in use."}

    # Validate color range
    if not (MSET_COLOR_RANGE[0] <= mset_restorecolor <= MSET_COLOR_RANGE[1]):
        return {"success": False, "message": f"Invalid set color {mset_restorecolor}. Must be between {MSET_COLOR_RANGE[0]} and {MSET_COLOR_RANGE[1]}."}

    
    # Generate unique directory for set storage (UUIDv4)
    mset_uuid = str(uuid.uuid4())
    uuid_dir = os.path.join(MSETS_DIRECTORY, mset_uuid)
    os.makedirs(uuid_dir, exist_ok=True)
    
    # Extract Move set name from filename
    ablbundle_filename = os.path.basename(ablbundle_path)
    mset_name, _ = os.path.splitext(ablbundle_filename)
    mset_name_encoded = urllib.parse.quote(mset_name)
    mset_folder = os.path.join(uuid_dir, mset_name)
    
    # Prevent overwriting existing sets
    if os.path.exists(mset_folder):
        return {"success": False, "message": f"Error: Set folder {mset_folder} already exists. Choose a different ID."}
    
    os.makedirs(mset_folder, exist_ok=True)

    # Extract .ablbundle contents
    try:
        with zipfile.ZipFile(ablbundle_path, 'r') as zip_ref:
            zip_ref.extractall(mset_folder)
    except zipfile.BadZipFile:
        return {"success": False, "message": "Error: Invalid .ablbundle file."}

    song_abl_path = os.path.join(mset_folder, "Song.abl")
    if not os.path.exists(song_abl_path):
        return {"success": False, "message": "Error: Song.abl file missing from bundle."}

    # Update sample paths in Song.abl to reference the samples inside the Move Set folder,
    # rather than pointing to the global sample library on the Move.
    with open(song_abl_path, 'r', encoding='utf-8') as file:
        content = file.read()

    content = re.sub(
        r'(\"sampleUri\"\s*:\s*\")Samples/([^\"]+)',
        rf'\1{MSET_ABLETON_URI}/{mset_uuid}/{mset_name_encoded}/Samples/\2',
        content
    )

    with open(song_abl_path, 'w', encoding='utf-8') as file:
        file.write(content)
    
    # Set extended attributes for Move system
    last_modified_timestamp = datetime.fromtimestamp(os.path.getmtime(song_abl_path), tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    try:
        subprocess.run(["chown", "-R", "ableton:users", uuid_dir], check=True)
        subprocess.run(["setfattr", "-n", "user.song-index", "-v", str(mset_restoreid), uuid_dir], check=True)
        subprocess.run(["setfattr", "-n", "user.song-color", "-v", str(mset_restorecolor), uuid_dir], check=True)
        subprocess.run(["setfattr", "-n", "user.last-modified-time", "-v", last_modified_timestamp, uuid_dir], check=True)
        subprocess.run(["setfattr", "-n", "user.was-externally-modified", "-v", "false", uuid_dir], check=True)
        subprocess.run(["setfattr", "-n", "user.local-cloud-state", "-v", "notSynced", uuid_dir], check=True)
    except subprocess.CalledProcessError as e:
        return {"success": False, "message": f"Error setting attributes: {e}"}
    
    logging.info(f"Successfully restored {ablbundle_path} to {uuid_dir}")
    return {"success": True, "message": f"Successfully restored {mset_name} to pad ID {mset_restoreid} with color {mset_restorecolor}"}
