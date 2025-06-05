"""Simple in-memory cache for library scans."""

from threading import Lock
import logging

_cache = {}
_lock = Lock()
logger = logging.getLogger(__name__)


def get_cache(key):
    """Retrieve cached value if it exists."""
    with _lock:
        value = _cache.get(key)
    if value is not None:
        logger.debug("Cache hit for %s", key)
    else:
        logger.debug("Cache miss for %s", key)
    return value


def set_cache(key, value):
    """Store value in cache."""
    with _lock:
        _cache[key] = value
    logger.debug("Updated cache for %s", key)


def invalidate_cache(key=None):
    """Invalidate the cache.

    If ``key`` is ``None`` all cached entries are cleared.
    """
    with _lock:
        if key is None:
            _cache.clear()
        else:
            _cache.pop(key, None)
    if key is None:
        logger.debug("Cleared entire cache")
    else:
        logger.debug("Invalidated cache for %s", key)
