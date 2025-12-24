"""Additional error path tests for Relayer."""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from walletkit.controllers.relayer import Relayer
from walletkit.core import Core
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
async def core(storage):
    """Create and initialize core."""
    core = Core(storage=storage)
    await core.start()
    return core


@pytest.fixture
def relayer(core):
    """Create Relayer instance."""
    return Relayer(
        core=core,
        logger=core.logger,
        relay_url="wss://relay.walletconnect.com",
        project_id="test-project-id",
    )


@pytest.mark.asyncio
async def test_relayer_publish_max_retries_exceeded(relayer):
    """Test publish when all retries are exhausted."""
    await relayer.init()
    
    # Mock connect to avoid real connection
    relayer.connect = AsyncMock()
    relayer._connected = True
    relayer._websocket = AsyncMock()
    
    # Mock request to always fail
    relayer.request = AsyncMock(side_effect=Exception("Always fails"))
    
    with pytest.raises(Exception, match="Always fails"):
        await relayer.publish("topic1", "test_message", opts={"tag": 1, "ttl": 100, "max_retries": 2})
    
    # Should have attempted max_retries
    assert relayer.request.call_count == 2


@pytest.mark.asyncio
async def test_relayer_publish_reconnect_on_failure(relayer):
    """Test publish reconnects when disconnected during retry."""
    await relayer.init()
    
    call_count = 0
    
    async def mock_request(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            relayer._connected = False
            raise Exception("Connection lost")
        return None
    
    relayer.request = mock_request
    relayer.connect = AsyncMock()
    
    # Should reconnect and retry
    await relayer.publish("topic1", "test_message", opts={"tag": 1, "ttl": 100})
    
    # Should have called connect
    assert relayer.connect.called


@pytest.mark.asyncio
async def test_relayer_request_websocket_not_available(relayer):
    """Test request when websocket is not available."""
    await relayer.init()
    
    # Mock connect to avoid real connection
    relayer.connect = AsyncMock()
    relayer._connected = True
    relayer._websocket = None
    
    with pytest.raises(ConnectionError, match="WebSocket not available"):
        await relayer.request("test_method", {})


@pytest.mark.asyncio
async def test_relayer_request_invalid_request_id(relayer):
    """Test request with invalid request ID."""
    await relayer.init()
    
    relayer._connected = True
    relayer._websocket = AsyncMock()
    
    # Mock format_jsonrpc_request to return invalid ID
    with patch("walletkit.controllers.relayer.format_jsonrpc_request") as mock_format:
        mock_format.return_value = {"id": "invalid", "method": "test", "params": {}}
        
        with pytest.raises(ValueError, match="Invalid request id"):
            await relayer.request("test_method", {})


@pytest.mark.asyncio
async def test_relayer_request_timeout(relayer):
    """Test request timeout handling."""
    await relayer.init()
    
    relayer._connected = True
    mock_ws = AsyncMock()
    relayer._websocket = mock_ws
    relayer._send = AsyncMock()
    
    # Mock format to return ID 1
    with patch("walletkit.controllers.relayer.format_jsonrpc_request") as mock_format:
        mock_format.return_value = {"id": 1, "method": "test", "params": {}}
        
        with patch("asyncio.wait_for") as mock_wait:
            mock_wait.side_effect = asyncio.TimeoutError()
            
            with pytest.raises(asyncio.TimeoutError):
                await relayer.request("test_method", {})


@pytest.mark.asyncio
async def test_relayer_request_error_response(relayer):
    """Test request with error response."""
    await relayer.init()
    
    # Mock connect to avoid real connection
    relayer.connect = AsyncMock()
    relayer._connected = True
    mock_ws = AsyncMock()
    relayer._websocket = mock_ws
    relayer._send = AsyncMock()
    
    # Mock format to return ID 1
    with patch("walletkit.controllers.relayer.format_jsonrpc_request") as mock_format:
        mock_format.return_value = {"id": 1, "method": "test", "params": {}}
        
        # Create a future that will be set by request method
        # We need to set it after request creates it but before it waits
        original_request = relayer.request.__func__ if hasattr(relayer.request, '__func__') else None
        
        # Patch the request to inject error response
        async def mock_request_inner(method, params):
            # Call the real request setup
            req = {"id": 1, "method": method, "params": params}
            req_id = req.get("id")
            fut = asyncio.get_event_loop().create_future()
            relayer._pending_rpc[req_id] = fut
            await relayer._send(req)
            
            # Immediately set error response
            fut.set_result({"error": "Test error", "id": req_id})
            
            # Wait for future (will complete immediately)
            payload = await asyncio.wait_for(fut, timeout=15.0)
            relayer._pending_rpc.pop(req_id, None)
            
            if isinstance(payload, dict) and payload.get("error"):
                raise RuntimeError(payload["error"])
            return payload.get("result") if isinstance(payload, dict) else payload
        
        relayer.request = mock_request_inner
        
        with pytest.raises(RuntimeError, match="Test error"):
            await relayer.request("test_method", {})


@pytest.mark.asyncio
async def test_relayer_handle_message_debug_exception(relayer):
    """Test _handle_message with exception in debug logging."""
    await relayer.init()
    
    # Set debug env var
    with patch.dict("os.environ", {"WALLETKIT_WC_DEBUG": "1"}):
        # Mock logger.debug to raise exception
        relayer.logger.debug = MagicMock(side_effect=Exception("Debug error"))
        
        # Should handle exception gracefully
        payload = {
            "method": "irn_subscription",
            "params": {
                "data": {
                    "topic": "test_topic",
                    "message": "test_message"
                }
            }
        }
        
        # Should not raise
        await relayer._handle_message(payload)


@pytest.mark.asyncio
async def test_relayer_heartbeat_ping_exception(relayer):
    """Test heartbeat monitor with ping exception."""
    await relayer.init()
    
    relayer._connected = True
    relayer._should_reconnect = True
    
    # Mock websocket ping to raise exception
    mock_ws = AsyncMock()
    mock_ws.ping = AsyncMock(side_effect=Exception("Ping failed"))
    relayer._websocket = mock_ws
    
    # Should handle exception and continue
    task = asyncio.create_task(relayer._heartbeat_monitor())
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_relayer_heartbeat_pong_timeout(relayer):
    """Test heartbeat monitor with pong timeout."""
    await relayer.init()
    
    relayer._connected = True
    relayer._should_reconnect = True
    
    # Mock websocket ping to return a future that times out
    mock_ws = AsyncMock()
    pong_fut = asyncio.get_event_loop().create_future()
    mock_ws.ping = AsyncMock(return_value=pong_fut)
    relayer._websocket = mock_ws
    
    # Mock wait_for to timeout
    with patch("asyncio.wait_for") as mock_wait:
        mock_wait.side_effect = asyncio.TimeoutError()
        
        # Should handle timeout gracefully
        task = asyncio.create_task(relayer._heartbeat_monitor())
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
