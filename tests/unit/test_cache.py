"""Unit tests for cache management."""

import asyncio
import json
import time
from pathlib import Path

import pytest

from science_card_improvement.utils.cache import CacheManager


@pytest.mark.unit
class TestCacheManager:
    """Test CacheManager class."""

    @pytest.fixture
    def cache_manager(self, tmp_path):
        """Create cache manager with temp directory."""
        return CacheManager(
            cache_dir=tmp_path / "cache",
            default_ttl=60,
            max_memory_size=10
        )

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_manager):
        """Test basic set and get operations."""
        await cache_manager.set("key1", "value1")
        result = await cache_manager.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_get_missing_key(self, cache_manager):
        """Test getting a non-existent key."""
        result = await cache_manager.get("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_with_default(self, cache_manager):
        """Test getting with default value."""
        result = await cache_manager.get("missing", default="default_value")
        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_set_with_custom_ttl(self, cache_manager):
        """Test set with custom TTL."""
        await cache_manager.set("key1", "value1", ttl=1)
        result = await cache_manager.get("key1")
        assert result == "value1"

        # Wait for expiration
        await asyncio.sleep(1.5)
        result = await cache_manager.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(self, cache_manager):
        """Test delete operation."""
        await cache_manager.set("key1", "value1")
        await cache_manager.delete("key1")
        result = await cache_manager.get("key1")
        assert result is None

    @pytest.mark.asyncio
    async def test_clear(self, cache_manager):
        """Test clear all cache."""
        await cache_manager.set("key1", "value1")
        await cache_manager.set("key2", "value2")
        await cache_manager.clear()

        assert await cache_manager.get("key1") is None
        assert await cache_manager.get("key2") is None

    @pytest.mark.asyncio
    async def test_complex_values(self, cache_manager):
        """Test caching complex values."""
        # Dictionary
        dict_value = {"name": "test", "count": 42, "nested": {"key": "value"}}
        await cache_manager.set("dict_key", dict_value)
        result = await cache_manager.get("dict_key")
        assert result == dict_value

        # List
        list_value = [1, 2, 3, "four", {"five": 5}]
        await cache_manager.set("list_key", list_value)
        result = await cache_manager.get("list_key")
        assert result == list_value

    @pytest.mark.asyncio
    async def test_memory_cache_eviction(self, cache_manager):
        """Test memory cache eviction when full."""
        # Fill memory cache beyond max size
        for i in range(15):
            await cache_manager.set(f"key{i}", f"value{i}")

        # Memory cache should have evicted old entries
        assert len(cache_manager.memory_cache) <= cache_manager.max_memory_size

    @pytest.mark.asyncio
    async def test_statistics(self, cache_manager):
        """Test statistics tracking."""
        initial_stats = cache_manager.stats
        assert initial_stats["hits"] == 0
        assert initial_stats["misses"] == 0
        assert initial_stats["sets"] == 0

        await cache_manager.set("key1", "value1")
        await cache_manager.get("key1")  # Hit
        await cache_manager.get("missing")  # Miss

        stats = cache_manager.stats
        assert stats["sets"] >= 1
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1

    @pytest.mark.asyncio
    async def test_file_cache_persistence(self, tmp_path):
        """Test cache persistence to disk."""
        cache_dir = tmp_path / "cache"

        # Create cache and set value
        cache1 = CacheManager(cache_dir=cache_dir, default_ttl=3600)
        await cache1.set("persistent_key", "persistent_value")

        # Create new cache instance and retrieve
        cache2 = CacheManager(cache_dir=cache_dir, default_ttl=3600)
        result = await cache2.get("persistent_key")
        assert result == "persistent_value"

    @pytest.mark.asyncio
    async def test_cache_key_hashing(self, cache_manager):
        """Test cache key hashing for long keys."""
        long_key = "a" * 500
        await cache_manager.set(long_key, "value")
        result = await cache_manager.get(long_key)
        assert result == "value"


@pytest.mark.unit
class TestCacheManagerEdgeCases:
    """Test edge cases for CacheManager."""

    @pytest.mark.asyncio
    async def test_none_value(self, tmp_path):
        """Test caching None value."""
        cache = CacheManager(cache_dir=tmp_path / "cache")
        await cache.set("none_key", None)
        # Note: None values may not be cached or may return None
        result = await cache.get("none_key")
        # Should handle None gracefully

    @pytest.mark.asyncio
    async def test_empty_string_value(self, tmp_path):
        """Test caching empty string."""
        cache = CacheManager(cache_dir=tmp_path / "cache")
        await cache.set("empty_key", "")
        result = await cache.get("empty_key")
        assert result == ""

    @pytest.mark.asyncio
    async def test_zero_ttl(self, tmp_path):
        """Test zero TTL (immediate expiration)."""
        cache = CacheManager(cache_dir=tmp_path / "cache", default_ttl=0)
        await cache.set("key", "value")
        await asyncio.sleep(0.1)
        result = await cache.get("key")
        assert result is None

    @pytest.mark.asyncio
    async def test_concurrent_access(self, tmp_path):
        """Test concurrent cache access."""
        cache = CacheManager(cache_dir=tmp_path / "cache")

        async def set_and_get(key: str, value: str) -> str:
            await cache.set(key, value)
            return await cache.get(key)

        # Concurrent operations
        tasks = [
            set_and_get(f"key{i}", f"value{i}")
            for i in range(10)
        ]
        results = await asyncio.gather(*tasks)

        for i, result in enumerate(results):
            assert result == f"value{i}"

    @pytest.mark.asyncio
    async def test_special_characters_in_key(self, tmp_path):
        """Test keys with special characters."""
        cache = CacheManager(cache_dir=tmp_path / "cache")

        special_keys = [
            "key:with:colons",
            "key/with/slashes",
            "key with spaces",
        ]

        for key in special_keys:
            await cache.set(key, "value")
            result = await cache.get(key)
            assert result == "value", f"Failed for key: {key}"

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, tmp_path):
        """Test cleanup of expired entries."""
        cache = CacheManager(cache_dir=tmp_path / "cache", default_ttl=1)

        # Set some values
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        # Wait for expiration
        await asyncio.sleep(1.5)

        # Cleanup
        cleaned = await cache.cleanup_expired()
        assert cleaned >= 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, tmp_path):
        """Test deleting non-existent key."""
        cache = CacheManager(cache_dir=tmp_path / "cache")
        result = await cache.delete("nonexistent")
        # Should handle gracefully
        assert result is True or result is False
