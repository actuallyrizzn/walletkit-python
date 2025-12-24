"""Extended tests for EventClient."""
import pytest

from walletkit.controllers.event_client import EventClient


@pytest.fixture
async def event_client(storage, logger):
    """Create and initialize EventClient."""
    client = EventClient(storage, logger, telemetry_enabled=False)
    await client.init()
    return client


@pytest.mark.asyncio
async def test_event_client_initialization(event_client):
    """Test EventClient initialization."""
    assert event_client._initialized
    assert not event_client.telemetry_enabled


@pytest.mark.asyncio
async def test_event_client_send_event(event_client):
    """Test sending events."""
    from walletkit.controllers.event_client import Event
    import time
    
    # Create event objects
    event = Event(
        event_id="test_id",
        event_type="test_event",
        timestamp=int(time.time() * 1000),
        props={"test": "data"},
    )
    
    # Should not raise error even if telemetry is disabled
    await event_client.send_event([event])


@pytest.mark.asyncio
async def test_event_client_with_telemetry(storage, logger):
    """Test EventClient with telemetry enabled."""
    client = EventClient(storage, logger, telemetry_enabled=True)
    await client.init()
    
    assert client.telemetry_enabled


@pytest.mark.asyncio
async def test_event_class_methods():
    """Test Event class methods."""
    from walletkit.controllers.event_client import Event
    import time
    
    event = Event(
        event_id="test_id",
        event_type="test_event",
        timestamp=int(time.time() * 1000),
        props={"test": "data"},
    )
    
    # Test add_trace
    event.add_trace("trace1")
    event.add_trace("trace2")
    assert len(event.traces) == 2
    assert "trace1" in event.traces
    assert "trace2" in event.traces
    
    # Test set_error
    event.set_error("error_message")
    assert event.error == "error_message"
    assert event.props["type"] == "error_message"
    
    # Test to_dict
    event_dict = event.to_dict()
    assert event_dict["eventId"] == "test_id"
    assert event_dict["eventType"] == "test_event"
    assert event_dict["traces"] == ["trace1", "trace2"]
    assert event_dict["error"] == "error_message"


@pytest.mark.asyncio
async def test_event_client_create_event(event_client):
    """Test create_event method."""
    event = event_client.create_event("test_event", props={"key": "value"})
    
    assert event is not None
    assert event.event_type == "test_event"
    assert event.props == {"key": "value"}
    assert event.event_id in event_client.events


@pytest.mark.asyncio
async def test_event_client_create_event_with_timestamp(event_client):
    """Test create_event with custom timestamp."""
    timestamp = 1234567890
    event = event_client.create_event("test_event", timestamp=timestamp)
    
    assert event.timestamp == timestamp


@pytest.mark.asyncio
async def test_event_client_get_event(event_client):
    """Test get_event method."""
    event = event_client.create_event("test_event")
    event_id = event.event_id
    
    retrieved = event_client.get_event(event_id)
    assert retrieved == event
    
    # Test nonexistent event
    assert event_client.get_event("nonexistent") is None


@pytest.mark.asyncio
async def test_event_client_delete_event(event_client):
    """Test delete_event method."""
    event = event_client.create_event("test_event")
    event_id = event.event_id
    
    assert event_id in event_client.events
    
    event_client.delete_event(event_id)
    assert event_id not in event_client.events
    
    # Should not raise error for nonexistent
    event_client.delete_event("nonexistent")


@pytest.mark.asyncio
async def test_event_client_send_event_with_telemetry(storage, logger):
    """Test send_event with telemetry enabled."""
    from walletkit.controllers.event_client import Event
    import time
    
    client = EventClient(storage, logger, telemetry_enabled=True)
    await client.init()
    
    event = Event(
        event_id="test_id",
        event_type="test_event",
        timestamp=int(time.time() * 1000),
    )
    
    # Should log when telemetry is enabled
    await client.send_event([event])


@pytest.mark.asyncio
async def test_event_client_restore(storage, logger):
    """Test _restore method."""
    from walletkit.controllers.event_client import Event
    
    # Store some events
    events_data = [
        {
            "eventId": "id1",
            "eventType": "type1",
            "timestamp": 1234567890,
            "props": {"key": "value"},
            "traces": ["trace1"],
            "error": None,
        },
        {
            "eventId": "id2",
            "eventType": "type2",
            "timestamp": 1234567891,
            "props": {},
            "traces": [],
            "error": "error_msg",
        },
    ]
    
    await storage.set_item("wc@2:core:1.0//event-client", events_data)
    
    client = EventClient(storage, logger, telemetry_enabled=True)
    await client.init()
    
    assert len(client.events) == 2
    assert "id1" in client.events
    assert "id2" in client.events


@pytest.mark.asyncio
async def test_event_client_restore_with_none(storage, logger):
    """Test _restore with None data."""
    await storage.set_item("wc@2:core:1.0//event-client", None)
    
    client = EventClient(storage, logger, telemetry_enabled=True)
    await client.init()
    
    assert len(client.events) == 0


@pytest.mark.asyncio
async def test_event_client_restore_with_non_list(storage, logger):
    """Test _restore with non-list data."""
    await storage.set_item("wc@2:core:1.0//event-client", {"not": "a list"})
    
    client = EventClient(storage, logger, telemetry_enabled=True)
    await client.init()
    
    assert len(client.events) == 0


@pytest.mark.asyncio
async def test_event_client_restore_exception(storage, logger):
    """Test _restore exception handling."""
    from unittest.mock import patch
    
    with patch.object(storage, "get_item", side_effect=Exception("Storage error")):
        client = EventClient(storage, logger, telemetry_enabled=True)
        # Should handle exception gracefully
        await client.init()
        assert len(client.events) == 0


@pytest.mark.asyncio
async def test_event_client_restore_missing_event_id(storage, logger):
    """Test _restore with event missing eventId."""
    events_data = [
        {
            "eventType": "type1",
            "timestamp": 1234567890,
        },
    ]
    
    await storage.set_item("wc@2:core:1.0//event-client", events_data)
    
    client = EventClient(storage, logger, telemetry_enabled=True)
    await client.init()
    
    # Should skip events without eventId
    assert len(client.events) == 0


@pytest.mark.asyncio
async def test_event_client_persist(storage, logger):
    """Test _persist method."""
    client = EventClient(storage, logger, telemetry_enabled=True)
    await client.init()
    
    # Create some events
    event1 = client.create_event("type1")
    event2 = client.create_event("type2")
    
    # Persist
    await client._persist()
    
    # Verify persisted
    persisted = await storage.get_item(client.storage_key)
    assert persisted is not None
    assert len(persisted) == 2


@pytest.mark.asyncio
async def test_event_client_persist_disabled(storage, logger):
    """Test _persist when telemetry is disabled."""
    client = EventClient(storage, logger, telemetry_enabled=False)
    await client.init()
    
    client.create_event("type1")
    
    # Should not persist when disabled
    await client._persist()
    
    persisted = await storage.get_item(client.storage_key)
    assert persisted is None


@pytest.mark.asyncio
async def test_event_client_init_idempotent(event_client):
    """Test init is idempotent."""
    initial_events = len(event_client.events)
    
    # Call init again
    await event_client.init()
    
    # Should not duplicate
    assert len(event_client.events) == initial_events
