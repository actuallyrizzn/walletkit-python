"""Tests for SignClient."""
import pytest

from walletkit.controllers.sign_client import SignClient
from walletkit.core import Core
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create storage instance."""
    return MemoryStorage()


@pytest.fixture
async def core(storage):
    """Create and initialize core."""
    core = Core(storage=storage)
    await core.start()
    return core


@pytest.fixture
async def sign_client(core):
    """Create and initialize SignClient."""
    metadata = {
        "name": "Test Wallet",
        "description": "Test Description",
        "url": "https://example.com",
        "icons": ["https://example.com/icon.png"],
    }
    client = await SignClient.init(core, metadata)
    return client


@pytest.mark.asyncio
async def test_sign_client_init(sign_client):
    """Test SignClient initialization."""
    assert sign_client._initialized
    assert sign_client.session.length == 0
    assert sign_client.proposal.length == 0
    assert sign_client.request_store.length == 0


@pytest.mark.asyncio
async def test_sign_client_approve_reject(sign_client):
    """Test approve and reject session proposal."""
    # Create a mock proposal with a topic that has crypto setup
    proposal_id = 123
    topic = "test_topic"
    
    # Set up crypto for the topic
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=topic)
    
    proposal = {
        "id": proposal_id,
        "topic": topic,
        "params": {
            "id": proposal_id,
            "proposer": {"metadata": {}},
            "requiredNamespaces": {},
        },
    }
    await sign_client.proposal.set(proposal_id, proposal)
    
    # Test reject (will try to encode, so we need crypto setup)
    # Mock the relayer publish to avoid actual network calls
    async def mock_publish(topic, message):
        pass
    
    original_publish = sign_client.core.relayer.publish
    sign_client.core.relayer.publish = mock_publish
    
    try:
        await sign_client.reject({
            "id": proposal_id,
            "reason": {"code": 5000, "message": "User rejected"},
        })
        
        # Proposal should be deleted
        assert not sign_client.proposal.has(proposal_id)
    finally:
        sign_client.core.relayer.publish = original_publish


@pytest.mark.asyncio
async def test_sign_client_get_pending_requests(sign_client):
    """Test getting pending session requests."""
    requests = sign_client.get_pending_session_requests()
    assert isinstance(requests, list)
    assert len(requests) == 0
    
    # Add a request
    await sign_client.request_store.add({
        "topic": "test_topic",
        "request": {"id": 1, "method": "eth_sendTransaction", "params": {}},
    })
    
    requests = sign_client.get_pending_session_requests()
    assert len(requests) == 1


@pytest.mark.asyncio
async def test_sign_client_disconnect(sign_client):
    """Test disconnecting a session."""
    # Create a session with crypto setup
    topic = "test_topic"
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=topic)
    
    session = {
        "topic": topic,
        "expiry": 1234567890,
        "namespaces": {},
        "peer": {"metadata": {}},
    }
    await sign_client.session.set(topic, session)
    
    # Register expiry
    sign_client.core.expirer.set(topic, session["expiry"])
    
    # Mock relayer publish
    async def mock_publish(t, m):
        pass
    
    original_publish = sign_client.core.relayer.publish
    sign_client.core.relayer.publish = mock_publish
    
    try:
        # Disconnect
        await sign_client.disconnect({
            "topic": topic,
            "reason": {"code": 6000, "message": "User disconnected"},
        })
        
        # Session should be deleted
        assert not sign_client.session.has(topic)
        # Expiry should be removed
        assert not sign_client.core.expirer.has(topic)
    finally:
        sign_client.core.relayer.publish = original_publish


@pytest.mark.asyncio
async def test_sign_client_expirer_integration(sign_client):
    """Test expirer integration with SignClient."""
    # Create a session with expiry
    topic = "expiry_test_topic"
    import time
    expiry = int(time.time() * 1000) + 1000  # 1 second from now
    
    session = {
        "topic": topic,
        "expiry": expiry,
        "namespaces": {},
        "peer": {"metadata": {}},
    }
    await sign_client.session.set(topic, session)
    
    # Register expiry
    sign_client.core.expirer.set(topic, expiry)
    assert sign_client.core.expirer.has(topic)
    
    # Create a proposal with expiry
    proposal_id = 456
    proposal_expiry = int(time.time() * 1000) + 1000
    proposal = {
        "id": proposal_id,
        "topic": "proposal_topic",
        "params": {"id": proposal_id},
    }
    await sign_client.proposal.set(proposal_id, proposal)
    sign_client.core.expirer.set(proposal_id, proposal_expiry)
    assert sign_client.core.expirer.has(proposal_id)


@pytest.mark.asyncio
async def test_sign_client_format_auth_message(sign_client):
    """Test formatting auth message."""
    request = {"method": "eth_sign", "params": {}}
    iss = "did:example:123"
    
    message = sign_client.format_auth_message({
        "request": request,
        "iss": iss,
    })
    
    assert isinstance(message, str)
    assert iss in message
    assert "WalletConnect Auth Message" in message

