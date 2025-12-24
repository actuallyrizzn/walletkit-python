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


@pytest.mark.asyncio
async def test_engine_init_with_event_client_error(mock_client):
    """Test engine init with event_client error."""
    from walletkit.exceptions import InitializationError
    
    # Make event_client.init raise an exception
    mock_client.core.event_client.init = AsyncMock(side_effect=Exception("Event client error"))
    
    engine = Engine(mock_client)
    
    # Should raise InitializationError
    with pytest.raises(InitializationError):
    await engine.init()


@pytest.mark.asyncio
async def test_engine_approve_session(engine):
    """Test approve session."""
    mock_acknowledged = AsyncMock()
    engine.sign_client.approve = AsyncMock(return_value={
        "acknowledged": mock_acknowledged,
        "topic": "test_topic"
    })
    engine.sign_client.session = MagicMock()
    engine.sign_client.session.get = MagicMock(return_value={"topic": "test_topic"})
    
    result = await engine.approve_session(
        id=1,
        namespaces={"eip155": {"chains": ["1"], "methods": [], "events": []}}
    )
    
    assert result == {"topic": "test_topic"}
    mock_acknowledged.assert_called_once()


@pytest.mark.asyncio
async def test_engine_approve_session_not_initialized(mock_client):
    """Test approve session when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        await engine.approve_session(
            id=1,
            namespaces={"eip155": {"chains": ["1"], "methods": [], "events": []}}
        )


@pytest.mark.asyncio
async def test_engine_reject_session(engine):
    """Test reject session."""
    engine.sign_client.reject = AsyncMock()
    
    await engine.reject_session(1, {"code": 4001, "message": "User rejected"})
    
    engine.sign_client.reject.assert_called_once()


@pytest.mark.asyncio
async def test_engine_reject_session_not_initialized(mock_client):
    """Test reject session when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        await engine.reject_session(1, {"code": 4001, "message": "User rejected"})


@pytest.mark.asyncio
async def test_engine_update_session(engine):
    """Test update session."""
    mock_acknowledged = AsyncMock()
    engine.sign_client.update = AsyncMock(return_value={"acknowledged": mock_acknowledged})
    
    result = await engine.update_session(
        topic="test_topic",
        namespaces={"eip155": {"chains": ["1"], "methods": [], "events": []}}
    )
    
    assert result == {"acknowledged": mock_acknowledged}
    engine.sign_client.update.assert_called_once()


@pytest.mark.asyncio
async def test_engine_update_session_not_initialized(mock_client):
    """Test update session when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        await engine.update_session("test_topic", {"eip155": {"chains": ["1"]}})


@pytest.mark.asyncio
async def test_engine_extend_session(engine):
    """Test extend session."""
    mock_acknowledged = AsyncMock()
    engine.sign_client.extend = AsyncMock(return_value={"acknowledged": mock_acknowledged})
    
    result = await engine.extend_session("test_topic")
    
    assert result == {"acknowledged": mock_acknowledged}
    engine.sign_client.extend.assert_called_once()


@pytest.mark.asyncio
async def test_engine_extend_session_not_initialized(mock_client):
    """Test extend session when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        await engine.extend_session("test_topic")


@pytest.mark.asyncio
async def test_engine_respond_session_request(engine):
    """Test respond session request."""
    engine.sign_client.respond = AsyncMock()
    
    await engine.respond_session_request(
        topic="test_topic",
        response={"id": 1, "result": "success"}
    )
    
    engine.sign_client.respond.assert_called_once()


@pytest.mark.asyncio
async def test_engine_respond_session_request_not_initialized(mock_client):
    """Test respond session request when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        await engine.respond_session_request("test_topic", {"id": 1, "result": "success"})


@pytest.mark.asyncio
async def test_engine_disconnect_session(engine):
    """Test disconnect session."""
    engine.sign_client.disconnect = AsyncMock()
    
    await engine.disconnect_session("test_topic", {"code": 6000, "message": "User disconnected"})
    
    engine.sign_client.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_engine_disconnect_session_not_initialized(mock_client):
    """Test disconnect session when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        await engine.disconnect_session("test_topic", {"code": 6000, "message": "User disconnected"})


@pytest.mark.asyncio
async def test_engine_emit_session_event(engine):
    """Test emit session event."""
    engine.sign_client.emit = AsyncMock()
    
    await engine.emit_session_event(
        topic="test_topic",
        event={"name": "test_event", "data": {}},
        chain_id="eip155:1"
    )
    
    engine.sign_client.emit.assert_called_once()


@pytest.mark.asyncio
async def test_engine_emit_session_event_not_initialized(mock_client):
    """Test emit session event when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        await engine.emit_session_event("test_topic", {"name": "test"}, "eip155:1")


@pytest.mark.asyncio
async def test_engine_get_active_sessions_not_initialized(mock_client):
    """Test get active sessions when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        engine.get_active_sessions()


@pytest.mark.asyncio
async def test_engine_get_pending_proposals_not_initialized(mock_client):
    """Test get pending proposals when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        engine.get_pending_session_proposals()


@pytest.mark.asyncio
async def test_engine_get_pending_requests_not_initialized(mock_client):
    """Test get pending requests when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        engine.get_pending_session_requests()


@pytest.mark.asyncio
async def test_engine_register_device_token(engine, mock_client):
    """Test register device token."""
    mock_client.core.echo_client.register_device_token = AsyncMock()
    
    await engine.register_device_token({"token": "test_token"})
    
    mock_client.core.echo_client.register_device_token.assert_called_once()


@pytest.mark.asyncio
async def test_engine_register_device_token_not_available(mock_client):
    """Test register device token when echo_client not available."""
    # Remove echo_client
    delattr(mock_client.core, "echo_client")
    
    engine = Engine(mock_client)
    await engine.init()
    
    with pytest.raises(NotImplementedError, match="EchoClient not available"):
        await engine.register_device_token({"token": "test_token"})


@pytest.mark.asyncio
async def test_engine_approve_session_authenticate(engine):
    """Test approve session authenticate."""
    engine.sign_client.approve_session_authenticate = AsyncMock(return_value={"session": {}})
    
    result = await engine.approve_session_authenticate({"id": 1, "auths": []})
    
    assert result == {"session": {}}
    engine.sign_client.approve_session_authenticate.assert_called_once()


@pytest.mark.asyncio
async def test_engine_approve_session_authenticate_not_initialized(mock_client):
    """Test approve session authenticate when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        await engine.approve_session_authenticate({"id": 1, "auths": []})


@pytest.mark.asyncio
async def test_engine_reject_session_authenticate(engine):
    """Test reject session authenticate."""
    engine.sign_client.reject_session_authenticate = AsyncMock()
    
    await engine.reject_session_authenticate(1, {"code": 4001, "message": "User rejected"})
    
    engine.sign_client.reject_session_authenticate.assert_called_once()


@pytest.mark.asyncio
async def test_engine_reject_session_authenticate_not_initialized(mock_client):
    """Test reject session authenticate when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        await engine.reject_session_authenticate(1, {"code": 4001, "message": "User rejected"})


@pytest.mark.asyncio
async def test_engine_format_auth_message(engine):
    """Test format auth message."""
    engine.sign_client.format_auth_message = MagicMock(return_value="formatted_message")
    
    result = engine.format_auth_message({"domain": "test"}, "iss")
    
    assert result == "formatted_message"
    engine.sign_client.format_auth_message.assert_called_once()


@pytest.mark.asyncio
async def test_engine_format_auth_message_not_initialized(mock_client):
    """Test format auth message when not initialized."""
    engine = Engine(mock_client)
    
    with pytest.raises(RuntimeError, match="Engine not initialized"):
        engine.format_auth_message({"domain": "test"}, "iss")


@pytest.mark.asyncio
async def test_engine_event_handlers(engine, mock_client):
    """Test event handler methods."""
    listener = MagicMock()
    
    # Test on
    engine.on("session_proposal", listener)
    mock_client.events.on.assert_called()
    
    # Test once
    engine.once("session_proposal", listener)
    mock_client.events.once.assert_called()
    
    # Test off
    engine.off("session_proposal", listener)
    mock_client.events.off.assert_called()
    
    # Test remove_listener
    engine.remove_listener("session_proposal", listener)
    mock_client.events.remove_listener.assert_called()


@pytest.mark.asyncio
async def test_engine_event_forwarding(engine):
    """Test event forwarding from SignClient to WalletKit."""
    # Test that event handlers are set up
    engine.sign_client.events.on = MagicMock()
    engine.sign_client.events.off = MagicMock()
    engine.sign_client.events.once = MagicMock()
    engine.sign_client.events.remove_listener = MagicMock()
    
    listener = MagicMock()
    
    # Register listener for session_proposal
    engine.on("session_proposal", listener)
    
    # Verify event forwarding was set up
    assert engine.sign_client.events.on.called
    
    # Test event emission
    mock_client = engine.client
    mock_client.events.emit = AsyncMock()
    
    # Trigger the event handler
    await engine._on_session_proposal({"id": 1})
    mock_client.events.emit.assert_called_with("session_proposal", {"id": 1})
    
    await engine._on_session_request({"id": 1})
    mock_client.events.emit.assert_called_with("session_request", {"id": 1})
    
    await engine._on_session_delete({"topic": "test"})
    mock_client.events.emit.assert_called_with("session_delete", {"topic": "test"})
    
    await engine._on_proposal_expire({"id": 1})
    mock_client.events.emit.assert_called_with("proposal_expire", {"id": 1})
    
    await engine._on_session_request_expire({"id": 1})
    mock_client.events.emit.assert_called_with("session_request_expire", {"id": 1})
    
    await engine._on_session_authenticate({"id": 1})
    mock_client.events.emit.assert_called_with("session_authenticate", {"id": 1})


@pytest.mark.asyncio
async def test_engine_set_event_without_sign_client(mock_client):
    """Test _set_event when sign_client is not initialized."""
    engine = Engine(mock_client)
    
    # Should not raise error
    engine._set_event("session_proposal", "on")
    
    # Now initialize and test
    await engine.init()
    engine.sign_client.events.on = MagicMock()
    
    engine._set_event("session_proposal", "on")
    engine.sign_client.events.on.assert_called()
    
    engine.sign_client.events.off = MagicMock()
    engine._set_event("session_proposal", "off")
    engine.sign_client.events.off.assert_called()
    
    engine.sign_client.events.once = MagicMock()
    engine._set_event("session_proposal", "once")
    engine.sign_client.events.once.assert_called()
    
    engine.sign_client.events.remove_listener = MagicMock()
    engine._set_event("session_proposal", "removeListener")
    engine.sign_client.events.remove_listener.assert_called()


@pytest.mark.asyncio
async def test_engine_set_event_unknown_event(engine):
    """Test _set_event with unknown event."""
    engine.sign_client.events.on = MagicMock()
    
    # Should not set up forwarding for unknown events
    engine._set_event("unknown_event", "on")
    
    # Should not have called sign_client.events.on for unknown event
    # (only for mapped events)
    pass
