"""Tests for WalletKit client."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from walletkit.client import WalletKit
from walletkit.core import Core
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
async def core():
    """Create and initialize core instance."""
    storage = MemoryStorage()
    core = Core(storage=storage)
    await core.start()
    return core


@pytest.fixture
async def client(core):
    """Create and initialize WalletKit client."""
    opts = {
        "core": core,
        "metadata": {
            "name": "Test Wallet",
            "description": "Test Wallet Description",
            "url": "https://test.wallet",
            "icons": ["https://test.wallet/icon.png"],
        },
    }
    client = await WalletKit.init(opts)
    return client


@pytest.mark.asyncio
async def test_client_init(client):
    """Test client initialization."""
    assert client._initialized is True
    assert client.engine is not None
    assert client.engine.sign_client is not None


@pytest.mark.asyncio
async def test_client_get_active_sessions(client):
    """Test getting active sessions."""
    sessions = client.get_active_sessions()
    assert isinstance(sessions, dict)


@pytest.mark.asyncio
async def test_client_get_pending_proposals(client):
    """Test getting pending proposals."""
    proposals = client.get_pending_session_proposals()
    assert isinstance(proposals, dict)


@pytest.mark.asyncio
async def test_client_get_pending_requests(client):
    """Test getting pending requests."""
    requests = client.get_pending_session_requests()
    assert isinstance(requests, list)


@pytest.mark.asyncio
async def test_client_pair(client):
    """Test pairing."""
    # Mock engine.pair
    client.engine.pair = AsyncMock()
    
    await client.pair("wc:test@2?relay-protocol=irn&symKey=test")
    
    client.engine.pair.assert_called_once()


@pytest.mark.asyncio
async def test_client_events(client):
    """Test event handling."""
    listener = MagicMock()
    
    client.on("session_proposal", listener)
    client.off("session_proposal", listener)
    client.once("session_proposal", listener)
    client.remove_listener("session_proposal", listener)

