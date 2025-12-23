"""Tests for Expirer controller."""
import asyncio
import time

import pytest

from walletkit.controllers.expirer import (
    Expirer,
    format_id_target,
    format_target,
    format_topic_target,
    parse_expirer_target,
)


@pytest.fixture
def storage():
    """Create storage instance."""
    from walletkit.utils.storage import MemoryStorage
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
async def expirer(storage, logger):
    """Create and initialize expirer."""
    exp = Expirer(storage, logger)
    await exp.init()
    yield exp
    await exp.cleanup()


def test_format_target():
    """Test target formatting."""
    assert format_topic_target("abc123") == "topic:abc123"
    assert format_id_target(42) == "id:42"
    assert format_target("topic1") == "topic:topic1"
    assert format_target(123) == "id:123"


def test_parse_expirer_target():
    """Test target parsing."""
    parsed = parse_expirer_target("topic:abc123")
    assert parsed["type"] == "topic"
    assert parsed["value"] == "abc123"
    
    parsed = parse_expirer_target("id:42")
    assert parsed["type"] == "id"
    assert parsed["value"] == 42


@pytest.mark.asyncio
async def test_expirer_init(expirer):
    """Test expirer initialization."""
    assert expirer.length == 0
    assert expirer._initialized


@pytest.mark.asyncio
async def test_expirer_set_get(expirer):
    """Test setting and getting expirations."""
    expiry = int(time.time() * 1000) + 10000  # 10 seconds from now
    
    expirer.set("topic1", expiry)
    assert expirer.length == 1
    assert expirer.has("topic1")
    
    expiration = expirer.get("topic1")
    assert expiration.target == "topic:topic1"
    assert expiration.expiry == expiry


@pytest.mark.asyncio
async def test_expirer_delete(expirer):
    """Test deleting expirations."""
    expiry = int(time.time() * 1000) + 10000
    
    expirer.set("topic1", expiry)
    assert expirer.length == 1
    
    expirer.delete("topic1")
    assert expirer.length == 0
    assert not expirer.has("topic1")


@pytest.mark.asyncio
async def test_expirer_expiry(expirer):
    """Test expiration expiry."""
    # Set expiration in the past
    expiry = int(time.time() * 1000) - 1000  # 1 second ago
    
    expired_event = None
    event_received = asyncio.Event()
    
    async def on_expired(event: dict) -> None:
        nonlocal expired_event
        expired_event = event
        event_received.set()
    
    expirer.on("expirer_expired", on_expired)
    
    expirer.set("topic1", expiry)
    
    # Wait for check loop to run and event to be received
    try:
        await asyncio.wait_for(event_received.wait(), timeout=2.0)
    except asyncio.TimeoutError:
        pass  # Event might have been processed already
    
    # Give a bit more time for async operations
    await asyncio.sleep(0.5)
    
    assert expired_event is not None
    assert expired_event["target"] == "topic:topic1"
    assert expirer.length == 0


@pytest.mark.asyncio
async def test_expirer_persistence(storage, logger):
    """Test expirer persistence."""
    exp1 = Expirer(storage, logger)
    await exp1.init()
    
    expiry = int(time.time() * 1000) + 10000
    exp1.set("topic1", expiry)
    exp1.set(42, expiry)
    
    # Wait for persistence to complete
    await asyncio.sleep(0.5)
    
    await exp1.cleanup()
    
    # Create new expirer and restore
    exp2 = Expirer(storage, logger)
    await exp2.init()
    
    assert exp2.length == 2
    assert exp2.has("topic1")
    assert exp2.has(42)
    
    await exp2.cleanup()

