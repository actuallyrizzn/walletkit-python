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

