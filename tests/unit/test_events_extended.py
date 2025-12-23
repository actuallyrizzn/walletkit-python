"""Extended tests for EventEmitter."""
import pytest

from walletkit.utils.events import EventEmitter


@pytest.mark.asyncio
async def test_event_emitter_remove_listener():
    """Test removing a specific listener."""
    emitter = EventEmitter()
    
    async def listener1(data):
        pass
    
    async def listener2(data):
        pass
    
    emitter.on("test", listener1)
    emitter.on("test", listener2)
    
    assert len(emitter._listeners.get("test", [])) == 2
    
    emitter.remove_listener("test", listener1)
    
    assert len(emitter._listeners.get("test", [])) == 1
    assert listener2 in emitter._listeners.get("test", [])


@pytest.mark.asyncio
async def test_event_emitter_remove_all_listeners():
    """Test removing all listeners for an event."""
    emitter = EventEmitter()
    
    async def listener1(data):
        pass
    
    async def listener2(data):
        pass
    
    emitter.on("test", listener1)
    emitter.on("test", listener2)
    emitter.on("other", listener1)
    
    emitter.remove_all_listeners("test")
    
    assert "test" not in emitter._listeners or len(emitter._listeners.get("test", [])) == 0
    assert len(emitter._listeners.get("other", [])) == 1


@pytest.mark.asyncio
async def test_event_emitter_listener_count():
    """Test getting listener count."""
    emitter = EventEmitter()
    
    async def listener1(data):
        pass
    
    async def listener2(data):
        pass
    
    assert emitter.listener_count("test") == 0
    
    emitter.on("test", listener1)
    assert emitter.listener_count("test") == 1
    
    emitter.on("test", listener2)
    assert emitter.listener_count("test") == 2
    
    emitter.off("test", listener1)
    assert emitter.listener_count("test") == 1


@pytest.mark.asyncio
async def test_event_emitter_listeners():
    """Test getting listeners for an event."""
    emitter = EventEmitter()
    
    async def listener1(data):
        pass
    
    async def listener2(data):
        pass
    
    emitter.on("test", listener1)
    emitter.on("test", listener2)
    
    # Check internal listeners dict
    listeners = emitter._listeners.get("test", [])
    assert len(listeners) == 2
    assert listener1 in listeners
    assert listener2 in listeners


@pytest.mark.asyncio
async def test_event_emitter_emit_multiple_listeners():
    """Test emitting to multiple listeners."""
    emitter = EventEmitter()
    results = []
    
    async def listener1(data):
        results.append(f"listener1:{data}")
    
    async def listener2(data):
        results.append(f"listener2:{data}")
    
    emitter.on("test", listener1)
    emitter.on("test", listener2)
    
    await emitter.emit("test", "data")
    
    assert len(results) == 2
    assert "listener1:data" in results
    assert "listener2:data" in results


@pytest.mark.asyncio
async def test_event_emitter_off_all():
    """Test removing all listeners with remove_all_listeners()."""
    emitter = EventEmitter()
    
    async def listener1(data):
        pass
    
    async def listener2(data):
        pass
    
    emitter.on("test", listener1)
    emitter.on("test", listener2)
    
    emitter.remove_all_listeners("test")
    
    assert emitter.listener_count("test") == 0

