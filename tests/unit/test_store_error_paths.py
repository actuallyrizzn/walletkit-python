"""Tests for Store error paths."""
import pytest

from walletkit.controllers.store import Store
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create storage instance."""
    return MemoryStorage()


@pytest.fixture
def logger():
    """Create logger instance."""
    class SimpleLogger:
        def info(self, msg: str) -> None:
            pass

        def debug(self, msg: str) -> None:
            pass

        def error(self, msg: str) -> None:
            pass

    return SimpleLogger()


@pytest.mark.asyncio
async def test_store_get_nonexistent_not_recently_deleted(storage, logger):
    """Test getting non-existent item that wasn't recently deleted."""
    store = Store(storage, logger, "test")
    await store.init()
    
    # Should raise KeyError with "No matching key" message
    with pytest.raises(KeyError, match="No matching key"):
        store.get("nonexistent")


@pytest.mark.asyncio
async def test_store_set_updates_existing(storage, logger):
    """Test that set() updates existing items."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"id": "key1", "value": 1})
    assert store.get("key1")["value"] == 1
    
    # Set again with new value
    await store.set("key1", {"id": "key1", "value": 2})
    assert store.get("key1")["value"] == 2


@pytest.mark.asyncio
async def test_store_delete_with_reason(storage, logger):
    """Test deleting with a reason."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"id": "key1"})
    await store.delete("key1", reason="test reason")
    
    assert store.length == 0
    with pytest.raises(KeyError):
        store.get("key1")

