"""Comprehensive tests for EventEmitter."""
import pytest

from walletkit.utils.events import EventEmitter


@pytest.mark.asyncio
async def test_event_emitter_once_listener():
    """Test one-time event listeners."""
    emitter = EventEmitter()
    call_count = 0
    
    async def listener(data):
        nonlocal call_count
        call_count += 1
    
    emitter.once("test", listener)
    
    await emitter.emit("test", "data1")
    assert call_count == 1
    
    # Should not be called again
    await emitter.emit("test", "data2")
    assert call_count == 1  # Still 1, not 2


@pytest.mark.asyncio
async def test_event_emitter_emit_no_listeners():
    """Test emitting with no listeners."""
    emitter = EventEmitter()
    
    # Should not raise error
    result = await emitter.emit("nonexistent", "data")
    assert result is False  # No listeners were called


@pytest.mark.asyncio
async def test_event_emitter_emit_with_args():
    """Test emitting with positional and keyword arguments."""
    emitter = EventEmitter()
    received_args = []
    received_kwargs = {}
    
    async def listener(*args, **kwargs):
        received_args.extend(args)
        received_kwargs.update(kwargs)
    
    emitter.on("test", listener)
    
    await emitter.emit("test", "arg1", "arg2", key1="value1", key2="value2")
    
    assert len(received_args) == 2
    assert received_args[0] == "arg1"
    assert received_args[1] == "arg2"
    assert received_kwargs["key1"] == "value1"
    assert received_kwargs["key2"] == "value2"


@pytest.mark.asyncio
async def test_event_emitter_sync_listener():
    """Test that sync listeners also work."""
    emitter = EventEmitter()
    call_count = 0
    
    def sync_listener(data):
        nonlocal call_count
        call_count += 1
    
    emitter.on("test", sync_listener)
    
    await emitter.emit("test", "data")
    assert call_count == 1


@pytest.mark.asyncio
async def test_event_emitter_remove_all_listeners_no_event():
    """Test removing all listeners when no event specified."""
    emitter = EventEmitter()
    
    async def listener1(data):
        pass
    
    async def listener2(data):
        pass
    
    emitter.on("event1", listener1)
    emitter.on("event2", listener2)
    
    emitter.remove_all_listeners()
    
    assert emitter.listener_count("event1") == 0
    assert emitter.listener_count("event2") == 0


@pytest.mark.asyncio
async def test_event_emitter_remove_all_listeners_specific_event():
    """Test removing all listeners for a specific event."""
    emitter = EventEmitter()
    
    async def listener1(data):
        pass
    
    async def listener2(data):
        pass
    
    emitter.on("event1", listener1)
    emitter.on("event1", listener2)
    emitter.on("event2", listener1)
    
    emitter.remove_all_listeners("event1")
    
    assert emitter.listener_count("event1") == 0
    assert emitter.listener_count("event2") == 1  # Should still have listener


@pytest.mark.asyncio
async def test_event_emitter_sync_listener_in_once():
    """Test sync listener in once listeners."""
    emitter = EventEmitter()
    call_count = 0
    
    def sync_listener(data):
        nonlocal call_count
        call_count += 1
    
    emitter.once("test", sync_listener)
    
    await emitter.emit("test", "data")
    assert call_count == 1
    
    # Should not be called again
    await emitter.emit("test", "data")
    assert call_count == 1
