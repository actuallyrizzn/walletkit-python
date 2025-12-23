"""Tests for RequestStore restore functionality."""
import pytest

from walletkit.controllers.request_store import RequestStore
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


# Note: The restore method catches RuntimeError internally, so we can't easily test
# the error path without mocking. This is acceptable as the error handling is tested
# in the Store base class tests.


@pytest.mark.asyncio
async def test_request_store_restore_with_non_list_data(storage, logger):
    """Test that restore handles non-list data gracefully."""
    store = RequestStore(storage, logger)
    
    # Put non-list data in storage
    await storage.set_item(store.storage_key, "not a list")
    
    # Should not raise error, just skip restore
    await store._restore()
    await store.init()
    
    assert store.length == 0


@pytest.mark.asyncio
async def test_request_store_restore_with_empty_list(storage, logger):
    """Test that restore handles empty list."""
    store = RequestStore(storage, logger)
    
    # Put empty list in storage
    await storage.set_item(store.storage_key, [])
    
    # Should not raise error
    await store._restore()
    await store.init()
    
    assert store.length == 0

