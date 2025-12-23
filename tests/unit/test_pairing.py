"""Tests for Pairing controller."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from walletkit.controllers.pairing import Pairing, calc_expiry
from walletkit.core import Core
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
async def core():
    """Create and initialize core instance."""
    storage = MemoryStorage()
    core = Core(storage=storage)
    await core.start()
    
    # Mock relayer to avoid actual network connections
    core.relayer.connect = AsyncMock()
    core.relayer.subscribe = AsyncMock(return_value="sub_id_123")
    core.relayer.unsubscribe = AsyncMock()
    core.relayer._connected = False
    
    return core


@pytest.fixture
async def pairing(core):
    """Create and initialize pairing controller."""
    pairing = Pairing(core, core.logger)
    await pairing.init()
    return pairing


@pytest.mark.asyncio
async def test_pairing_init(pairing):
    """Test pairing initialization."""
    assert pairing._initialized is True


@pytest.mark.asyncio
async def test_pairing_create(pairing):
    """Test pairing creation."""
    result = await pairing.create()
    assert "topic" in result
    assert "uri" in result
    assert result["topic"] in pairing.pairings
    assert result["uri"].startswith("wc:")


@pytest.mark.asyncio
async def test_pairing_get(pairing):
    """Test getting a pairing."""
    result = await pairing.create()
    topic = result["topic"]
    
    pairing_obj = pairing.get(topic)
    assert pairing_obj is not None
    assert pairing_obj["topic"] == topic


@pytest.mark.asyncio
async def test_pairing_activate(pairing):
    """Test activating a pairing."""
    result = await pairing.create()
    topic = result["topic"]
    
    await pairing.activate(topic)
    pairing_obj = pairing.get(topic)
    assert pairing_obj["active"] is True


@pytest.mark.asyncio
async def test_calc_expiry():
    """Test expiry calculation."""
    ttl = 5000  # 5 seconds
    expiry = calc_expiry(ttl)
    assert expiry > 0
    assert expiry > int(__import__("time").time() * 1000)


@pytest.mark.asyncio
async def test_pairing_create_with_params(pairing):
    """Test pairing creation with parameters."""
    result = await pairing.create({
        "methods": ["eth_sendTransaction"],
        "transportType": "ws",
    })
    
    assert "topic" in result
    assert "uri" in result
    pairing_obj = pairing.get(result["topic"])
    assert pairing_obj["methods"] == ["eth_sendTransaction"]


@pytest.mark.asyncio
async def test_pairing_pair(pairing):
    """Test pairing with URI."""
    # Create a pairing first to get a valid URI
    created = await pairing.create()
    uri = created["uri"]
    
    # Create a new pairing instance and pair with the URI
    pairing2 = Pairing(pairing.core, pairing.core.logger)
    await pairing2.init()
    
    await pairing2.pair({"uri": uri})
    
    # Should have the pairing
    topic = created["topic"]
    pairing_obj = pairing2.get(topic)
    assert pairing_obj is not None
    assert pairing_obj["topic"] == topic


@pytest.mark.asyncio
async def test_pairing_pair_missing_uri(pairing):
    """Test pair with missing URI."""
    with pytest.raises(ValueError, match="URI is required"):
        await pairing.pair({})


@pytest.mark.asyncio
async def test_pairing_pair_already_active(pairing):
    """Test pair when pairing already exists and is active."""
    result = await pairing.create()
    topic = result["topic"]
    await pairing.activate(topic)
    
    uri = result["uri"]
    with pytest.raises(ValueError, match="Pairing already exists"):
        await pairing.pair({"uri": uri})


@pytest.mark.asyncio
async def test_pairing_get_nonexistent(pairing):
    """Test getting nonexistent pairing."""
    result = pairing.get("nonexistent_topic")
    assert result is None


@pytest.mark.asyncio
async def test_pairing_activate_nonexistent(pairing):
    """Test activating nonexistent pairing."""
    with pytest.raises(ValueError, match="Pairing not found"):
        await pairing.activate("nonexistent_topic")


@pytest.mark.asyncio
async def test_pairing_delete(pairing):
    """Test deleting a pairing."""
    result = await pairing.create()
    topic = result["topic"]
    
    assert topic in pairing.pairings
    
    await pairing.delete(topic)
    
    assert topic not in pairing.pairings


@pytest.mark.asyncio
async def test_pairing_delete_nonexistent(pairing):
    """Test deleting nonexistent pairing."""
    # Should not raise error
    await pairing.delete("nonexistent_topic")


@pytest.mark.asyncio
async def test_pairing_check_initialized(core):
    """Test _check_initialized raises error when not initialized."""
    pairing = Pairing(core, core.logger)
    
    with pytest.raises(RuntimeError, match="not initialized"):
        await pairing.create()
    
    with pytest.raises(RuntimeError, match="not initialized"):
        pairing.get("topic")
    
    with pytest.raises(RuntimeError, match="not initialized"):
        await pairing.activate("topic")
    
    with pytest.raises(RuntimeError, match="not initialized"):
        await pairing.delete("topic")


@pytest.mark.asyncio
async def test_pairing_expirer_event_handling(pairing):
    """Test expirer event handling."""
    result = await pairing.create()
    topic = result["topic"]
    
    # Manually trigger expiry
    from walletkit.controllers.expirer import EXPIRER_EVENTS
    
    # Emit expired event
    await pairing.core.expirer.events.emit(EXPIRER_EVENTS["expired"], {
        "target": f"topic:{topic}",
    })
    
    # Give time for async processing
    import asyncio
    await asyncio.sleep(0.1)
    
    # Pairing should be deleted
    assert topic not in pairing.pairings


@pytest.mark.asyncio
async def test_pairing_expirer_event_error_handling(pairing):
    """Test expirer event error handling."""
    # Create pairing
    result = await pairing.create()
    topic = result["topic"]
    
    # Emit expired event with invalid target
    from walletkit.controllers.expirer import EXPIRER_EVENTS
    
    await pairing.core.expirer.events.emit(EXPIRER_EVENTS["expired"], {
        "target": "invalid_target",
    })
    
    # Should handle error gracefully
    import asyncio
    await asyncio.sleep(0.1)
    
    # Pairing should still exist (error was handled)
    assert topic in pairing.pairings


@pytest.mark.asyncio
async def test_pairing_init_idempotent(pairing):
    """Test init is idempotent."""
    initial_pairings = len(pairing.pairings)
    
    # Call init again
    await pairing.init()
    
    # Should not duplicate
    assert len(pairing.pairings) == initial_pairings
