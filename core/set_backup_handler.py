import os
import shutil
from datetime import datetime
from typing import Optional

BACKUP_EXT = '.ablbak'


def backup_set(set_path: str) -> str:
    """Create a timestamped backup of the given set file and keep last 10.

    This should be called **before** modifying the set so the previous
    version can be restored. ``backup_set`` only creates the backup file and
    does not alter ``latest.txt`` which tracks the timestamp of the current
    version.
    """
    if not os.path.isfile(set_path):
        raise FileNotFoundError(f"{set_path} not found")

    backup_dir = os.path.join(os.path.dirname(set_path), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%dT%H%M%S%f')
    backup_name = os.path.basename(set_path) + f'.{timestamp}' + BACKUP_EXT
    backup_path = os.path.join(backup_dir, backup_name)
    shutil.copy2(set_path, backup_path)



    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(BACKUP_EXT)],
        key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)),
        reverse=True,
    )
    for old in backups[10:]:
        try:
            os.remove(os.path.join(backup_dir, old))
        except Exception:
            pass
    return backup_path


def write_latest_timestamp(set_path: str, timestamp: Optional[str] = None) -> None:
    """Persist ``timestamp`` as the current version string."""
    backup_dir = os.path.join(os.path.dirname(set_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    latest_file = os.path.join(backup_dir, "latest.txt")
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    with open(latest_file, "w") as f:
        f.write(timestamp)


def get_current_timestamp(set_path: str) -> Optional[str]:
    """Return human-readable timestamp of the currently saved version."""
    backup_dir = os.path.join(os.path.dirname(set_path), "backups")
    latest_file = os.path.join(backup_dir, "latest.txt")
    ts = None
    if os.path.isfile(latest_file):
        try:
            with open(latest_file) as f:
                ts = f.read().strip()
            datetime.strptime(ts, "%Y%m%dT%H%M%S%f")
        except Exception:
            ts = None
    if ts is None and os.path.isfile(set_path):
        mtime = os.path.getmtime(set_path)
        dt = datetime.fromtimestamp(mtime)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if ts is None:
        return None
    dt = datetime.strptime(ts, "%Y%m%dT%H%M%S%f")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def list_backups(set_path: str):
    """Return a list of backups with display names sorted newest first."""
    backup_dir = os.path.join(os.path.dirname(set_path), 'backups')
    if not os.path.isdir(backup_dir):
        return []
    backups = sorted(
        [f for f in os.listdir(backup_dir) if f.endswith(BACKUP_EXT)],
        key=lambda f: os.path.getmtime(os.path.join(backup_dir, f)),
        reverse=True,
    )[:10]
    result = []
    for name in backups:
        path = os.path.join(backup_dir, name)
        ts = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
        result.append({'name': name, 'display': ts})
    return result


def restore_backup(set_path: str, backup_name: str) -> bool:
    """Restore the specified backup over the set file."""
    backup_dir = os.path.join(os.path.dirname(set_path), "backups")
    # Prevent path traversal by only allowing base names
    if os.path.basename(backup_name) != backup_name:
        return False
    backup_path = os.path.join(backup_dir, backup_name)
    if not os.path.isfile(backup_path):
        return False
    shutil.copy2(backup_path, set_path)
    # update latest timestamp to match restored backup
    base = os.path.basename(backup_name)
    parts = base.split(".")
    if len(parts) >= 3:
        ts = parts[-2]
        write_latest_timestamp(set_path, ts)
    else:
        write_latest_timestamp(set_path)
    return True
