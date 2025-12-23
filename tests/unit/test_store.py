"""Tests for Store implementations."""
from typing import Any, Dict

import pytest

from walletkit.controllers.proposal_store import ProposalStore
from walletkit.controllers.request_store import RequestStore
from walletkit.controllers.session_store import SessionStore
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
async def test_store_basic_operations(storage, logger):
    """Test basic store operations."""
    store = Store(storage, logger, "test_store")
    await store.init()

    # Set and get
    await store.set("key1", {"value": "test1"})
    assert store.get("key1") == {"value": "test1"}
    assert store.length == 1

    # Update
    await store.update("key1", {"value": "updated"})
    assert store.get("key1") == {"value": "updated"}

    # Delete
    await store.delete("key1")
    assert store.length == 0
    with pytest.raises(KeyError):
        store.get("key1")


@pytest.mark.asyncio
async def test_store_persistence(storage, logger):
    """Test store persistence."""
    # Use a store with get_key function for proper restoration
    def get_key(data: Dict[str, Any]) -> str:
        return data.get("key", "")
    
    store = Store(storage, logger, "test_store", get_key=get_key)
    await store.init()

    await store.set("key1", {"key": "key1", "value": "test1"})
    await store.set("key2", {"key": "key2", "value": "test2"})

    # Create new store instance and restore
    store2 = Store(storage, logger, "test_store", get_key=get_key)
    await store2.init()

    assert store2.length == 2
    assert store2.get("key1") == {"key": "key1", "value": "test1"}
    assert store2.get("key2") == {"key": "key2", "value": "test2"}


@pytest.mark.asyncio
async def test_store_get_all(storage, logger):
    """Test get_all with filtering."""
    store = Store(storage, logger, "test_store")
    await store.init()

    await store.set("key1", {"type": "a", "value": 1})
    await store.set("key2", {"type": "a", "value": 2})
    await store.set("key3", {"type": "b", "value": 3})

    all_items = store.get_all()
    assert len(all_items) == 3

    filtered = store.get_all({"type": "a"})
    assert len(filtered) == 2


@pytest.mark.asyncio
async def test_session_store(storage, logger):
    """Test SessionStore."""
    store = SessionStore(storage, logger)
    await store.init()

    session = {"topic": "topic1", "peer": {"metadata": {}}}
    await store.set("topic1", session)

    assert store.get("topic1") == session
    assert store.length == 1


@pytest.mark.asyncio
async def test_proposal_store(storage, logger):
    """Test ProposalStore."""
    store = ProposalStore(storage, logger)
    await store.init()

    proposal = {"id": 123, "params": {}}
    await store.set(123, proposal)

    assert store.get(123) == proposal
    assert store.length == 1


@pytest.mark.asyncio
async def test_request_store(storage, logger):
    """Test RequestStore."""
    store = RequestStore(storage, logger)
    await store.init()

    request = {
        "topic": "topic1",
        "request": {"id": 1, "method": "eth_sendTransaction", "params": {}},
    }
    await store.add(request)

    assert store.length == 1
    assert len(store.get_by_topic("topic1")) == 1
    assert store.get_by_id(1) == request

    await store.delete(1)
    assert store.length == 0

