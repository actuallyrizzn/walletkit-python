"""Comprehensive tests for RequestStore."""
import pytest

from walletkit.controllers.request_store import RequestStore


@pytest.fixture
async def request_store(storage, logger):
    """Create and initialize RequestStore."""
    store = RequestStore(storage, logger)
    await store.init()
    return store


@pytest.mark.asyncio
async def test_request_store_get_by_id(request_store):
    """Test getting request by ID."""
    request1 = {
        "topic": "topic1",
        "request": {"id": 1, "method": "test1"},
    }
    request2 = {
        "topic": "topic2",
        "request": {"id": 2, "method": "test2"},
    }
    
    await request_store.add(request1)
    await request_store.add(request2)
    
    found = request_store.get_by_id(1)
    assert found["request"]["id"] == 1
    assert found["request"]["method"] == "test1"
    
    found = request_store.get_by_id(2)
    assert found["request"]["id"] == 2
    assert found["request"]["method"] == "test2"


@pytest.mark.asyncio
async def test_request_store_get_by_id_nonexistent(request_store):
    """Test getting non-existent request by ID."""
    with pytest.raises(KeyError):
        request_store.get_by_id(999)


@pytest.mark.asyncio
async def test_request_store_delete_by_id(request_store):
    """Test deleting request by ID."""
    request1 = {
        "topic": "topic1",
        "request": {"id": 1, "method": "test1"},
    }
    request2 = {
        "topic": "topic2",
        "request": {"id": 2, "method": "test2"},
    }
    
    await request_store.add(request1)
    await request_store.add(request2)
    
    assert request_store.length == 2
    
    await request_store.delete(1)  # Use delete() method, not delete_by_id()
    
    assert request_store.length == 1
    assert request_store.get_by_id(2)["request"]["id"] == 2
    
    with pytest.raises(KeyError):
        request_store.get_by_id(1)


@pytest.mark.asyncio
async def test_request_store_delete_by_id_nonexistent(request_store):
    """Test deleting non-existent request by ID."""
    # Should not raise error
    await request_store.delete(999)  # Use delete() method


@pytest.mark.asyncio
async def test_request_store_persistence(storage, logger):
    """Test request store persistence."""
    store1 = RequestStore(storage, logger)
    await store1.init()
    
    await store1.add({
        "topic": "topic1",
        "request": {"id": 1, "method": "test"},
    })
    
    # Create new instance - should restore
    store2 = RequestStore(storage, logger)
    await store2.init()
    
    assert store2.length == 1
    assert store2.get_by_id(1)["request"]["id"] == 1

