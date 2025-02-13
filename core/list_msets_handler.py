import os
import subprocess
from core.config import MSETS_DIRECTORY

def get_xattr_value(relative_path, attr):
    """
    Retrieve the extended attribute value for a given file or directory.
    
    Args:
        relative_path (str): Path to the target file or directory.
        attr (str): The name of the extended attribute to retrieve.
    
    Returns:
        str: The value of the extended attribute, or "Unknown" if retrieval fails.
    """
    try:
        output = subprocess.check_output(
            ["getfattr", "--only-values", "-n", attr, relative_path],
            cwd=MSETS_DIRECTORY,
            encoding="utf-8"
        ).strip()
        return output
    except subprocess.CalledProcessError:
        return "Unknown"

def list_msets(return_free_ids=False):
    """
    Retrieve a list of stored Move sets and available IDs.
    
    Args:
        return_free_ids (bool): Whether to also return available IDs.
    
    Returns:
        list: A list of dictionaries containing Move set metadata.
        dict (optional): A dictionary containing used and free slot IDs.
    """
    msets = []
    used_ids = set()

    for uuid in os.listdir(MSETS_DIRECTORY):
        uuid_path = os.path.join(MSETS_DIRECTORY, uuid)
        if os.path.isdir(uuid_path):
            # Retrieve Move set name (if available)
            mset_folders = [f for f in os.listdir(uuid_path) if os.path.isdir(os.path.join(uuid_path, f))]
            mset_name = mset_folders[0] if mset_folders else "Unknown"

            # Retrieve extended attributes
            mset_id = get_xattr_value(uuid, "user.song-index")
            mset_color = get_xattr_value(uuid, "user.song-color")
            mset_cloudstate = get_xattr_value(uuid, "user.local-cloud-state")
            mset_modifiedtime = get_xattr_value(uuid, "user.last-modified-time")
            mset_extmodified = get_xattr_value(uuid, "user.was-externally-modified")

            mset_id_value = int(mset_id) if mset_id.isdigit() else 9999
            msets.append({
                "uuid": uuid,
                "mset_name": mset_name,
                "mset_id": mset_id_value,
                "mset_color": mset_color if mset_color.isdigit() else "Unknown",
                "mset_cloudstate": mset_cloudstate,
                "mset_modifiedtime": mset_modifiedtime,
                "mset_extmodified": mset_extmodified
            })

            if 0 <= mset_id_value <= 31:
                used_ids.add(mset_id_value)

    msets_sorted = sorted(msets, key=lambda x: x["mset_id"])

    if return_free_ids:
        free_ids = [i for i in range(32) if i not in used_ids]
        return msets_sorted, {"used": used_ids, "free": free_ids}

    return msets_sorted

def list_msets_free():
    """
    Return a list of available Move set IDs.
    
    Returns:
        list: A list of free slot indices (0-31).
    """
    _, ids_info = list_msets(return_free_ids=True)
    return ids_info["free"]
