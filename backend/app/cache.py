"""
Simple in-process TTL cache for news list responses.

Eliminates repeated DB round-trips for the same query when the data
hasn't changed. Invalidated explicitly whenever an article is
created, updated, deleted, or published via the admin router.
"""

import time
from threading import Lock

_lock = Lock()
_store: dict[str, tuple[object, float]] = {}

# Default TTL in seconds (60 s is enough for a news site)
DEFAULT_TTL = 60

# Keys include free-text search terms and article slugs, so bound the store:
# once it grows past this, expired entries are swept on the next write.
MAX_ENTRIES = 500


def get(key: str):
    """Return cached value or None if missing / expired."""
    with _lock:
        entry = _store.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.monotonic() > expires_at:
        with _lock:
            _store.pop(key, None)
        return None
    return value


def set(key: str, value, ttl: int = DEFAULT_TTL) -> None:
    """Store value under key, expiring after ttl seconds."""
    now = time.monotonic()
    with _lock:
        if len(_store) >= MAX_ENTRIES:
            for k in [k for k, (_, exp) in _store.items() if exp < now]:
                del _store[k]
            if len(_store) >= MAX_ENTRIES:
                _store.clear()
        _store[key] = (value, now + ttl)


def invalidate() -> None:
    """Flush the entire cache (called after any admin write)."""
    with _lock:
        _store.clear()
