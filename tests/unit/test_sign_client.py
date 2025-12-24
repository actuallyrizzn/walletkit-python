"""Tests for SignClient."""
import asyncio

import pytest
from unittest.mock import AsyncMock

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
    # Avoid network access in SignClient unit tests
    core.relayer.connect = AsyncMock()
    core.relayer.subscribe = AsyncMock(return_value="sub_id")
    core.relayer.unsubscribe = AsyncMock()
    core.relayer.publish = AsyncMock()
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
    async def mock_publish(topic, message, opts=None):
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
    async def mock_publish(t, m, opts=None):
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
    expiry = int(time.time()) + 1  # 1 second from now
    
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
    proposal_expiry = int(time.time()) + 1
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
    request = {
        "domain": "example.com",
        "aud": "https://example.com",
        "version": "1",
        "nonce": "12345",
        "iat": "2023-01-01T00:00:00Z",
        "statement": "Test statement",
    }
    iss = "did:pkh:eip155:1:0x1234567890123456789012345678901234567890"
    
    message = sign_client.format_auth_message({
        "request": request,
        "iss": iss,
    })
    
    assert isinstance(message, str)
    assert "example.com wants you to sign in" in message
    assert "0x1234567890123456789012345678901234567890" in message
    assert "Test statement" in message
    assert "Version: 1" in message
    assert "Nonce: 12345" in message
    assert "URI: https://example.com" in message


@pytest.mark.asyncio
async def test_sign_client_approve_session_authenticate(sign_client):
    """Test approving session authentication."""
    from unittest.mock import AsyncMock
    
    # Simulate an auth request
    auth_id = 123
    auth_topic = "auth_topic"
    auth_params = {
        "authPayload": {
            "domain": "example.com",
            "chains": ["eip155:1"],
        },
        "requester": {"metadata": {}},
    }
    # requester.publicKey is required by SignClient to derive the auth response topic
    from walletkit.utils.crypto_utils import generate_key_pair
    auth_params["requester"]["publicKey"] = generate_key_pair()["publicKey"]
    
    # Set up crypto for the topic
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=auth_topic)
    
    # Manually add pending auth request (simulating _handle_session_authenticate)
    sign_client._pending_auth_requests[auth_id] = {
        "id": auth_id,
        "topic": auth_topic,
        "params": auth_params,
    }
    
    # Mock relayer.publish to avoid actual network calls
    original_publish = sign_client.core.relayer.publish
    sign_client.core.relayer.publish = AsyncMock()
    
    try:
        # Create auth objects
        auths = [
            {
                "h": {"t": "caip122"},
                "p": {
                    "iss": "did:pkh:eip155:1:0x1234567890123456789012345678901234567890",
                    "domain": "example.com",
                    "version": "1",
                    "nonce": "12345",
                    "iat": "2023-01-01T00:00:00Z",
                },
                "s": {"t": "eip191", "s": "0xsignature"},
            }
        ]
        
        result = await sign_client.approve_session_authenticate({
            "id": auth_id,
            "auths": auths,
        })
        
        assert "session" in result
        assert isinstance(result["session"]["topic"], str)
        assert len(result["session"]["topic"]) == 64
        assert sign_client.session.has(result["session"]["topic"])
        sign_client.core.relayer.publish.assert_awaited_once()
        assert auth_id not in sign_client._pending_auth_requests
    finally:
        sign_client.core.relayer.publish = original_publish


@pytest.mark.asyncio
async def test_sign_client_reject_session_authenticate(sign_client):
    """Test rejecting session authentication."""
    from unittest.mock import AsyncMock
    
    # Simulate an auth request
    auth_id = 456
    auth_topic = "auth_topic_reject"
    auth_params = {
        "authPayload": {
            "domain": "example.com",
            "chains": ["eip155:1"],
        },
        "requester": {"metadata": {}},
    }
    from walletkit.utils.crypto_utils import generate_key_pair
    auth_params["requester"]["publicKey"] = generate_key_pair()["publicKey"]
    
    # Set up crypto for the topic
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=auth_topic)
    
    # Manually add pending auth request
    sign_client._pending_auth_requests[auth_id] = {
        "id": auth_id,
        "topic": auth_topic,
        "params": auth_params,
    }
    
    # Mock relayer.publish to avoid actual network calls
    original_publish = sign_client.core.relayer.publish
    sign_client.core.relayer.publish = AsyncMock()
    
    try:
        reason = {"code": 5000, "message": "User rejected"}
        await sign_client.reject_session_authenticate({
            "id": auth_id,
            "reason": reason,
        })
        
        sign_client.core.relayer.publish.assert_awaited_once()
        assert auth_id not in sign_client._pending_auth_requests
    finally:
        sign_client.core.relayer.publish = original_publish



@pytest.mark.asyncio
async def test_sign_client_approve_missing_id(sign_client):
    """Test approve with missing proposal ID."""
    with pytest.raises(ValueError, match="Proposal ID required"):
        await sign_client.approve({"namespaces": {}})


@pytest.mark.asyncio
async def test_sign_client_approve_nonexistent_proposal(sign_client):
    """Test approve with nonexistent proposal."""
    with pytest.raises(ValueError, match="Proposal topic not found"):
        await sign_client.approve({"id": 99999, "namespaces": {}})


@pytest.mark.asyncio
async def test_sign_client_approve_success(sign_client):
    """Test successful session approval."""
    proposal_id = 123
    topic = "test_topic"
    
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=topic)
    
    proposal = {
        "id": proposal_id,
        "topic": topic,
        "params": {
            "id": proposal_id,
            "proposer": {"metadata": {"name": "Test dApp"}},
            "requiredNamespaces": {"eip155": {"chains": ["eip155:1"]}},
        },
    }
    # proposer.publicKey is required by SignClient to derive the session topic
    from walletkit.utils.crypto_utils import generate_key_pair
    proposal["params"]["proposer"]["publicKey"] = generate_key_pair()["publicKey"]
    await sign_client.proposal.set(proposal_id, proposal)
    
    async def mock_publish(t, m, opts=None):
        pass
    
    original_publish = sign_client.core.relayer.publish
    sign_client.core.relayer.publish = mock_publish
    
    try:
        result = await sign_client.approve({
            "id": proposal_id,
            "namespaces": {"eip155": {"chains": ["eip155:1"], "methods": [], "events": []}},
        })
        
        assert "topic" in result
        assert "acknowledged" in result
        assert isinstance(result["topic"], str)
        assert len(result["topic"]) == 64
    finally:
        sign_client.core.relayer.publish = original_publish


@pytest.mark.asyncio
async def test_sign_client_reject_missing_id(sign_client):
    """Test reject with missing proposal ID."""
    with pytest.raises(ValueError, match="Proposal ID required"):
        await sign_client.reject({"reason": {"code": 5000}})


@pytest.mark.asyncio
async def test_sign_client_reject_nonexistent_proposal(sign_client):
    """Test reject with nonexistent proposal."""
    with pytest.raises(ValueError, match="Proposal topic not found"):
        await sign_client.reject({"id": 99999, "reason": {"code": 5000}})


@pytest.mark.asyncio
async def test_sign_client_update_missing_topic(sign_client):
    """Test update with missing topic."""
    with pytest.raises(ValueError, match="Topic and namespaces required"):
        await sign_client.update({"namespaces": {}})


@pytest.mark.asyncio
async def test_sign_client_update_missing_namespaces(sign_client):
    """Test update with missing namespaces."""
    with pytest.raises(ValueError, match="Topic and namespaces required"):
        await sign_client.update({"topic": "test_topic"})


@pytest.mark.asyncio
async def test_sign_client_update_success(sign_client):
    """Test successful session update."""
    topic = "test_topic"
    
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=topic)
    
    session = {
        "topic": topic,
        "expiry": 1234567890,
        "namespaces": {},
        "peer": {},
    }
    await sign_client.session.set(topic, session)
    
    async def mock_publish(t, m, opts=None):
        pass
    
    original_publish = sign_client.core.relayer.publish
    sign_client.core.relayer.publish = mock_publish
    
    try:
        result = await sign_client.update({
            "topic": topic,
            "namespaces": {"eip155": {"chains": ["eip155:1"], "methods": [], "events": []}},
        })
        
        assert "acknowledged" in result
    finally:
        sign_client.core.relayer.publish = original_publish


@pytest.mark.asyncio
async def test_sign_client_extend_missing_topic(sign_client):
    """Test extend with missing topic."""
    with pytest.raises(ValueError, match="Topic required"):
        await sign_client.extend({})


@pytest.mark.asyncio
async def test_sign_client_extend_success(sign_client):
    """Test successful session extend."""
    topic = "test_topic"
    
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=topic)
    
    import time
    session = {
        "topic": topic,
        "expiry": int(time.time()) + 10000,
        "namespaces": {},
        "peer": {},
    }
    await sign_client.session.set(topic, session)
    sign_client.core.expirer.set(topic, session["expiry"])
    
    async def mock_publish(t, m, opts=None):
        pass
    
    original_publish = sign_client.core.relayer.publish
    sign_client.core.relayer.publish = mock_publish
    
    try:
        result = await sign_client.extend({"topic": topic})
        
        assert "acknowledged" in result
    finally:
        sign_client.core.relayer.publish = original_publish


@pytest.mark.asyncio
async def test_sign_client_respond_missing_topic(sign_client):
    """Test respond with missing topic."""
    with pytest.raises(ValueError, match="Topic and response required"):
        await sign_client.respond({"response": {"id": 1}})


@pytest.mark.asyncio
async def test_sign_client_respond_missing_response(sign_client):
    """Test respond with missing response."""
    with pytest.raises(ValueError, match="Topic and response required"):
        await sign_client.respond({"topic": "test_topic"})


@pytest.mark.asyncio
async def test_sign_client_respond_success(sign_client):
    """Test successful request response."""
    topic = "test_topic"
    
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=topic)
    
    request_id = 123
    await sign_client.request_store.add({
        "topic": topic,
        "request": {"id": request_id, "method": "eth_sendTransaction"},
    })
    
    async def mock_publish(t, m, opts=None):
        pass
    
    original_publish = sign_client.core.relayer.publish
    sign_client.core.relayer.publish = mock_publish
    
    try:
        await sign_client.respond({
            "topic": topic,
            "response": {"id": request_id, "jsonrpc": "2.0", "result": "0x123"},
        })
        
        # Request should be removed
        assert not sign_client.request_store.has(request_id)
    finally:
        sign_client.core.relayer.publish = original_publish


@pytest.mark.asyncio
async def test_sign_client_disconnect_missing_topic(sign_client):
    """Test disconnect with missing topic."""
    with pytest.raises(ValueError, match="Topic required"):
        await sign_client.disconnect({"reason": {"code": 6000}})


@pytest.mark.asyncio
async def test_sign_client_emit_missing_topic(sign_client):
    """Test emit with missing topic."""
    with pytest.raises(ValueError, match="Topic, event, and chainId required"):
        await sign_client.emit({"event": {}})


@pytest.mark.asyncio
async def test_sign_client_emit_missing_event(sign_client):
    """Test emit with missing event."""
    with pytest.raises(ValueError, match="Topic, event, and chainId required"):
        await sign_client.emit({"topic": "test_topic"})


@pytest.mark.asyncio
async def test_sign_client_emit_missing_chain_id(sign_client):
    """Test emit with missing chainId."""
    with pytest.raises(ValueError, match="Topic, event, and chainId required"):
        await sign_client.emit({"topic": "test_topic", "event": {}})


@pytest.mark.asyncio
async def test_sign_client_emit_success(sign_client):
    """Test successful event emission."""
    topic = "test_topic"
    
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=topic)
    
    async def mock_publish(t, m, opts=None):
        pass
    
    original_publish = sign_client.core.relayer.publish
    sign_client.core.relayer.publish = mock_publish
    
    try:
        await sign_client.emit({
            "topic": topic,
            "event": {"name": "accountsChanged", "data": ["0x123"]},
            "chainId": "eip155:1",
        })
    finally:
        sign_client.core.relayer.publish = original_publish


@pytest.mark.asyncio
async def test_sign_client_handle_session_propose(sign_client):
    """Test handling session proposal message."""
    proposal_id = 123
    topic = "proposal_topic"
    
    params = {
        "id": proposal_id,
        "proposer": {"metadata": {"name": "Test dApp"}},
        "requiredNamespaces": {},
    }
    
    proposal_received = False
    
    async def on_proposal(event):
        nonlocal proposal_received
        proposal_received = True
    
    sign_client.on("session_proposal", on_proposal)
    
    await sign_client._handle_session_propose(topic, params, proposal_id)
    
    assert proposal_received
    assert sign_client.proposal.has(proposal_id)


@pytest.mark.asyncio
async def test_sign_client_handle_session_settle(sign_client):
    """Test handling session settlement."""
    topic = "session_topic"
    
    import time
    expiry = int(time.time()) + 10000
    
    params = {
        "session": {
            "topic": topic,
            "expiry": expiry,
            "namespaces": {},
            "peer": {},
        }
    }
    
    # Set up acknowledgment callback
    ack_called = False
    
    async def ack():
        nonlocal ack_called
        ack_called = True
    
    sign_client._pending_acknowledgments[topic] = ack
    
    await sign_client._handle_session_settle(topic, params, None)
    
    assert sign_client.session.has(topic)
    assert ack_called
    assert topic not in sign_client._pending_acknowledgments


@pytest.mark.asyncio
async def test_sign_client_handle_session_request(sign_client):
    """Test handling session request."""
    topic = "session_topic"
    request_id = 456
    
    params = {
        "request": {
            "id": request_id,
            "method": "eth_sendTransaction",
            "params": {},
        }
    }
    
    request_received = False
    
    async def on_request(event):
        nonlocal request_received
        request_received = True
    
    sign_client.on("session_request", on_request)
    
    await sign_client._handle_session_request(topic, params, request_id)
    
    assert request_received
    assert sign_client.request_store.has(request_id)


@pytest.mark.asyncio
async def test_sign_client_handle_session_update(sign_client):
    """Test handling session update."""
    topic = "session_topic"
    
    session = {
        "topic": topic,
        "expiry": 1234567890,
        "namespaces": {},
        "peer": {},
    }
    await sign_client.session.set(topic, session)
    
    params = {
        "namespaces": {"eip155": {"chains": ["eip155:1"]}},
    }
    
    ack_called = False
    
    async def ack():
        nonlocal ack_called
        ack_called = True
    
    sign_client._pending_acknowledgments[topic] = ack
    
    await sign_client._handle_session_update(topic, params, None)
    
    updated_session = sign_client.session.get(topic)
    assert "namespaces" in updated_session
    assert ack_called


@pytest.mark.asyncio
async def test_sign_client_handle_session_extend(sign_client):
    """Test handling session extend."""
    topic = "session_topic"
    
    import time
    expiry = int(time.time()) + 10000
    
    session = {
        "topic": topic,
        "expiry": expiry,
        "namespaces": {},
        "peer": {},
    }
    await sign_client.session.set(topic, session)
    sign_client.core.expirer.set(topic, expiry)
    
    new_expiry = int(time.time()) + 20000
    params = {"expiry": new_expiry}
    
    ack_called = False
    
    async def ack():
        nonlocal ack_called
        ack_called = True
    
    sign_client._pending_acknowledgments[topic] = ack
    
    await sign_client._handle_session_extend(topic, params, None)
    
    updated_session = sign_client.session.get(topic)
    assert updated_session["expiry"] == new_expiry
    assert ack_called


@pytest.mark.asyncio
async def test_sign_client_handle_session_delete(sign_client):
    """Test handling session delete."""
    topic = "session_topic"
    
    session = {
        "topic": topic,
        "expiry": 1234567890,
        "namespaces": {},
        "peer": {},
    }
    await sign_client.session.set(topic, session)
    sign_client.core.expirer.set(topic, session["expiry"])
    
    delete_received = False
    
    async def on_delete(event):
        nonlocal delete_received
        delete_received = True
    
    sign_client.on("session_delete", on_delete)
    
    await sign_client._handle_session_delete(topic, {}, None)
    
    assert not sign_client.session.has(topic)
    assert delete_received


@pytest.mark.asyncio
async def test_sign_client_handle_session_authenticate(sign_client):
    """Test handling session authenticate."""
    topic = "auth_topic"
    auth_id = 789
    
    params = {
        "authPayload": {
            "domain": "example.com",
            "chains": ["eip155:1"],
        },
        "requester": {},
    }
    
    auth_received = False
    
    async def on_auth(event):
        nonlocal auth_received
        auth_received = True
    
    sign_client.on("session_authenticate", on_auth)
    
    await sign_client._handle_session_authenticate(topic, params, auth_id)
    
    assert auth_received
    assert auth_id in sign_client._pending_auth_requests


@pytest.mark.asyncio
async def test_sign_client_approve_session_authenticate_missing_id(sign_client):
    """Test approve session authenticate with missing ID."""
    with pytest.raises(ValueError, match="Auth request ID required"):
        await sign_client.approve_session_authenticate({"auths": []})


@pytest.mark.asyncio
async def test_sign_client_approve_session_authenticate_missing_auths(sign_client):
    """Test approve session authenticate with missing auths."""
    with pytest.raises(ValueError, match="Auths required"):
        await sign_client.approve_session_authenticate({"id": 123})


@pytest.mark.asyncio
async def test_sign_client_approve_session_authenticate_nonexistent(sign_client):
    """Test approve session authenticate with nonexistent request."""
    with pytest.raises(ValueError, match="Auth request not found"):
        await sign_client.approve_session_authenticate({
            "id": 99999,
            "auths": [{"p": {"iss": "did:pkh:eip155:1:0x123"}}],
        })


@pytest.mark.asyncio
async def test_sign_client_reject_session_authenticate_missing_id(sign_client):
    """Test reject session authenticate with missing ID."""
    with pytest.raises(ValueError, match="Auth request ID required"):
        await sign_client.reject_session_authenticate({"reason": {"code": 5000}})


@pytest.mark.asyncio
async def test_sign_client_reject_session_authenticate_nonexistent(sign_client):
    """Test reject session authenticate with nonexistent request."""
    with pytest.raises(ValueError, match="Auth request not found"):
        await sign_client.reject_session_authenticate({
            "id": 99999,
            "reason": {"code": 5000},
        })


@pytest.mark.asyncio
async def test_sign_client_format_auth_message_missing_iss(sign_client):
    """Test format auth message with missing issuer."""
    with pytest.raises(ValueError, match="Issuer.*required"):
        sign_client.format_auth_message({
            "request": {"domain": "example.com"},
        })


@pytest.mark.asyncio
async def test_sign_client_format_auth_message_missing_domain(sign_client):
    """Test format auth message with missing domain."""
    with pytest.raises(ValueError, match="Domain required"):
        sign_client.format_auth_message({
            "request": {},
            "iss": "did:pkh:eip155:1:0x123",
        })


@pytest.mark.asyncio
async def test_sign_client_format_auth_message_missing_uri(sign_client):
    """Test format auth message with missing URI/aud."""
    with pytest.raises(ValueError, match="Either 'aud' or 'uri' is required"):
        sign_client.format_auth_message({
            "request": {"domain": "example.com"},
            "iss": "did:pkh:eip155:1:0x123",
        })


@pytest.mark.asyncio
async def test_sign_client_format_auth_message_with_resources(sign_client):
    """Test format auth message with resources."""
    import base64
    import json

    # Minimal recap that should be appended into the statement (WalletConnect behavior).
    recap_obj = {
        "att": {
            "eip155": {
                "request/eth_accounts": [{}],
                "request/personal_sign": [{}],
                "request/eth_sendTransaction": [{}],
            }
        }
    }
    recap_json = json.dumps(recap_obj, separators=(",", ":")).encode("utf-8")
    recap_b64url = base64.urlsafe_b64encode(recap_json).decode("utf-8").replace("=", "")
    recap_resource = f"urn:recap:{recap_b64url}"

    request = {
        "domain": "example.com",
        "aud": "https://example.com",
        "statement": "Test statement",
        "version": "1",
        "nonce": "test_nonce",
        "iat": "2023-01-01T00:00:00.000Z",
        "resources": ["https://example.com/resource1", recap_resource],
    }
    iss = "did:pkh:eip155:1:0x1234567890123456789012345678901234567890"
    
    message = sign_client.format_auth_message({
        "request": request,
        "iss": iss,
    })
    
    assert "Resources:" in message
    assert "- https://example.com/resource1" in message
    assert f"- {recap_resource}" in message

    expected_recap_stmt = (
        "I further authorize the stated URI to perform the following actions on my behalf: "
        "(1) 'request': 'eth_accounts', 'eth_sendTransaction', 'personal_sign' for 'eip155'."
    )
    assert "Test statement " + expected_recap_stmt in message


@pytest.mark.asyncio
async def test_sign_client_format_auth_message_with_expiration(sign_client):
    """Test format auth message with expiration time."""
    request = {
        "domain": "example.com",
        "aud": "https://example.com",
        "version": "1",
        "nonce": "12345",
        "iat": "2023-01-01T00:00:00Z",
        "exp": "2024-01-01T00:00:00Z",
    }
    iss = "did:pkh:eip155:1:0x1234567890123456789012345678901234567890"
    
    message = sign_client.format_auth_message({
        "request": request,
        "iss": iss,
    })
    
    assert "Expiration Time:" in message
    assert "2024-01-01T00:00:00Z" in message


@pytest.mark.asyncio
async def test_sign_client_expirer_handles_session_expiry(sign_client):
    """Test expirer handles session expiry."""
    import asyncio
    from walletkit.controllers.expirer import EXPIRER_EVENTS
    
    topic = "expiry_topic"
    
    import time
    expiry = int(time.time()) - 1  # Already expired
    
    session = {
        "topic": topic,
        "expiry": expiry,
        "namespaces": {},
        "peer": {},
    }
    await sign_client.session.set(topic, session)
    
    # Manually trigger expiry (simulating expirer event)
    await sign_client.core.expirer.events.emit(EXPIRER_EVENTS["expired"], {
        "target": f"topic:{topic}",
    })
    
    # Session should be deleted
    await asyncio.sleep(0.1)  # Give time for async operations
    assert not sign_client.session.has(topic)


@pytest.mark.asyncio
async def test_sign_client_expirer_handles_proposal_expiry(sign_client):
    """Test expirer handles proposal expiry."""
    import asyncio
    from walletkit.controllers.expirer import EXPIRER_EVENTS
    
    proposal_id = 999
    
    proposal = {
        "id": proposal_id,
        "topic": "proposal_topic",
        "params": {"id": proposal_id},
    }
    await sign_client.proposal.set(proposal_id, proposal)
    
    # Manually trigger expiry (simulating expirer event)
    await sign_client.core.expirer.events.emit(EXPIRER_EVENTS["expired"], {
        "target": f"id:{proposal_id}",
    })
    
    # Proposal should be deleted
    await asyncio.sleep(0.1)  # Give time for async operations
    assert not sign_client.proposal.has(proposal_id)


@pytest.mark.asyncio
async def test_sign_client_init_event_client_error(core):
    """Test init with event_client error."""
    # Make event_client.init raise an exception
    core.event_client.init = AsyncMock(side_effect=Exception("Event client error"))
    
    sign_client = await SignClient.init(
        core=core,
        metadata={"name": "Test", "description": "Test"},
    )
    
    # Should still initialize successfully
    assert sign_client._initialized is True


@pytest.mark.asyncio
async def test_sign_client_relayer_message_handler_error(sign_client):
    """Test relayer message handler error handling."""
    # Emit message with invalid data
    await sign_client.core.relayer.events.emit("message", {
        "topic": "test_topic",
        "message": "invalid_message",
    })
    
    # Should handle error gracefully
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_sign_client_relayer_message_missing_topic(sign_client):
    """Test relayer message handler with missing topic."""
    await sign_client.core.relayer.events.emit("message", {
        "message": "test_message",
    })
    
    # Should handle gracefully
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_sign_client_relayer_message_missing_message(sign_client):
    """Test relayer message handler with missing message."""
    await sign_client.core.relayer.events.emit("message", {
        "topic": "test_topic",
    })
    
    # Should handle gracefully
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_sign_client_handle_protocol_message_wc_sessionSettle(sign_client):
    """Test handling wc_sessionSettle message."""
    topic = "test_topic"
    payload = {
        "method": "wc_sessionSettle",
        "params": {
            "topic": topic,
            "session": {"topic": topic, "peer": {"metadata": {}}},
        },
        "id": 1,
    }
    
    await sign_client._handle_protocol_message(topic, payload)
    # Should handle without error


@pytest.mark.asyncio
async def test_sign_client_handle_protocol_message_wc_sessionEvent(sign_client):
    """Test handling wc_sessionEvent message."""
    topic = "test_topic"
    payload = {
        "method": "wc_sessionEvent",
        "params": {
            "topic": topic,
            "event": {"name": "test_event", "data": {}},
            "chainId": "eip155:1",
        },
        "id": 1,
    }
    
    await sign_client._handle_protocol_message(topic, payload)
    # Should handle without error


@pytest.mark.asyncio
async def test_sign_client_acknowledged_callback(sign_client):
    """Test acknowledged callback in approve."""
    # Mock relayer to avoid actual network calls
    sign_client.core.relayer.publish = AsyncMock()
    sign_client.core.relayer.connect = AsyncMock()
    
    # Create a proposal with topic
    proposal_id = 1
    topic = "test_topic"
    proposal = {
        "id": proposal_id,
        "topic": topic,
        "params": {
            "requiredNamespaces": {
                "eip155": {"chains": ["eip155:1"], "methods": [], "events": []}
            },
            "proposer": {"metadata": {}},
        },
    }
    from walletkit.utils.crypto_utils import generate_key_pair
    proposal["params"]["proposer"]["publicKey"] = generate_key_pair()["publicKey"]
    await sign_client.proposal.set(proposal_id, proposal)
    
    # Set up sym key for the topic
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=topic)
    
    # Approve session
    result = await sign_client.approve({
        "id": proposal_id,
        "namespaces": {
            "eip155": {"chains": ["eip155:1"], "methods": [], "events": []}
        },
    })
    
    # Call acknowledged callback
    ack_callback = result.get("acknowledged")
    if ack_callback:
        await ack_callback()
    
    # Proposal should be deleted
    with pytest.raises(KeyError):
        sign_client.proposal.get(proposal_id)


@pytest.mark.asyncio
async def test_sign_client_update_acknowledged_callback(sign_client):
    """Test acknowledged callback in update."""
    # Mock relayer to avoid actual network calls
    sign_client.core.relayer.publish = AsyncMock()
    sign_client.core.relayer.connect = AsyncMock()
    
    # Create a session first with sym key
    topic = "test_topic"
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    await sign_client.core.crypto.set_sym_key(sym_key, override_topic=topic)
    
    session = {
        "topic": topic,
        "namespaces": {
            "eip155": {"chains": ["1"], "methods": [], "events": []}
        },
        "peer": {"metadata": {}},
    }
    await sign_client.session.set(topic, session)
    
    # Update session
    result = await sign_client.update({
        "topic": topic,
        "namespaces": {
            "eip155": {"chains": ["1", "137"], "methods": [], "events": []}
        },
    })
    
    # Call acknowledged callback
    ack_callback = result.get("acknowledged")
    if ack_callback:
        await ack_callback()


@pytest.mark.asyncio
async def test_sign_client_expirer_error_handling(sign_client):
    """Test expirer error handling."""
    # Create a proposal
    proposal_id = 123
    proposal = {
        "id": proposal_id,
        "params": {"requiredNamespaces": {}},
    }
    await sign_client.proposal.set(proposal_id, proposal)
    
    # Manually trigger expirer event with invalid data
    from walletkit.controllers.expirer import EXPIRER_EVENTS
    
    await sign_client.core.expirer.events.emit(EXPIRER_EVENTS["expired"], {
        "target": "invalid_target",
    })
    
    # Should handle error gracefully
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_sign_client_event_listeners(sign_client):
    """Test event listener methods."""
    listener = lambda x: None
    
    # Test once
    result = sign_client.once("test_event", listener)
    assert result is not None
    
    # Test off
    result = sign_client.off("test_event", listener)
    assert result is not None