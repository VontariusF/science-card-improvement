"""Cache management with multiple backend support."""

import asyncio
import hashlib
import json
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

import aiofiles

from src.config.settings import get_settings
from src.exceptions.custom_exceptions import CacheError
from src.utils.logger import LoggerMixin


class CacheManager(LoggerMixin):
    """Unified cache manager with file and memory backends."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        default_ttl: int = 3600,
        max_memory_size: int = 100,
    ):
        """Initialize cache manager.

        Args:
            cache_dir: Directory for file-based cache
            default_ttl: Default TTL in seconds
            max_memory_size: Maximum number of items in memory cache
        """
        self.settings = get_settings()
        self.cache_dir = cache_dir or self.settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
        self.max_memory_size = max_memory_size

        # Memory cache
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "memory_size": 0,
            "disk_size": 0,
        }

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        try:
            # Check memory cache first
            if key in self.memory_cache:
                entry = self.memory_cache[key]
                if self._is_valid_entry(entry):
                    self.stats["hits"] += 1
                    self.access_times[key] = time.time()
                    return entry["value"]
                else:
                    # Expired, remove from memory
                    del self.memory_cache[key]
                    del self.access_times[key]

            # Check file cache
            file_path = self._get_cache_file_path(key)
            if file_path.exists():
                async with aiofiles.open(file_path, "rb") as f:
                    content = await f.read()
                    entry = pickle.loads(content)

                if self._is_valid_entry(entry):
                    # Load to memory cache
                    self._add_to_memory_cache(key, entry)
                    self.stats["hits"] += 1
                    return entry["value"]
                else:
                    # Expired, delete file
                    file_path.unlink()

            self.stats["misses"] += 1
            return default

        except Exception as e:
            self.log_error(f"Cache get error", key=key, exception=e)
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds

        Returns:
            Success status
        """
        try:
            ttl = ttl or self.default_ttl
            expiry = datetime.utcnow() + timedelta(seconds=ttl)

            entry = {
                "value": value,
                "expiry": expiry.isoformat(),
                "created": datetime.utcnow().isoformat(),
            }

            # Add to memory cache
            self._add_to_memory_cache(key, entry)

            # Save to file cache
            file_path = self._get_cache_file_path(key)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(pickle.dumps(entry))

            self.stats["sets"] += 1
            return True

        except Exception as e:
            self.log_error(f"Cache set error", key=key, exception=e)
            raise CacheError(f"Failed to set cache key: {key}", cache_key=key)

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            Success status
        """
        try:
            # Remove from memory cache
            if key in self.memory_cache:
                del self.memory_cache[key]
                del self.access_times[key]

            # Remove file
            file_path = self._get_cache_file_path(key)
            if file_path.exists():
                file_path.unlink()

            self.stats["deletes"] += 1
            return True

        except Exception as e:
            self.log_error(f"Cache delete error", key=key, exception=e)
            return False

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries.

        Args:
            pattern: Optional pattern to match keys

        Returns:
            Number of entries cleared
        """
        cleared = 0

        try:
            if pattern:
                # Clear matching keys
                keys_to_delete = [
                    k for k in self.memory_cache.keys()
                    if pattern in k
                ]
                for key in keys_to_delete:
                    if await self.delete(key):
                        cleared += 1

                # Clear matching files
                for file_path in self.cache_dir.glob("*.cache"):
                    if pattern in file_path.stem:
                        file_path.unlink()
                        cleared += 1
            else:
                # Clear all
                cleared = len(self.memory_cache)
                self.memory_cache.clear()
                self.access_times.clear()

                for file_path in self.cache_dir.glob("*.cache"):
                    file_path.unlink()
                    cleared += 1

            self.log_info(f"Cleared {cleared} cache entries", pattern=pattern)
            return cleared

        except Exception as e:
            self.log_error(f"Cache clear error", pattern=pattern, exception=e)
            return cleared

    async def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        removed = 0

        # Clean memory cache
        keys_to_delete = []
        for key, entry in self.memory_cache.items():
            if not self._is_valid_entry(entry):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.memory_cache[key]
            del self.access_times[key]
            removed += 1

        # Clean file cache
        for file_path in self.cache_dir.glob("*.cache"):
            try:
                async with aiofiles.open(file_path, "rb") as f:
                    content = await f.read()
                    entry = pickle.loads(content)

                if not self._is_valid_entry(entry):
                    file_path.unlink()
                    removed += 1
            except Exception:
                # Corrupted file, remove it
                file_path.unlink()
                removed += 1

        self.log_info(f"Cleaned up {removed} expired cache entries")
        return removed

    def _add_to_memory_cache(self, key: str, entry: Dict[str, Any]) -> None:
        """Add entry to memory cache with LRU eviction."""
        # Check memory limit
        if len(self.memory_cache) >= self.max_memory_size:
            # Evict least recently used
            if self.access_times:
                lru_key = min(self.access_times, key=self.access_times.get)
                del self.memory_cache[lru_key]
                del self.access_times[lru_key]

        self.memory_cache[key] = entry
        self.access_times[key] = time.time()
        self.stats["memory_size"] = len(self.memory_cache)

    def _is_valid_entry(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        if "expiry" not in entry:
            return False

        expiry = datetime.fromisoformat(entry["expiry"])
        return datetime.utcnow() < expiry

    def _get_cache_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Hash the key for filename
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"

    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        # Calculate disk size
        disk_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.cache"))
        self.stats["disk_size"] = disk_size

        # Calculate hit rate
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }


class AsyncLRUCache:
    """Async LRU cache decorator."""

    def __init__(self, maxsize: int = 128, ttl: int = 3600):
        """Initialize LRU cache.

        Args:
            maxsize: Maximum cache size
            ttl: Time to live in seconds
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_order: list = []

    def __call__(self, func):
        """Decorate async function with caching."""
        async def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = self._make_key(func.__name__, args, kwargs)

            # Check cache
            if cache_key in self.cache:
                entry = self.cache[cache_key]
                if self._is_valid(entry):
                    # Move to end (most recently used)
                    self.access_order.remove(cache_key)
                    self.access_order.append(cache_key)
                    return entry["value"]
                else:
                    # Expired
                    del self.cache[cache_key]
                    self.access_order.remove(cache_key)

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            self._add_to_cache(cache_key, result)

            return result

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.cache_info = self.cache_info
        wrapper.cache_clear = self.cache_clear

        return wrapper

    def _make_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Create cache key from function arguments."""
        key_parts = [func_name]

        for arg in args:
            if hasattr(arg, "__dict__"):
                key_parts.append(str(arg.__dict__))
            else:
                key_parts.append(str(arg))

        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")

        return ":".join(key_parts)

    def _is_valid(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is valid."""
        expiry = entry.get("expiry")
        if not expiry:
            return False
        return time.time() < expiry

    def _add_to_cache(self, key: str, value: Any) -> None:
        """Add value to cache with LRU eviction."""
        # Check size limit
        if len(self.cache) >= self.maxsize:
            # Evict least recently used
            lru_key = self.access_order[0]
            del self.cache[lru_key]
            self.access_order.remove(lru_key)

        # Add new entry
        self.cache[key] = {
            "value": value,
            "expiry": time.time() + self.ttl,
        }
        self.access_order.append(key)

    def cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        return {
            "size": len(self.cache),
            "maxsize": self.maxsize,
            "ttl": self.ttl,
            "keys": list(self.cache.keys()),
        }

    def cache_clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.access_order.clear()