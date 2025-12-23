"""Extended tests for storage implementations."""
import pytest
import tempfile
import os

from walletkit.utils.storage import FileStorage, MemoryStorage, IKeyValueStorage


@pytest.mark.asyncio
async def test_memory_storage_get_set_delete():
    """Test MemoryStorage get/set/delete operations."""
    storage = MemoryStorage()
    
    # Set and get
    await storage.set_item("key1", "value1")
    assert await storage.get_item("key1") == "value1"
    
    # Update
    await storage.set_item("key1", "value1_updated")
    assert await storage.get_item("key1") == "value1_updated"
    
    # Delete
    await storage.remove_item("key1")
    assert await storage.get_item("key1") is None


@pytest.mark.asyncio
async def test_memory_storage_get_all():
    """Test MemoryStorage get_all operation."""
    storage = MemoryStorage()
    
    await storage.set_item("key1", "value1")
    await storage.set_item("key2", "value2")
    await storage.set_item("key3", "value3")
    
    # Get all items by iterating keys
    keys = await storage.get_keys()
    assert len(keys) == 3
    assert "key1" in keys
    assert "key2" in keys
    assert "key3" in keys
    
    # Verify values
    assert await storage.get_item("key1") == "value1"
    assert await storage.get_item("key2") == "value2"
    assert await storage.get_item("key3") == "value3"


@pytest.mark.asyncio
async def test_file_storage_persistence():
    """Test FileStorage persistence across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "test_storage.json")
        
        # Create first storage instance and write
        storage1 = FileStorage(storage_path)
        await storage1.set_item("key1", "value1")
        await storage1.set_item("key2", "value2")
        
        # Create second storage instance and read (will reload from disk)
        storage2 = FileStorage(storage_path)
        assert await storage2.get_item("key1") == "value1"
        assert await storage2.get_item("key2") == "value2"
        
        # Update from second instance
        await storage2.set_item("key1", "value1_updated")
        
        # Create third instance to verify persistence (storage1 cache may be stale)
        storage3 = FileStorage(storage_path)
        assert await storage3.get_item("key1") == "value1_updated"


@pytest.mark.asyncio
async def test_file_storage_delete():
    """Test FileStorage delete operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "test_storage.json")
        storage = FileStorage(storage_path)
        
        await storage.set_item("key1", "value1")
        await storage.set_item("key2", "value2")
        
        await storage.remove_item("key1")
        
        assert await storage.get_item("key1") is None
        
        assert await storage.get_item("key2") == "value2"


@pytest.mark.asyncio
async def test_file_storage_get_all():
    """Test FileStorage get_all operation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "test_storage.json")
        storage = FileStorage(storage_path)
        
        await storage.set_item("key1", "value1")
        await storage.set_item("key2", "value2")
        
        # Get all items by iterating keys
        keys = await storage.get_keys()
        assert len(keys) == 2
        assert "key1" in keys
        assert "key2" in keys
        
        # Verify values
        assert await storage.get_item("key1") == "value1"
        assert await storage.get_item("key2") == "value2"

