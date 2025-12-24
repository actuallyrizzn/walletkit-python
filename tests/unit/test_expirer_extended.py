"""Extended tests for Expirer."""
import pytest
import asyncio

from walletkit.controllers.expirer import Expirer, EXPIRER_EVENTS, parse_expirer_target


@pytest.fixture
async def expirer(storage, logger):
    """Create and initialize Expirer."""
    exp = Expirer(storage, logger)
    await exp.init()
    return exp


@pytest.mark.asyncio
async def test_expirer_set_get(expirer):
    """Test setting and getting expirations."""
    import time
    expiry = int(time.time()) + 1
    
    expirer.set("test_target", expiry)
    
    assert expirer.has("test_target")
    expiration = expirer.get("test_target")
    assert expiration.expiry == expiry
    assert expiration.target == "topic:test_target"  # Expirer formats targets


@pytest.mark.asyncio
async def test_expirer_delete(expirer):
    """Test deleting expirations."""
    import time
    expiry = int(time.time()) + 1
    
    expirer.set("test_target", expiry)
    assert expirer.has("test_target")
    
    expirer.delete("test_target")
    assert not expirer.has("test_target")


@pytest.mark.asyncio
async def test_expirer_length(expirer):
    """Test expirer length property."""
    import time
    expiry = int(time.time()) + 1
    
    assert expirer.length == 0
    
    expirer.set("target1", expiry)
    assert expirer.length == 1
    
    expirer.set("target2", expiry)
    assert expirer.length == 2
    
    expirer.delete("target1")
    assert expirer.length == 1


@pytest.mark.asyncio
async def test_parse_expirer_target():
    """Test parsing expirer target strings."""
    # Topic target
    parsed = parse_expirer_target("topic:test_topic")
    assert parsed["type"] == "topic"
    assert parsed["value"] == "test_topic"
    
    # ID target
    parsed = parse_expirer_target("id:123")
    assert parsed["type"] == "id"
    assert parsed["value"] == 123
    
    # Invalid format should raise ValueError
    with pytest.raises(ValueError):
        parse_expirer_target("invalid")


@pytest.mark.asyncio
async def test_expirer_get_all(expirer):
    """Test getting all expirations via keys."""
    import time
    expiry1 = int(time.time()) + 1
    expiry2 = int(time.time()) + 2
    
    expirer.set("target1", expiry1)
    expirer.set("target2", expiry2)
    
    # Get all via keys property (formatted as "topic:target1")
    keys = expirer.keys
    assert len(keys) == 2
    assert "topic:target1" in keys
    assert "topic:target2" in keys

