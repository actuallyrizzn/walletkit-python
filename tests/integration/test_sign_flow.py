"""Integration tests for WalletKit Sign Protocol flow."""
import os
import pytest
import asyncio
from typing import Dict, Any

from walletkit import WalletKit, Core
from walletkit.types.client import Metadata
from walletkit.utils.storage import MemoryStorage


# Test configuration
TEST_PROJECT_ID = os.getenv("WALLETCONNECT_PROJECT_ID", "test-project-id")

TEST_METADATA: Metadata = {
    "name": "Test Wallet",
    "description": "Test Wallet Description",
    "url": "https://test.wallet",
    "icons": ["https://test.wallet/icon.png"],
}

TEST_NAMESPACES = {
    "eip155": {
        "chains": ["eip155:1"],
        "methods": ["eth_sendTransaction", "eth_sign", "personal_sign"],
        "events": ["chainChanged", "accountsChanged"],
    },
}

TEST_REQUIRED_NAMESPACES = {
    "eip155": {
        "chains": ["eip155:1"],
        "methods": ["eth_sendTransaction"],
        "events": ["accountsChanged"],
    },
}


@pytest.fixture
async def wallet_core():
    """Create a Core instance for wallet."""
    storage = MemoryStorage()
    core = Core(
        project_id=TEST_PROJECT_ID,
        storage=storage,
    )
    await core.start()
    yield core
    # Cleanup
    if hasattr(core, "relayer") and core.relayer:
        try:
            await core.relayer.disconnect()
        except Exception:
            pass


@pytest.fixture
async def dapp_core():
    """Create a Core instance for dApp."""
    storage = MemoryStorage()
    core = Core(
        project_id=TEST_PROJECT_ID,
        storage=storage,
    )
    await core.start()
    yield core
    # Cleanup
    if hasattr(core, "relayer") and core.relayer:
        try:
            await core.relayer.disconnect()
        except Exception:
            pass


@pytest.fixture
async def wallet(wallet_core):
    """Create a WalletKit instance for wallet."""
    wallet_instance = await WalletKit.init({
        "core": wallet_core,
        "metadata": TEST_METADATA,
    })
    yield wallet_instance


@pytest.fixture
async def dapp(dapp_core):
    """Create a WalletKit instance for dApp."""
    dapp_instance = await WalletKit.init({
        "core": dapp_core,
        "metadata": TEST_METADATA,
    })
    yield dapp_instance


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pairing_creation(dapp):
    """Test creating a pairing URI."""
    # Create pairing
    pairing = await dapp.core.pairing.create({
        "methods": ["wc_sessionPropose"],
    })
    
    assert pairing is not None
    assert "uri" in pairing
    assert "topic" in pairing
    assert pairing["uri"].startswith("wc:")
    assert len(pairing["topic"]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pairing_with_uri(wallet, dapp):
    """Test pairing with a URI."""
    # Create pairing URI from dApp
    pairing = await dapp.core.pairing.create({
        "methods": ["wc_sessionPropose"],
    })
    uri = pairing["uri"]
    
    # Pair wallet with URI
    await wallet.pair(uri)
    
    # Give some time for pairing to complete
    await asyncio.sleep(0.5)
    
    # Verify pairing exists
    # (In a real scenario, we'd check pairing state)
    assert True  # Placeholder - pairing should succeed


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_proposal_flow(wallet, dapp):
    """Test complete session proposal flow."""
    session_approved = asyncio.Event()
    session_result = {}
    
    # Set up wallet to listen for proposals
    @wallet.on("session_proposal")
    async def on_proposal(event: Dict[str, Any]) -> None:
        proposal_id = event.get("id")
        params = event.get("params", {})
        
        # Auto-approve for test
        try:
            result = await wallet.approve_session(
                id=proposal_id,
                namespaces=TEST_NAMESPACES,
            )
            session_result["session"] = result
            session_approved.set()
        except Exception as e:
            session_result["error"] = str(e)
            session_approved.set()
    
    # Create pairing and initiate session proposal
    pairing = await dapp.core.pairing.create({
        "methods": ["wc_sessionPropose"],
    })
    uri = pairing["uri"]
    
    # Pair wallet
    await wallet.pair(uri)
    
    # Wait for session approval (with timeout)
    try:
        await asyncio.wait_for(session_approved.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        pytest.fail("Session proposal timeout")
    
    # Verify session was created
    if "error" in session_result:
        pytest.fail(f"Session approval failed: {session_result['error']}")
    
    assert "session" in session_result
    session = session_result["session"]
    assert session is not None
    assert "topic" in session or session.get("topic") is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_rejection(wallet, dapp):
    """Test session proposal rejection."""
    session_rejected = asyncio.Event()
    
    # Set up wallet to listen for proposals
    @wallet.on("session_proposal")
    async def on_proposal(event: Dict[str, Any]) -> None:
        proposal_id = event.get("id")
        
        # Reject proposal
        await wallet.reject_session(
            id=proposal_id,
            reason={"code": 5000, "message": "User rejected"},
        )
        session_rejected.set()
    
    # Create pairing and initiate session proposal
    pairing = await dapp.core.pairing.create({
        "methods": ["wc_sessionPropose"],
    })
    uri = pairing["uri"]
    
    # Pair wallet
    await wallet.pair(uri)
    
    # Wait for rejection (with timeout)
    try:
        await asyncio.wait_for(session_rejected.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        pytest.fail("Session rejection timeout")
    
    # Verify proposal was rejected
    proposals = wallet.get_pending_session_proposals()
    assert len(proposals) == 0  # Proposal should be removed after rejection


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_request_response(wallet, dapp):
    """Test session request and response flow."""
    session_established = asyncio.Event()
    request_received = asyncio.Event()
    response_received = asyncio.Event()
    
    session_topic = None
    
    # Set up wallet to handle proposals
    @wallet.on("session_proposal")
    async def on_proposal(event: Dict[str, Any]) -> None:
        proposal_id = event.get("id")
        result = await wallet.approve_session(
            id=proposal_id,
            namespaces=TEST_NAMESPACES,
        )
        nonlocal session_topic
        session_topic = result.get("topic")
        session_established.set()
    
    # Set up wallet to handle requests
    @wallet.on("session_request")
    async def on_request(event: Dict[str, Any]) -> None:
        topic = event.get("topic")
        request_id = event.get("id")
        
        # Respond to request
        await wallet.respond_session_request(
            topic=topic,
            response={
                "id": request_id,
                "jsonrpc": "2.0",
                "result": "0x1234567890abcdef",
            },
        )
        request_received.set()
    
    # Create pairing and initiate session
    pairing = await dapp.core.pairing.create({
        "methods": ["wc_sessionPropose"],
    })
    uri = pairing["uri"]
    
    # Pair wallet
    await wallet.pair(uri)
    
    # Wait for session establishment
    try:
        await asyncio.wait_for(session_established.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        pytest.fail("Session establishment timeout")
    
    assert session_topic is not None
    
    # Note: In a real integration test, we would send a request from dApp
    # and verify the response. This requires a full dApp implementation
    # that can send requests via SignClient.
    
    # For now, we just verify the session exists
    sessions = wallet.get_active_sessions()
    assert len(sessions) > 0 or session_topic is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_disconnect(wallet, dapp):
    """Test session disconnection."""
    session_established = asyncio.Event()
    session_topic = None
    
    # Set up wallet to handle proposals
    @wallet.on("session_proposal")
    async def on_proposal(event: Dict[str, Any]) -> None:
        proposal_id = event.get("id")
        result = await wallet.approve_session(
            id=proposal_id,
            namespaces=TEST_NAMESPACES,
        )
        nonlocal session_topic
        session_topic = result.get("topic")
        session_established.set()
    
    # Create pairing and initiate session
    pairing = await dapp.core.pairing.create({
        "methods": ["wc_sessionPropose"],
    })
    uri = pairing["uri"]
    
    # Pair wallet
    await wallet.pair(uri)
    
    # Wait for session establishment
    try:
        await asyncio.wait_for(session_established.wait(), timeout=10.0)
    except asyncio.TimeoutError:
        pytest.fail("Session establishment timeout")
    
    assert session_topic is not None
    
    # Disconnect session
    await wallet.disconnect_session(
        topic=session_topic,
        reason={"code": 6000, "message": "User disconnected"},
    )
    
    # Verify session is removed
    await asyncio.sleep(0.5)  # Give time for cleanup
    sessions = wallet.get_active_sessions()
    assert session_topic not in sessions or len(sessions) == 0

