"""
Session-level caching for event data.

Configurable caching to optimize data loading while allowing on-demand
fetches for real-time updates.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Single cache entry with metadata."""

    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 3600  # 1 hour default

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds


class SessionCache:
    """
    Session-level cache for event data.
    
    Stores project/session data with optional expiration.
    Can be disabled per request via cache_enabled flag.
    
    Usage:
        cache = SessionCache(enabled=True, ttl_seconds=3600)
        cache.set("projects", projects_data)
        projects = cache.get("projects")
    """

    def __init__(self, enabled: bool = True, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            enabled: If False, cache is bypassed (on-demand mode)
            ttl_seconds: Time-to-live for cached entries
        """
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        self.logger = logging.getLogger(f"{__name__}.SessionCache")

    def set(self, key: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        """
        Store data in cache.
        
        Args:
            key: Cache key (e.g., "projects", "sessions")
            data: Data to cache
            ttl_seconds: Optional TTL override for this entry
        """
        if not self.enabled:
            self.logger.debug(f"Cache disabled, skipping set for key: {key}")
            return

        ttl = ttl_seconds or self.ttl_seconds
        self._cache[key] = CacheEntry(data=data, ttl_seconds=ttl)
        self.logger.debug(f"Cached '{key}' (TTL: {ttl}s)")

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        if not self.enabled:
            self.logger.debug(f"Cache disabled, skipping get for key: {key}")
            return None

        entry = self._cache.get(key)
        if entry is None:
            self.logger.debug(f"Cache miss for key: {key}")
            return None

        if entry.is_expired():
            self.logger.debug(f"Cache expired for key: {key}, removing")
            del self._cache[key]
            return None

        self.logger.debug(f"Cache hit for key: {key}")
        return entry.data

    def invalidate(self, key: str) -> None:
        """
        Manually invalidate a cache entry.
        
        Args:
            key: Cache key to invalidate
        """
        if key in self._cache:
            del self._cache[key]
            self.logger.debug(f"Invalidated cache for key: {key}")

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        self.logger.debug("Cleared entire cache")

    def toggle(self, enabled: bool) -> None:
        """
        Toggle cache on/off.
        
        Args:
            enabled: If True, enable caching; if False, bypass cache
        """
        was_enabled = self.enabled
        self.enabled = enabled
        if was_enabled != enabled:
            action = "enabled" if enabled else "disabled"
            self.logger.info(f"Cache {action}")
            if not enabled:
                self.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "enabled": self.enabled,
            "entries": len(self._cache),
            "keys": list(self._cache.keys()),
        }


# Global cache instance
_session_cache: Optional[SessionCache] = None


def get_session_cache(enabled: bool = True, ttl_seconds: int = 3600) -> SessionCache:
    """
    Get the session cache singleton.
    
    Args:
        enabled: Enable/disable caching (default: True)
        ttl_seconds: Time-to-live for entries (default: 3600)
        
    Returns:
        SessionCache: Global cache instance
    """
    global _session_cache
    if _session_cache is None:
        _session_cache = SessionCache(enabled=enabled, ttl_seconds=ttl_seconds)
    return _session_cache
