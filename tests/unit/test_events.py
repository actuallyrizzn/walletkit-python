"""Tests for EventEmitter."""
import pytest

from walletkit.utils.events import EventEmitter


@pytest.mark.asyncio
async def test_event_emitter_on_emit():
    """Test basic event on and emit."""
    emitter = EventEmitter()
    called = False

    def listener():
        nonlocal called
        called = True

    emitter.on("test", listener)
    await emitter.emit("test")
    assert called is True


@pytest.mark.asyncio
async def test_event_emitter_async_listener():
    """Test async listener."""
    emitter = EventEmitter()
    called = False

    async def async_listener():
        nonlocal called
        called = True

    emitter.on("test", async_listener)
    await emitter.emit("test")
    assert called is True


@pytest.mark.asyncio
async def test_event_emitter_once():
    """Test one-time listener."""
    emitter = EventEmitter()
    call_count = 0

    def listener():
        nonlocal call_count
        call_count += 1

    emitter.once("test", listener)
    await emitter.emit("test")
    await emitter.emit("test")
    assert call_count == 1


@pytest.mark.asyncio
async def test_event_emitter_off():
    """Test removing listener."""
    emitter = EventEmitter()
    called = False

    def listener():
        nonlocal called
        called = True

    emitter.on("test", listener)
    emitter.off("test", listener)
    await emitter.emit("test")
    assert called is False


@pytest.mark.asyncio
async def test_event_emitter_with_args():
    """Test event with arguments."""
    emitter = EventEmitter()
    received_args = None

    def listener(*args, **kwargs):
        nonlocal received_args
        received_args = (args, kwargs)

    emitter.on("test", listener)
    await emitter.emit("test", "arg1", "arg2", key="value")
    assert received_args == (("arg1", "arg2"), {"key": "value"})

