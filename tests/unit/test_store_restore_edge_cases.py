"""Edge case tests for Store restore functionality."""
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
async def test_store_restore_with_existing_data_raises_error(storage, logger):
    """Test that restore raises error if store already has data."""
    store = Store(storage, logger, "test")
    await store.init()
    
    # Add some data
    await store.set("key1", {"id": "key1"})
    
    # Try to restore - should raise RuntimeError
    with pytest.raises(RuntimeError, match="Restore would override existing data"):
        await store._restore()


@pytest.mark.asyncio
async def test_store_restore_with_non_list_data(storage, logger):
    """Test that restore handles non-list data gracefully."""
    store = Store(storage, logger, "test")
    
    # Put non-list data in storage
    await storage.set_item(store.storage_key, "not a list")
    
    # Should not raise error, just skip restore
    await store._restore()
    await store.init()
    
    assert store.length == 0


@pytest.mark.asyncio
async def test_store_restore_with_empty_list(storage, logger):
    """Test that restore handles empty list."""
    store = Store(storage, logger, "test")
    
    # Put empty list in storage
    await storage.set_item(store.storage_key, [])
    
    # Should not raise error
    await store._restore()
    await store.init()
    
    assert store.length == 0

