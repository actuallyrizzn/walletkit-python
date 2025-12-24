"""Edge case tests for Store."""
import pytest

from walletkit.controllers.store import Store


@pytest.mark.asyncio
async def test_store_get_nonexistent(storage, logger):
    """Test getting non-existent item."""
    store = Store(storage, logger, "test")
    await store.init()
    
    with pytest.raises(KeyError):
        store.get("nonexistent")


@pytest.mark.asyncio
async def test_store_get_all_with_complex_filter(storage, logger):
    """Test get_all with complex filter."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"id": "key1", "type": "A", "status": "active", "value": 1})
    await store.set("key2", {"id": "key2", "type": "B", "status": "active", "value": 2})
    await store.set("key3", {"id": "key3", "type": "A", "status": "inactive", "value": 3})
    
    # Filter by multiple conditions
    results = store.get_all({"type": "A", "status": "active"})
    assert len(results) == 1
    assert results[0]["id"] == "key1"


@pytest.mark.asyncio
async def test_store_delete_tracks_recently_deleted(storage, logger):
    """Test that delete tracks recently deleted items."""
    store = Store(storage, logger, "test")
    await store.init()
    
    # Add and delete items
    await store.set("key1", {"id": "key1"})
    await store.set("key2", {"id": "key2"})
    
    await store.delete("key1")
    await store.delete("key2")
    
    # Check that items are deleted
    assert store.length == 0
    with pytest.raises(KeyError):
        store.get("key1")


@pytest.mark.asyncio
async def test_store_persistence_with_get_key(storage, logger):
    """Test store persistence with get_key function."""
    def get_key(data: dict) -> str:
        return data.get("id", "")
    
    store1 = Store(storage, logger, "test", get_key=get_key)
    await store1.init()
    
    await store1.set("key1", {"id": "key1", "value": 1})
    await store1.set("key2", {"id": "key2", "value": 2})
    
    # Create new instance - should restore
    store2 = Store(storage, logger, "test", get_key=get_key)
    await store2.init()
    
    assert store2.length == 2
    assert store2.get("key1")["value"] == 1
    assert store2.get("key2")["value"] == 2

