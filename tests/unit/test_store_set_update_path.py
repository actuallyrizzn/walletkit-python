"""Test Store set/update path."""
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
async def test_store_set_updates_existing_via_update(storage, logger):
    """Test that set() calls update() for existing items."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"id": "key1", "value": 1})
    
    # Set again - should call update internally
    await store.set("key1", {"id": "key1", "value": 2, "new_field": "test"})
    
    item = store.get("key1")
    assert item["value"] == 2
    assert item["new_field"] == "test"

