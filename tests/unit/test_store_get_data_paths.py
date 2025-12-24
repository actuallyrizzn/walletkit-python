"""Test Store _get_data paths."""
import pytest

from walletkit.controllers.store import Store


@pytest.mark.asyncio
async def test_store_get_data_recently_deleted_error(storage, logger):
    """Test _get_data raises error for recently deleted items."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"id": "key1"})
    await store.delete("key1")
    
    # Should raise KeyError with "recently deleted" message
    with pytest.raises(KeyError, match="recently deleted"):
        store._get_data("key1")


@pytest.mark.asyncio
async def test_store_get_data_nonexistent_error(storage, logger):
    """Test _get_data raises error for nonexistent items."""
    store = Store(storage, logger, "test")
    await store.init()
    
    # Should raise KeyError with "No matching key" message
    with pytest.raises(KeyError, match="No matching key"):
        store._get_data("nonexistent")

