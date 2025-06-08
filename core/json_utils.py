from typing import Any


def get_object_at_path(data: Any, path: str) -> Any:
    """Return the object at the given dotted path with list indices."""
    if not path:
        return data
    parts = path.split('.')
    current = data
    for part in parts:
        if '[' in part and part.endswith(']'):
            name, index_str = part.split('[', 1)
            index = int(index_str[:-1])
            if name:
                if not isinstance(current, dict) or name not in current:
                    return None
                current = current[name]
            if not isinstance(current, list) or index >= len(current):
                return None
            current = current[index]
        else:
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
    return current


def get_parent_and_key(data: Any, path: str):
    """Return the parent object and final key for a dotted path."""
    parts = path.split('.')
    parent = data
    for part in parts[:-1]:
        if '[' in part and part.endswith(']'):
            name, index_str = part.split('[', 1)
            index = int(index_str[:-1])
            if name:
                parent = parent.get(name, [])
            if not isinstance(parent, list) or index >= len(parent):
                return None, None
            parent = parent[index]
        else:
            parent = parent.get(part)
            if parent is None:
                return None, None
    return parent, parts[-1]
