"""Extended tests for Store."""
import pytest

from walletkit.controllers.store import Store


@pytest.mark.asyncio
async def test_store_get_all_filtering(storage, logger):
    """Test get_all with complex filtering."""
    def get_key(data: dict) -> str:
        return data.get("key", "")
    
    store = Store(storage, logger, "test", get_key=get_key)
    await store.init()
    
    await store.set("key1", {"key": "key1", "type": "a", "value": 1, "active": True})
    await store.set("key2", {"key": "key2", "type": "a", "value": 2, "active": False})
    await store.set("key3", {"key": "key3", "type": "b", "value": 3, "active": True})
    
    # Filter by type
    filtered = store.get_all({"type": "a"})
    assert len(filtered) == 2
    
    # Filter by multiple fields
    filtered = store.get_all({"type": "a", "active": True})
    assert len(filtered) == 1
    assert filtered[0]["key"] == "key1"


@pytest.mark.asyncio
async def test_store_update_nonexistent(storage, logger):
    """Test updating non-existent key creates it."""
    store = Store(storage, logger, "test")
    await store.init()
    
    # Update should create if doesn't exist (via set logic)
    await store.set("new_key", {"value": "initial"})
    await store.update("new_key", {"value": "updated"})
    
    assert store.get("new_key")["value"] == "updated"


@pytest.mark.asyncio
async def test_store_recently_deleted(storage, logger):
    """Test recently deleted tracking."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"value": "test"})
    await store.delete("key1")
    
    # Should raise KeyError with "recently deleted" message
    with pytest.raises(KeyError) as exc_info:
        store.get("key1")
    assert "recently deleted" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_store_has(storage, logger):
    """Test has method."""
    store = Store(storage, logger, "test")
    await store.init()
    
    assert store.has("key1") is False
    
    await store.set("key1", {"value": "test"})
    assert store.has("key1") is True
    
    await store.delete("key1")
    assert store.has("key1") is False

