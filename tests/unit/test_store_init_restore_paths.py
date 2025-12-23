"""Test Store init restore paths."""
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
async def test_store_init_restores_with_get_key(storage, logger):
    """Test that init restores items using get_key function."""
    def get_key(data: dict) -> str:
        return data.get("id", "")
    
    # First instance - set data
    store1 = Store(storage, logger, "test", get_key=get_key)
    await store1.init()
    await store1.set("key1", {"id": "key1", "value": 1})
    
    # Second instance - should restore
    store2 = Store(storage, logger, "test", get_key=get_key)
    await store2.init()
    
    assert store2.length == 1
    assert store2.get("key1")["value"] == 1


@pytest.mark.asyncio
async def test_store_init_restores_without_get_key_infers_id(storage, logger):
    """Test that init restores items inferring key from 'id' field."""
    # First instance - set data
    store1 = Store(storage, logger, "test")
    await store1.init()
    await store1.set("key1", {"id": "key1", "value": 1})
    
    # Second instance - should restore using 'id' field
    store2 = Store(storage, logger, "test")
    await store2.init()
    
    assert store2.length == 1
    assert store2.get("key1")["value"] == 1


@pytest.mark.asyncio
async def test_store_init_restores_without_get_key_infers_topic(storage, logger):
    """Test that init restores items inferring key from 'topic' field."""
    # First instance - set data
    store1 = Store(storage, logger, "test")
    await store1.init()
    await store1.set("topic1", {"topic": "topic1", "value": 1})
    
    # Second instance - should restore using 'topic' field
    store2 = Store(storage, logger, "test")
    await store2.init()
    
    assert store2.length == 1
    assert store2.get("topic1")["value"] == 1

