"""Extended tests for RequestStore."""
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


@pytest.fixture
async def request_store(storage, logger):
    """Create and initialize RequestStore."""
    store = RequestStore(storage, logger)
    await store.init()
    return store


@pytest.mark.asyncio
async def test_request_store_add_get(request_store):
    """Test adding and getting requests."""
    request = {
        "topic": "test_topic",
        "request": {
            "id": 1,
            "method": "eth_sendTransaction",
            "params": {},
        },
    }
    
    await request_store.add(request)
    
    requests = request_store.get_by_topic("test_topic")
    assert len(requests) == 1
    assert requests[0]["request"]["id"] == 1


@pytest.mark.asyncio
async def test_request_store_delete_by_topic(request_store):
    """Test deleting requests by topic."""
    request1 = {
        "topic": "topic1",
        "request": {"id": 1, "method": "test"},
    }
    request2 = {
        "topic": "topic1",
        "request": {"id": 2, "method": "test"},
    }
    request3 = {
        "topic": "topic2",
        "request": {"id": 3, "method": "test"},
    }
    
    await request_store.add(request1)
    await request_store.add(request2)
    await request_store.add(request3)
    
    assert request_store.length == 3
    
    await request_store.delete_by_topic("topic1")
    
    assert request_store.length == 1
    remaining = request_store.get_by_topic("topic2")
    assert len(remaining) == 1
    assert remaining[0]["request"]["id"] == 3


@pytest.mark.asyncio
async def test_request_store_get_all(request_store):
    """Test getting all requests."""
    await request_store.add({
        "topic": "topic1",
        "request": {"id": 1, "method": "test1"},
    })
    await request_store.add({
        "topic": "topic2",
        "request": {"id": 2, "method": "test2"},
    })
    
    all_requests = request_store.get_all()
    assert len(all_requests) == 2


@pytest.mark.asyncio
async def test_request_store_length(request_store):
    """Test request store length property."""
    assert request_store.length == 0
    
    await request_store.add({
        "topic": "topic1",
        "request": {"id": 1, "method": "test"},
    })
    
    assert request_store.length == 1
    
    await request_store.add({
        "topic": "topic2",
        "request": {"id": 2, "method": "test"},
    })
    
    assert request_store.length == 2

