"""Final tests for storage utilities."""
import pytest

from walletkit.utils.storage import MemoryStorage, FileStorage


@pytest.mark.asyncio
async def test_memory_storage_get_keys():
    """Test getting all keys from memory storage."""
    storage = MemoryStorage()
    
    await storage.set_item("key1", "value1")
    await storage.set_item("key2", "value2")
    
    keys = await storage.get_keys()
    assert len(keys) == 2
    assert "key1" in keys
    assert "key2" in keys


@pytest.mark.asyncio
async def test_file_storage_get_keys(tmp_path):
    """Test getting all keys from file storage."""
    storage = FileStorage(storage_path=tmp_path / "test_storage")
    
    await storage.set_item("key1", "value1")
    await storage.set_item("key2", "value2")
    
    keys = await storage.get_keys()
    assert len(keys) == 2
    assert "key1" in keys
    assert "key2" in keys


@pytest.mark.asyncio
async def test_memory_storage_remove_nonexistent():
    """Test removing non-existent key from memory storage."""
    storage = MemoryStorage()
    
    # Should not raise error
    await storage.remove_item("nonexistent")


@pytest.mark.asyncio
async def test_file_storage_remove_nonexistent(tmp_path):
    """Test removing non-existent key from file storage."""
    storage = FileStorage(storage_path=tmp_path / "test_storage")
    
    # Should not raise error
    await storage.remove_item("nonexistent")

