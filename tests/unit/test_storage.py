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


@pytest.mark.asyncio
async def test_file_storage_default_path():
    """Test FileStorage with default path."""
    storage = FileStorage()
    assert storage.storage_path.exists()
    
    # Clean up
    await storage.set_item("test_key", "test_value")
    await storage.remove_item("test_key")


@pytest.mark.asyncio
async def test_file_storage_load_cache_error():
    """Test FileStorage _load_cache with corrupted file."""
    import tempfile
    import json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir)
        
        # Create a corrupted JSON file
        bad_file = storage_path / "bad_file.json"
        with open(bad_file, "w") as f:
            f.write("invalid json{")
        
        # Should handle error gracefully
        storage = FileStorage(storage_path)
        # Should not raise exception


@pytest.mark.asyncio
async def test_file_storage_get_item_file_error():
    """Test FileStorage get_item with file read error."""
    import tempfile
    from unittest.mock import patch
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileStorage(Path(tmpdir))
        
        # Set an item first
        await storage.set_item("test_key", "test_value")
        
        # Clear cache to force file read
        storage._cache.clear()
        
        # Mock file read to raise exception
        with patch("builtins.open", side_effect=Exception("Read error")):
            result = await storage.get_item("test_key")
            # Should return None on error
            assert result is None


@pytest.mark.asyncio
async def test_file_storage_set_item_write_error():
    """Test FileStorage set_item with write error."""
    import tempfile
    from unittest.mock import patch
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileStorage(Path(tmpdir))
        
        # Mock file write to raise exception
        with patch("builtins.open", side_effect=Exception("Write error")):
            with pytest.raises(Exception, match="Write error"):
                await storage.set_item("test_key", "test_value")
            
            # Should be removed from cache on error
            assert "test_key" not in storage._cache


@pytest.mark.asyncio
async def test_file_storage_remove_item_error():
    """Test FileStorage remove_item with unlink error."""
    import tempfile
    from unittest.mock import patch
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileStorage(Path(tmpdir))
        
        # Create a file
        await storage.set_item("test_key", "test_value")
        
        # Mock unlink to raise exception
        with patch("pathlib.Path.unlink", side_effect=Exception("Unlink error")):
            # Should handle error gracefully
            await storage.remove_item("test_key")
            
            # Should still be removed from cache
            assert "test_key" not in storage._cache


@pytest.mark.asyncio
async def test_file_storage_get_item_nonexistent():
    """Test FileStorage get_item with nonexistent key."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileStorage(Path(tmpdir))
        
        result = await storage.get_item("nonexistent")
        assert result is None


@pytest.mark.asyncio
async def test_memory_storage_remove_nonexistent():
    """Test MemoryStorage remove_item with nonexistent key."""
    storage = MemoryStorage()
    
    # Should not raise error
    await storage.remove_item("nonexistent")
    
    # Should still work normally
    await storage.set_item("key1", "value1")
    await storage.remove_item("key1")
    assert await storage.get_item("key1") is None


@pytest.mark.asyncio
async def test_file_storage_key_sanitization():
    """Test FileStorage key sanitization for filesystem."""
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileStorage(Path(tmpdir))
        
        # Test keys with special characters
        await storage.set_item("key/with/slashes", "value1")
        await storage.set_item("key\\with\\backslashes", "value2")
        
        assert await storage.get_item("key/with/slashes") == "value1"
        assert await storage.get_item("key\\with\\backslashes") == "value2"
        
        # Test get_keys includes sanitized keys
        keys = await storage.get_keys()
        assert "key/with/slashes" in keys
        assert "key\\with\\backslashes" in keys


@pytest.mark.asyncio
async def test_file_storage_load_cache_nonexistent_dir():
    """Test FileStorage _load_cache when directory doesn't exist."""
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = Path(tmpdir)
        # Remove directory
        shutil.rmtree(tmpdir)
        
        # Should handle gracefully
        storage = FileStorage(storage_path)
        assert storage.storage_path.exists()  # Should be created
