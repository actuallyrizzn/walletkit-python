"""Tests for Engine controller."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from walletkit.controllers.engine import Engine
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
def mock_client(core):
    """Create mock WalletKit client."""
    class MockClient:
        def __init__(self):
            self.core = core
            self.metadata = {"name": "Test Wallet", "description": "Test"}
            self.sign_config = None
            self.logger = core.logger
            self.events = MagicMock()
    
    return MockClient()


@pytest.fixture
async def engine(mock_client):
    """Create and initialize engine."""
    engine = Engine(mock_client)
    await engine.init()
    return engine


@pytest.mark.asyncio
async def test_engine_init(engine):
    """Test engine initialization."""
    assert engine.sign_client is not None
    assert engine.sign_client._initialized is True


@pytest.mark.asyncio
async def test_engine_pair(engine, mock_client):
    """Test pairing."""
    # Mock pairing.pair
    mock_client.core.pairing.pair = AsyncMock()
    
    await engine.pair("wc:test@2?relay-protocol=irn&symKey=test")
    
    mock_client.core.pairing.pair.assert_called_once()


@pytest.mark.asyncio
async def test_engine_get_active_sessions(engine):
    """Test getting active sessions."""
    sessions = engine.get_active_sessions()
    assert isinstance(sessions, dict)


@pytest.mark.asyncio
async def test_engine_get_pending_proposals(engine):
    """Test getting pending proposals."""
    proposals = engine.get_pending_session_proposals()
    assert isinstance(proposals, dict)


@pytest.mark.asyncio
async def test_engine_get_pending_requests(engine):
    """Test getting pending requests."""
    requests = engine.get_pending_session_requests()
    assert isinstance(requests, list)

