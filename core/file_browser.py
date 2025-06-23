import os
import json
from typing import Callable, Tuple, Union, Optional

from core.cache_manager import get_cache, set_cache

_CACHE_PREFIX = "file_browser:"


def _list_directory(base_dir: str, rel_path: str) -> Tuple[list[str], list[str]]:
    """List subdirectories and files for the given path with caching.

    Cached entries are automatically invalidated if the directory's
    modification time or entry count changes.
    """
    abs_path = os.path.join(base_dir, rel_path)
    key = f"{_CACHE_PREFIX}{abs_path}"
    cached = get_cache(key)
    try:
        mtime = os.stat(abs_path).st_mtime_ns
        entries = os.listdir(abs_path)
    except FileNotFoundError:
        return [], []

    if cached is not None and cached.get("mtime") == mtime and cached.get("count") == len(entries):
        return cached["dirs"], cached["files"]


    dirs: list[str] = []
    files: list[str] = []
    for name in sorted(entries):
        full = os.path.join(abs_path, name)
        if os.path.isdir(full):
            dirs.append(name)
        elif os.path.isfile(full):
            files.append(name)

    set_cache(key, {"dirs": dirs, "files": files, "mtime": mtime, "count": len(entries)})
    return dirs, files


def _check_json_file(file_path: str, kind: str) -> bool:
    """Check JSON file for a specific ``kind`` with caching.

    Cached results are revalidated if the file's modification time changes.
    """
    key = f"{_CACHE_PREFIX}{kind}:{file_path}"
    cached = get_cache(key)
    try:
        mtime = os.stat(file_path).st_mtime_ns
    except FileNotFoundError:
        return False

    if cached is not None and cached.get("mtime") == mtime:
        return cached.get("result", False)

    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        result = _has_kind(data, kind)
    except Exception:
        result = False

    set_cache(key, {"result": result, "mtime": mtime})
    return result


def _has_kind(data: Union[dict, list], kind: str) -> bool:
    if isinstance(data, dict):
        if data.get("kind") == kind:
            return True
        return any(_has_kind(v, kind) for v in data.values())
    if isinstance(data, list):
        return any(_has_kind(item, kind) for item in data)
    return False


FILTERS: dict[str, Callable[[str], bool]] = {
    "wav": lambda p: p.lower().endswith(".wav"),
    "drift": lambda p: (
        p.lower().endswith(".ablpreset")
        or p.lower().endswith(".json")
    )
    and _check_json_file(p, "drift"),
    "wavetable": lambda p: (
        p.lower().endswith(".ablpreset")
        or p.lower().endswith(".json")
    )
    and _check_json_file(p, "wavetable"),
    "drumrack": lambda p: (
        p.lower().endswith(".ablpreset")
        or p.lower().endswith(".json")
    )
    and _check_json_file(p, "drumRack"),
    "melodicsampler": lambda p: (
        p.lower().endswith(".ablpreset")
        or p.lower().endswith(".json")
    )
    and _check_json_file(p, "melodicSampler"),
    "fxchain": lambda p: (
        p.lower().endswith(".ablpreset")
        or p.lower().endswith(".json")
    ),
}


def generate_dir_html(
    base_dir: str,
    rel_path: str,
    action_url: str,
    field_name: str,
    action_value: str,
    filter_key: Optional[str] = None,
    *,
    path_prefix: str = "",
) -> str:
    """Return HTML listing for the directory.

    ``path_prefix`` is prepended to all ``data-path`` attributes so that
    virtual directory roots can be implemented.
    """
    filter_func = FILTERS.get(filter_key, lambda p: True)
    dirs, files = _list_directory(base_dir, rel_path)
    root_path = os.path.join(path_prefix, rel_path) if path_prefix or rel_path else ""
    html = (
        f'<ul class="file-tree" data-path="{root_path}">'
        if path_prefix or rel_path
        else '<ul class="file-tree root" data-path="">'
    )
    for d in dirs:
        sub_rel = os.path.join(rel_path, d) if rel_path else d
        data_path = os.path.join(path_prefix, sub_rel) if path_prefix else sub_rel
        html += (
            f'<li class="dir closed" data-path="{data_path}">'
            f'<span>📁 {d}</span>'
            '<ul class="hidden"></ul></li>'
        )
    for f in files:
        full = os.path.join(base_dir, rel_path, f)
        if filter_func(full):
            rel = os.path.join(rel_path, f) if rel_path else f
            html += (
                '<li class="file">'
                f'<form method="post" action="{action_url}" class="file-entry">'
                f'<input type="hidden" name="action" value="{action_value}">'\
                f'<input type="hidden" name="{field_name}" value="{full}">'\
                f'<button type="submit">📄 {f}</button>'
                '</form>'
                '</li>'
            )
    html += '</ul>'
    return html
