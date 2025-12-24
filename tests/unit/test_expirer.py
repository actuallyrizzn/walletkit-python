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
    expiry = int(time.time()) + 10  # 10 seconds from now
    
    expirer.set("topic1", expiry)
    assert expirer.length == 1
    assert expirer.has("topic1")
    
    expiration = expirer.get("topic1")
    assert expiration.target == "topic:topic1"
    assert expiration.expiry == expiry


@pytest.mark.asyncio
async def test_expirer_delete(expirer):
    """Test deleting expirations."""
    expiry = int(time.time()) + 10
    
    expirer.set("topic1", expiry)
    assert expirer.length == 1
    
    expirer.delete("topic1")
    assert expirer.length == 0
    assert not expirer.has("topic1")


@pytest.mark.asyncio
async def test_expirer_expiry(expirer):
    """Test expiration expiry."""
    # Set expiration in the past
    expiry = int(time.time()) - 1  # 1 second ago
    
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
    
    expiry = int(time.time()) + 10
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


def test_format_target_unknown_type():
    """Test format_target with unknown type."""
    with pytest.raises(ValueError, match="Unknown target type"):
        format_target(123.45)  # Float is not supported


def test_parse_expirer_target_invalid_format():
    """Test parse_expirer_target with invalid format."""
    with pytest.raises(ValueError, match="Invalid target format"):
        parse_expirer_target("invalid")


def test_parse_expirer_target_unknown_type():
    """Test parse_expirer_target with unknown type."""
    with pytest.raises(ValueError, match="Unknown target type"):
        parse_expirer_target("unknown:value")


@pytest.mark.asyncio
async def test_expirer_get_nonexistent(expirer):
    """Test getting nonexistent expiration."""
    with pytest.raises(KeyError, match="No expiration found"):
        expirer.get("nonexistent")


@pytest.mark.asyncio
async def test_expirer_has_with_exception(expirer):
    """Test has() method with exception handling."""
    # Test with invalid key type that raises exception
    result = expirer.has(123.45)  # Float should cause exception in format_target
    assert result is False  # Should return False on exception


@pytest.mark.asyncio
async def test_expirer_values_property(expirer):
    """Test values property."""
    expiry = int(time.time()) + 10
    expirer.set("topic1", expiry)
    expirer.set("topic2", expiry)
    
    values = expirer.values
    assert len(values) == 2
    assert all(isinstance(v, type(expirer.get("topic1"))) for v in values)


@pytest.mark.asyncio
async def test_expirer_event_listeners(expirer):
    """Test event listener methods."""
    listener = lambda x: None
    
    expirer.on("test_event", listener)
    expirer.once("test_event", listener)
    expirer.off("test_event", listener)
    expirer.remove_listener("test_event", listener)


@pytest.mark.asyncio
async def test_expirer_check_loop_error_handling(storage, logger):
    """Test _check_loop error handling."""
    exp = Expirer(storage, logger)
    await exp.init()
    
    # Mock _check_expirations to raise an exception
    original_check = exp._check_expirations
    call_count = 0
    
    def mock_check():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Test error")
        return original_check()
    
    exp._check_expirations = mock_check
    
    # Wait for check loop to run
    await asyncio.sleep(0.2)
    
    await exp.cleanup()


@pytest.mark.asyncio
async def test_expirer_restore_with_non_list(storage, logger):
    """Test _restore with non-list data."""
    # Store non-list data
    await storage.set_item("wc@2:expirer:core:", {"not": "a list"})
    
    exp = Expirer(storage, logger)
    await exp.init()
    
    # Should handle gracefully
    assert exp.length == 0
    await exp.cleanup()


@pytest.mark.asyncio
async def test_expirer_restore_with_empty_list(storage, logger):
    """Test _restore with empty list."""
    await storage.set_item("wc@2:expirer:core:", [])
    
    exp = Expirer(storage, logger)
    await exp.init()
    
    assert exp.length == 0
    await exp.cleanup()


@pytest.mark.asyncio
async def test_expirer_restore_with_existing_data(storage, logger):
    """Test _restore when expirations already exist."""
    from walletkit.controllers.expirer import Expiration
    
    exp1 = Expirer(storage, logger)
    await exp1.init()
    
    expiry = int(time.time()) + 10
    exp1.set("topic1", expiry)
    await asyncio.sleep(0.2)  # Wait for persistence
    
    await exp1.cleanup()
    
    # Try to restore when data already exists - need to manually set expirations
    # to simulate the condition where expirations exist before restore
    exp2 = Expirer(storage, logger)
    
    # Verify storage key matches
    assert exp2.storage_key == exp1.storage_key
    
    # Manually set an expiration before calling _restore to trigger the error
    exp2.expirations["topic:test"] = Expiration("topic:test", expiry)
    
    # Verify expirations dict is not empty
    assert len(exp2.expirations) > 0
    assert bool(exp2.expirations) is True
    
    # Storage should have persisted data from exp1
    persisted = await storage.get_item(exp2.storage_key)
    assert persisted is not None
    assert len(persisted) > 0
    assert isinstance(persisted, list)
    
    # Now call _restore directly - it should detect existing expirations
    # and raise RuntimeError because persisted data exists AND expirations exist
    with pytest.raises(RuntimeError, match="Restore would override existing data"):
        await exp2._restore()


@pytest.mark.asyncio
async def test_expirer_restore_exception_handling(storage, logger):
    """Test _restore exception handling."""
    # Create a storage that raises exception
    from walletkit.utils.storage import IKeyValueStorage
    
    class FailingStorage(IKeyValueStorage):
        async def get_item(self, key):
            raise Exception("Storage error")
        
        async def set_item(self, key, value):
            pass
        
        async def remove_item(self, key):
            pass
        
        async def get_keys(self):
            return []
    
    failing_storage = FailingStorage()
    exp = Expirer(failing_storage, logger)
    
    # Should handle exception gracefully
    await exp.init()
    assert exp.length == 0
    await exp.cleanup()


@pytest.mark.asyncio
async def test_expirer_check_initialized(storage, logger):
    """Test _check_initialized raises error when not initialized."""
    exp = Expirer(storage, logger)
    
    with pytest.raises(RuntimeError, match="not initialized"):
        exp.get("topic1")


@pytest.mark.asyncio
async def test_expirer_cleanup(expirer):
    """Test cleanup method."""
    # Should not raise error
    await expirer.cleanup()
    
    # Should be safe to call multiple times
    await expirer.cleanup()


@pytest.mark.asyncio
async def test_expirer_init_idempotent(expirer):
    """Test init is idempotent."""
    initial_length = expirer.length
    
    # Call init again
    await expirer.init()
    
    # Should not duplicate
    assert expirer.length == initial_length