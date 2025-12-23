"""Tests for storage implementations."""
import pytest
import tempfile
from pathlib import Path

from walletkit.utils.storage import FileStorage, MemoryStorage


@pytest.mark.asyncio
async def test_memory_storage():
    """Test memory storage."""
    storage = MemoryStorage()

    # Test set and get
    await storage.set_item("key1", "value1")
    assert await storage.get_item("key1") == "value1"

    # Test remove
    await storage.remove_item("key1")
    assert await storage.get_item("key1") is None

    # Test get_keys
    await storage.set_item("key1", "value1")
    await storage.set_item("key2", "value2")
    keys = await storage.get_keys()
    assert set(keys) == {"key1", "key2"}


@pytest.mark.asyncio
async def test_file_storage():
    """Test file storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileStorage(Path(tmpdir))

        # Test set and get
        await storage.set_item("key1", "value1")
        assert await storage.get_item("key1") == "value1"

        # Test complex data
        await storage.set_item("key2", {"nested": {"data": 123}})
        result = await storage.get_item("key2")
        assert result == {"nested": {"data": 123}}

        # Test remove
        await storage.remove_item("key1")
        assert await storage.get_item("key1") is None

        # Test get_keys
        keys = await storage.get_keys()
        assert "key2" in keys

