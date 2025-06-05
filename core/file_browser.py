import os


def list_directory(base_dir: str, rel_path: str, extensions=None):
    """Return directories and files filtered by extensions starting from base_dir."""
    abs_dir = os.path.realpath(os.path.join(base_dir, rel_path))
    base_real = os.path.realpath(base_dir)
    if not abs_dir.startswith(base_real):
        return {"success": False, "message": "Invalid path"}
    if not os.path.isdir(abs_dir):
        return {"success": False, "message": "Not a directory"}

    dirs = []
    files = []
    for entry in sorted(os.listdir(abs_dir)):
        if entry.startswith('.'):
            continue
        full = os.path.join(abs_dir, entry)
        if os.path.isdir(full):
            dirs.append(entry)
        else:
            if extensions:
                if any(entry.lower().endswith(ext.lower()) for ext in extensions):
                    files.append(entry)
            else:
                files.append(entry)
    return {"success": True, "dirs": dirs, "files": files, "path": rel_path}
