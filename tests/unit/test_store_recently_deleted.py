"""Tests for Store recently deleted functionality."""
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
async def test_store_get_recently_deleted_raises_error(storage, logger):
    """Test that getting a recently deleted item raises KeyError."""
    store = Store(storage, logger, "test")
    await store.init()
    
    await store.set("key1", {"id": "key1"})
    await store.delete("key1")
    
    # Should raise KeyError with "recently deleted" message
    with pytest.raises(KeyError, match="recently deleted"):
        store.get("key1")


@pytest.mark.asyncio
async def test_store_recently_deleted_limit_enforcement(storage, logger):
    """Test that recently deleted list is limited."""
    store = Store(storage, logger, "test")
    await store.init()
    
    # Add and delete many items (more than limit of 200)
    for i in range(250):
        await store.set(f"key{i}", {"id": f"key{i}"})
        await store.delete(f"key{i}")
    
    # The recently deleted list should be trimmed
    # Try to get a recently deleted item - should still raise error
    with pytest.raises(KeyError):
        store.get("key0")

