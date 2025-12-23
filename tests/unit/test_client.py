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


@pytest.mark.asyncio
async def test_client_init_failure(core):
    """Test client initialization failure."""
    opts = {
        "core": core,
        "metadata": {
            "name": "Test Wallet",
            "description": "Test Wallet Description",
            "url": "https://test.wallet",
            "icons": ["https://test.wallet/icon.png"],
        },
    }
    client = WalletKit(opts)
    # Make engine.init raise an exception
    client.engine.init = AsyncMock(side_effect=Exception("Init failed"))
    
    with pytest.raises(Exception, match="Init failed"):
        await client._initialize()
    
    assert client._initialized is False


@pytest.mark.asyncio
async def test_client_pair_exception(client):
    """Test pair exception handling."""
    client.engine.pair = AsyncMock(side_effect=Exception("Pair failed"))
    
    with pytest.raises(Exception, match="Pair failed"):
        await client.pair("wc:test@2?relay-protocol=irn&symKey=test")


@pytest.mark.asyncio
async def test_client_approve_session(client):
    """Test approve session."""
    client.engine.approve_session = AsyncMock(return_value={"topic": "test"})
    
    result = await client.approve_session(
        id=1,
        namespaces={"eip155": {"chains": ["1"], "methods": [], "events": []}}
    )
    
    assert result == {"topic": "test"}
    client.engine.approve_session.assert_called_once()


@pytest.mark.asyncio
async def test_client_approve_session_exception(client):
    """Test approve session exception handling."""
    client.engine.approve_session = AsyncMock(side_effect=Exception("Approve failed"))
    
    with pytest.raises(Exception, match="Approve failed"):
        await client.approve_session(
            id=1,
            namespaces={"eip155": {"chains": ["1"], "methods": [], "events": []}}
        )


@pytest.mark.asyncio
async def test_client_reject_session(client):
    """Test reject session."""
    client.engine.reject_session = AsyncMock()
    
    await client.reject_session(1, {"code": 4001, "message": "User rejected"})
    
    client.engine.reject_session.assert_called_once()


@pytest.mark.asyncio
async def test_client_reject_session_exception(client):
    """Test reject session exception handling."""
    client.engine.reject_session = AsyncMock(side_effect=Exception("Reject failed"))
    
    with pytest.raises(Exception, match="Reject failed"):
        await client.reject_session(1, {"code": 4001, "message": "User rejected"})


@pytest.mark.asyncio
async def test_client_update_session(client):
    """Test update session."""
    client.engine.update_session = AsyncMock(return_value={"acknowledged": True})
    
    result = await client.update_session(
        topic="test_topic",
        namespaces={"eip155": {"chains": ["1"], "methods": [], "events": []}}
    )
    
    assert result == {"acknowledged": True}
    client.engine.update_session.assert_called_once()


@pytest.mark.asyncio
async def test_client_update_session_exception(client):
    """Test update session exception handling."""
    client.engine.update_session = AsyncMock(side_effect=Exception("Update failed"))
    
    with pytest.raises(Exception, match="Update failed"):
        await client.update_session(
            topic="test_topic",
            namespaces={"eip155": {"chains": ["1"], "methods": [], "events": []}}
        )


@pytest.mark.asyncio
async def test_client_extend_session(client):
    """Test extend session."""
    client.engine.extend_session = AsyncMock(return_value={"acknowledged": True})
    
    result = await client.extend_session("test_topic")
    
    assert result == {"acknowledged": True}
    client.engine.extend_session.assert_called_once()


@pytest.mark.asyncio
async def test_client_extend_session_exception(client):
    """Test extend session exception handling."""
    client.engine.extend_session = AsyncMock(side_effect=Exception("Extend failed"))
    
    with pytest.raises(Exception, match="Extend failed"):
        await client.extend_session("test_topic")


@pytest.mark.asyncio
async def test_client_respond_session_request(client):
    """Test respond session request."""
    client.engine.respond_session_request = AsyncMock()
    
    await client.respond_session_request(
        topic="test_topic",
        response={"id": 1, "result": "success"}
    )
    
    client.engine.respond_session_request.assert_called_once()


@pytest.mark.asyncio
async def test_client_respond_session_request_exception(client):
    """Test respond session request exception handling."""
    client.engine.respond_session_request = AsyncMock(side_effect=Exception("Respond failed"))
    
    with pytest.raises(Exception, match="Respond failed"):
        await client.respond_session_request(
            topic="test_topic",
            response={"id": 1, "result": "success"}
        )


@pytest.mark.asyncio
async def test_client_disconnect_session(client):
    """Test disconnect session."""
    client.engine.disconnect_session = AsyncMock()
    
    await client.disconnect_session("test_topic", {"code": 6000, "message": "User disconnected"})
    
    client.engine.disconnect_session.assert_called_once()


@pytest.mark.asyncio
async def test_client_disconnect_session_exception(client):
    """Test disconnect session exception handling."""
    client.engine.disconnect_session = AsyncMock(side_effect=Exception("Disconnect failed"))
    
    with pytest.raises(Exception, match="Disconnect failed"):
        await client.disconnect_session("test_topic", {"code": 6000, "message": "User disconnected"})


@pytest.mark.asyncio
async def test_client_emit_session_event(client):
    """Test emit session event."""
    client.engine.emit_session_event = AsyncMock()
    
    await client.emit_session_event(
        topic="test_topic",
        event={"name": "test_event", "data": {}},
        chain_id="eip155:1"
    )
    
    client.engine.emit_session_event.assert_called_once()


@pytest.mark.asyncio
async def test_client_emit_session_event_exception(client):
    """Test emit session event exception handling."""
    client.engine.emit_session_event = AsyncMock(side_effect=Exception("Emit failed"))
    
    with pytest.raises(Exception, match="Emit failed"):
        await client.emit_session_event(
            topic="test_topic",
            event={"name": "test_event", "data": {}},
            chain_id="eip155:1"
        )


@pytest.mark.asyncio
async def test_client_get_active_sessions_exception(client):
    """Test get active sessions exception handling."""
    client.engine.get_active_sessions = MagicMock(side_effect=Exception("Get sessions failed"))
    
    with pytest.raises(Exception, match="Get sessions failed"):
        client.get_active_sessions()


@pytest.mark.asyncio
async def test_client_get_pending_proposals_exception(client):
    """Test get pending proposals exception handling."""
    client.engine.get_pending_session_proposals = MagicMock(side_effect=Exception("Get proposals failed"))
    
    with pytest.raises(Exception, match="Get proposals failed"):
        client.get_pending_session_proposals()


@pytest.mark.asyncio
async def test_client_get_pending_requests_exception(client):
    """Test get pending requests exception handling."""
    client.engine.get_pending_session_requests = MagicMock(side_effect=Exception("Get requests failed"))
    
    with pytest.raises(Exception, match="Get requests failed"):
        client.get_pending_session_requests()


@pytest.mark.asyncio
async def test_client_register_device_token(client):
    """Test register device token."""
    client.engine.register_device_token = AsyncMock()
    
    await client.register_device_token({"token": "test_token"})
    
    client.engine.register_device_token.assert_called_once()


@pytest.mark.asyncio
async def test_client_register_device_token_exception(client):
    """Test register device token exception handling."""
    client.engine.register_device_token = AsyncMock(side_effect=Exception("Register failed"))
    
    with pytest.raises(Exception, match="Register failed"):
        await client.register_device_token({"token": "test_token"})


@pytest.mark.asyncio
async def test_client_approve_session_authenticate(client):
    """Test approve session authenticate."""
    client.engine.approve_session_authenticate = AsyncMock(return_value={"session": {}})
    
    result = await client.approve_session_authenticate({"id": 1, "auths": []})
    
    assert result == {"session": {}}
    client.engine.approve_session_authenticate.assert_called_once()


@pytest.mark.asyncio
async def test_client_approve_session_authenticate_exception(client):
    """Test approve session authenticate exception handling."""
    client.engine.approve_session_authenticate = AsyncMock(side_effect=Exception("Approve auth failed"))
    
    with pytest.raises(Exception, match="Approve auth failed"):
        await client.approve_session_authenticate({"id": 1, "auths": []})


@pytest.mark.asyncio
async def test_client_format_auth_message(client):
    """Test format auth message."""
    client.engine.format_auth_message = MagicMock(return_value="formatted_message")
    
    result = client.format_auth_message({"domain": "test"}, "iss")
    
    assert result == "formatted_message"
    client.engine.format_auth_message.assert_called_once()


@pytest.mark.asyncio
async def test_client_format_auth_message_exception(client):
    """Test format auth message exception handling."""
    client.engine.format_auth_message = MagicMock(side_effect=Exception("Format failed"))
    
    with pytest.raises(Exception, match="Format failed"):
        client.format_auth_message({"domain": "test"}, "iss")


@pytest.mark.asyncio
async def test_client_reject_session_authenticate(client):
    """Test reject session authenticate."""
    client.engine.reject_session_authenticate = AsyncMock()
    
    await client.reject_session_authenticate(1, {"code": 4001, "message": "User rejected"})
    
    client.engine.reject_session_authenticate.assert_called_once()


@pytest.mark.asyncio
async def test_client_reject_session_authenticate_exception(client):
    """Test reject session authenticate exception handling."""
    client.engine.reject_session_authenticate = AsyncMock(side_effect=Exception("Reject auth failed"))
    
    with pytest.raises(Exception, match="Reject auth failed"):
        await client.reject_session_authenticate(1, {"code": 4001, "message": "User rejected"})


@pytest.mark.asyncio
async def test_client_with_name_option(core):
    """Test client with name option."""
    opts = {
        "core": core,
        "name": "CustomName",
        "metadata": {
            "name": "Test Wallet",
            "description": "Test Wallet Description",
            "url": "https://test.wallet",
            "icons": ["https://test.wallet/icon.png"],
        },
    }
    client = WalletKit(opts)
    assert client.name == "CustomName"


@pytest.mark.asyncio
async def test_client_with_sign_config(core):
    """Test client with sign config."""
    opts = {
        "core": core,
        "signConfig": {"metadata": {}},
        "metadata": {
            "name": "Test Wallet",
            "description": "Test Wallet Description",
            "url": "https://test.wallet",
            "icons": ["https://test.wallet/icon.png"],
        },
    }
    client = WalletKit(opts)
    assert client.sign_config == {"metadata": {}}
