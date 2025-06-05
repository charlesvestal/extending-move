import os
import json
from typing import Callable, Tuple

from core.cache_manager import get_cache, set_cache

_CACHE_PREFIX = "file_browser:"


def _list_directory(base_dir: str, rel_path: str) -> Tuple[list[str], list[str]]:
    """List subdirectories and files for the given path with caching."""
    abs_path = os.path.join(base_dir, rel_path)
    key = f"{_CACHE_PREFIX}{abs_path}"
    cached = get_cache(key)
    if cached is not None:
        return cached["dirs"], cached["files"]

    try:
        entries = os.listdir(abs_path)
    except FileNotFoundError:
        return [], []
    dirs: list[str] = []
    files: list[str] = []
    for name in sorted(entries):
        full = os.path.join(abs_path, name)
        if os.path.isdir(full):
            dirs.append(name)
        elif os.path.isfile(full):
            files.append(name)
    set_cache(key, {"dirs": dirs, "files": files})
    return dirs, files


def _check_json_file(file_path: str, predicate: Callable[[dict], bool]) -> bool:
    """Check JSON file against predicate with caching."""
    key = f"{_CACHE_PREFIX}{file_path}"
    cached = get_cache(key)
    if cached is not None and "result" in cached:
        return cached["result"]
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
        result = predicate(data)
    except Exception:
        result = False
    set_cache(key, {"result": result})
    return result


def _has_kind(data: dict | list, kind: str) -> bool:
    if isinstance(data, dict):
        if data.get("kind") == kind:
            return True
        return any(_has_kind(v, kind) for v in data.values())
    if isinstance(data, list):
        return any(_has_kind(item, kind) for item in data)
    return False


FILTERS: dict[str, Callable[[str], bool]] = {
    "wav": lambda p: p.lower().endswith(".wav"),
    "drift": lambda p: p.lower().endswith(".ablpreset") and _check_json_file(p, lambda d: _has_kind(d, "drift")),
    "drumrack": lambda p: p.lower().endswith(".ablpreset") and _check_json_file(p, lambda d: _has_kind(d, "drumRack")),
}


def generate_dir_html(
    base_dir: str,
    rel_path: str,
    action_url: str,
    field_name: str,
    action_value: str,
    filter_key: str | None = None,
) -> str:
    """Return HTML listing for the directory."""
    filter_func = FILTERS.get(filter_key, lambda p: True)
    dirs, files = _list_directory(base_dir, rel_path)
    html = f'<ul class="file-tree" data-path="{rel_path}">' \
        if rel_path else '<ul class="file-tree root" data-path="">'
    for d in dirs:
        sub_rel = os.path.join(rel_path, d) if rel_path else d
        html += (
            f'<li class="dir closed" data-path="{sub_rel}">'
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
                f'<input type="hidden" name="action" value="{action_value}">' \
                f'<input type="hidden" name="{field_name}" value="{full}">' \
                f'<button type="submit">📄 {f}</button>'
                '</form>'
                '</li>'
            )
    html += '</ul>'
    return html
