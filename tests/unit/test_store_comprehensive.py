"""Comprehensive tests for Store base class."""
import pytest

from walletkit.controllers.store import Store


@pytest.mark.asyncio
async def test_store_values(storage, logger):
    """Test getting all values."""
    def get_key(data: dict) -> str:
        return data.get("id", "")
    
    store = Store(storage, logger, "test", get_key=get_key)
    await store.init()
    
    await store.set("key1", {"id": "key1", "value": 1})
    await store.set("key2", {"id": "key2", "value": 2})
    
    values = store.values
    assert len(values) == 2
    assert any(v["id"] == "key1" for v in values)
    assert any(v["id"] == "key2" for v in values)


@pytest.mark.asyncio
async def test_store_keys(storage, logger):
    """Test getting all keys."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"value": 1})
    await store.set("key2", {"value": 2})
    
    keys = store.keys
    assert len(keys) == 2
    assert "key1" in keys
    assert "key2" in keys


@pytest.mark.asyncio
async def test_store_delete_nonexistent(storage, logger):
    """Test deleting non-existent key."""
    store = Store(storage, logger, "test")
    await store.init()
    
    # Should not raise error
    await store.delete("nonexistent")


@pytest.mark.asyncio
async def test_store_clear(storage, logger):
    """Test clearing all items by deleting them."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"value": 1})
    await store.set("key2", {"value": 2})
    
    assert store.length == 2
    
    # Clear by deleting all keys
    for key in list(store.keys):
        await store.delete(key)
    
    assert store.length == 0
    assert len(store.keys) == 0


@pytest.mark.asyncio
async def test_store_get_all_empty_filter(storage, logger):
    """Test get_all with empty filter returns all."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"type": "a", "value": 1})
    await store.set("key2", {"type": "b", "value": 2})
    
    all_items = store.get_all({})
    assert len(all_items) == 2


@pytest.mark.asyncio
async def test_store_update_existing(storage, logger):
    """Test updating existing item."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"value": 1, "name": "original"})
    
    await store.update("key1", {"name": "updated"})
    
    item = store.get("key1")
    assert item["value"] == 1  # Should preserve existing
    assert item["name"] == "updated"  # Should update

