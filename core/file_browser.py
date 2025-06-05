import os


def list_directory(base_dir: str, rel_path: str, extensions=None, allowed_files=None):
    """Return directories and files filtered by ``extensions`` and ``allowed_files``."""
    abs_dir = os.path.realpath(os.path.join(base_dir, rel_path))
    base_real = os.path.realpath(base_dir)
    if not abs_dir.startswith(base_real):
        return {"success": False, "message": "Invalid path"}
    if not os.path.isdir(abs_dir):
        return {"success": False, "message": "Not a directory"}

    dirs = []
    files = []
    allowed_set = set(os.path.normpath(p) for p in allowed_files) if allowed_files else None
    for entry in sorted(os.listdir(abs_dir)):
        if entry.startswith('.'):
            continue
        full = os.path.join(abs_dir, entry)
        rel = os.path.normpath(os.path.join(rel_path, entry)) if rel_path else entry
        if os.path.isdir(full):
            include_dir = True
            if allowed_set is not None:
                prefix = rel + os.sep
                include_dir = any(p.startswith(prefix) for p in allowed_set)
            if include_dir:
                dirs.append(entry)
        else:
            if extensions and not any(entry.lower().endswith(ext.lower()) for ext in extensions):
                continue
            if allowed_set is not None and rel not in allowed_set:
                continue
            files.append(entry)
    return {"success": True, "dirs": dirs, "files": files, "path": rel_path}


def resolve_path(base_dir: str, rel_path: str) -> str:
    """Return an absolute path within ``base_dir`` or raise ``ValueError``."""
    abs_path = os.path.realpath(os.path.join(base_dir, rel_path))
    base_real = os.path.realpath(base_dir)
    if not abs_path.startswith(base_real):
        raise ValueError("Invalid path")
    return abs_path
