"""Edge case tests for EventEmitter."""
import pytest

from walletkit.utils.events import EventEmitter


@pytest.mark.asyncio
async def test_event_emitter_off_nonexistent_listener():
    """Test removing non-existent listener."""
    emitter = EventEmitter()
    
    async def listener1(data):
        pass
    
    async def listener2(data):
        pass
    
    emitter.on("test", listener1)
    
    # Should not raise error
    emitter.off("test", listener2)
    
    assert emitter.listener_count("test") == 1


@pytest.mark.asyncio
async def test_event_emitter_listener_count_with_once():
    """Test listener_count includes once listeners."""
    emitter = EventEmitter()
    
    async def regular_listener(data):
        pass
    
    async def once_listener(data):
        pass
    
    emitter.on("test", regular_listener)
    emitter.once("test", once_listener)
    
    assert emitter.listener_count("test") == 2


@pytest.mark.asyncio
async def test_event_emitter_remove_listener_alias():
    """Test remove_listener is alias for off."""
    emitter = EventEmitter()
    
    async def listener(data):
        pass
    
    emitter.on("test", listener)
    emitter.remove_listener("test", listener)
    
    assert emitter.listener_count("test") == 0


@pytest.mark.asyncio
async def test_event_emitter_multiple_events():
    """Test managing multiple events."""
    emitter = EventEmitter()
    results = {"event1": [], "event2": [], "event3": []}
    
    async def listener1(data):
        results["event1"].append(data)
    
    async def listener2(data):
        results["event2"].append(data)
    
    async def listener3(data):
        results["event3"].append(data)
    
    emitter.on("event1", listener1)
    emitter.on("event2", listener2)
    emitter.on("event3", listener3)
    
    await emitter.emit("event1", "data1")
    await emitter.emit("event2", "data2")
    await emitter.emit("event3", "data3")
    
    assert results["event1"] == ["data1"]
    assert results["event2"] == ["data2"]
    assert results["event3"] == ["data3"]

