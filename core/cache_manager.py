"""Simple in-memory cache for library scans."""

from threading import Lock

_cache = {}
_lock = Lock()


def get_cache(key):
    """Retrieve cached value if it exists."""
    with _lock:
        return _cache.get(key)


def set_cache(key, value):
    """Store value in cache."""
    with _lock:
        _cache[key] = value


def invalidate_cache(key=None):
    """Invalidate the cache.

    If ``key`` is ``None`` all cached entries are cleared.
    """
    with _lock:
        if key is None:
            _cache.clear()
        else:
            _cache.pop(key, None)
