"""Relayer controller implementation."""
import asyncio
import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import websockets
from websockets.client import WebSocketClientProtocol

from walletkit.exceptions import ConnectionError, ProtocolError, TimeoutError
from walletkit.types.core import ICore
from walletkit.types.logger import Logger
from walletkit.utils.events import EventEmitter
from walletkit.utils.jsonrpc import format_jsonrpc_request, get_big_int_rpc_id


class Relayer:
    """Relayer controller for WebSocket communication."""

    def __init__(
        self,
        core: ICore,
        logger: Logger,
        relay_url: Optional[str] = None,
        project_id: Optional[str] = None,
        origin: Optional[str] = None,
    ) -> None:
        """Initialize Relayer.
        
        Args:
            core: Core instance
            logger: Logger instance
            relay_url: Relay server URL
            project_id: WalletConnect project ID
            origin: Optional WebSocket Origin header value for relay handshake
        """
        self.core = core
        self.logger = logger
        self.relay_url = relay_url or "wss://relay.walletconnect.com"
        self.project_id = project_id
        self.origin = origin
        
        self.protocol = "wc"
        self.version = 2
        self.name = "relayer"
        self.events = EventEmitter()
        
        self._initialized = False
        self._websocket: Optional[WebSocketClientProtocol] = None
        self._connected = False
        self._connecting = False
        self._subscribed_topics: Dict[str, str] = {}  # topic -> subscription_id
        self._message_queue: list[Dict[str, Any]] = []
        self._pending_rpc: Dict[int, asyncio.Future] = {}
        self._receive_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 6
        self._reconnect_delay = 1.0  # Initial delay in seconds
        self._max_reconnect_delay = 30.0  # Max delay in seconds
        self._heartbeat_interval = 30.0  # Heartbeat interval in seconds
        self._heartbeat_timeout = 35.0  # Heartbeat timeout (30s + 5s buffer)
        self._last_heartbeat: Optional[float] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._should_reconnect = True

    async def init(self) -> None:
        """Initialize relayer."""
        if not self._initialized:
            self._initialized = True
            self.logger.info("Relayer initialized")

    @property
    def connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected and self._websocket is not None

    @property
    def connecting(self) -> bool:
        """Check if WebSocket is connecting."""
        return self._connecting

    async def connect(self, relay_url: Optional[str] = None) -> None:
        """Connect to relay server.
        
        Args:
            relay_url: Optional relay URL override
        """
        if self._connecting:
            return
        
        if relay_url:
            self.relay_url = relay_url
        
        self._connecting = True
        self._should_reconnect = True
        self._reconnect_attempts = 0
        
        try:
            await self._do_connect()
        except (ConnectionError, TimeoutError) as e:
            self._connecting = False
            self._connected = False
            self.logger.error(f"Failed to connect to relay: {e}")
            # Start reconnection if enabled
            if self._should_reconnect:
                await self._start_reconnect()
            raise
        except Exception as e:
            self._connecting = False
            self._connected = False
            self.logger.error(f"Unexpected error connecting to relay: {e}")
            # Start reconnection if enabled
            if self._should_reconnect:
                await self._start_reconnect()
            raise ConnectionError(f"Failed to connect to relay: {e}") from e
    
    async def _do_connect(self) -> None:
        """Perform actual connection."""
        # WalletConnect relay requires an `auth` JWT (relay-auth) + ua + projectId.
        # Follow the reference behavior of `formatRelayRpcUrl`.
        url = self.relay_url
        auth = await self.core.crypto.sign_jwt(self.relay_url)
        ua = f"{self.protocol}-{self.version}/walletkit-python"

        parsed = urlparse(url)
        qs = parse_qs(parsed.query or "")
        qs["auth"] = [auth]
        qs["ua"] = [ua]
        if self.project_id:
            qs["projectId"] = [self.project_id]

        url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                urlencode(qs, doseq=True),
                parsed.fragment,
            )
        )
        
        self.logger.info(f"Connecting to relay: {url}")
        
        # Add timeout to connection
        try:
            self._websocket = await asyncio.wait_for(
                websockets.connect(url, origin=self.origin) if self.origin else websockets.connect(url),
                timeout=10.0,  # 10 second connection timeout
            )
        except asyncio.TimeoutError as e:
            raise TimeoutError("Connection timeout") from e
        except websockets.exceptions.InvalidURI as e:
            raise ConnectionError(f"Invalid relay URL: {e}") from e
        except websockets.exceptions.InvalidHandshake as e:
            raise ConnectionError(f"WebSocket handshake failed: {e}") from e
        
        self._connected = True
        self._connecting = False
        self._reconnect_attempts = 0  # Reset on successful connection
        self._last_heartbeat = asyncio.get_event_loop().time()
        
        # Start receiving messages
        self._receive_task = asyncio.create_task(self._receive_messages())
        
        # Start heartbeat monitoring
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        
        # Process queued messages
        await self._process_message_queue()
        
        await self.events.emit("connect", {})
        self.logger.info("Connected to relay")

    async def disconnect(self) -> None:
        """Disconnect from relay server."""
        self._should_reconnect = False  # Disable reconnection
        
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None
        
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
        
        if self._websocket:
            try:
                await self._websocket.close()
            except (websockets.exceptions.ConnectionClosed, RuntimeError):
                # Connection already closed or event loop closed - ignore
                pass
            except Exception as e:
                # Log unexpected errors but don't fail disconnect
                self.logger.debug(f"Error closing WebSocket: {e}")
            self._websocket = None
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        
        self._connected = False
        await self.events.emit("disconnect", {})

    async def publish(
        self,
        topic: str,
        message: str,
        opts: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish message to topic with retry logic.
        
        Args:
            topic: Topic to publish to
            message: Message to publish (JSON string)
            opts: Optional publish options (max_retries, retry_delay)
        """
        self._check_initialized()
        
        max_retries = opts.get("max_retries", 3) if opts else 3
        retry_delay = opts.get("retry_delay", 1.0) if opts else 1.0
        
        if not self.connected:
            await self.connect()
        
        # WalletConnect relay API expects ttl/prompt/tag for publishes.
        # Defaults align with reference implementation (6 hours, prompt=false, tag=0).
        ttl = (opts or {}).get("ttl", 6 * 60 * 60)  # seconds
        prompt = (opts or {}).get("prompt", False)
        tag = (opts or {}).get("tag", 0)

        params = {"topic": topic, "message": message, "ttl": ttl, "prompt": prompt, "tag": tag}
        
        # Retry logic for publish
        last_error = None
        for attempt in range(max_retries):
            try:
                if os.getenv("WALLETKIT_WC_DEBUG") == "1":
                    self.logger.debug(f"[WC_DEBUG] irn_publish topic={topic} tag={tag} ttl={ttl} prompt={prompt}")
                await self.request("irn_publish", params)
                return  # Success
            except (ConnectionError, ProtocolError, TimeoutError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Publish failed (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {delay}s: {e}"
                    )
                    await asyncio.sleep(delay)
                    # Try to reconnect if disconnected
                    if not self.connected:
                        try:
                            await self.connect()
                        except Exception as reconnect_error:
                            self.logger.debug(f"Reconnection attempt failed: {reconnect_error}")
                            # Continue with retry loop
                            pass
            except Exception as e:
                # Unexpected error - log and re-raise immediately
                self.logger.error(f"Unexpected error during publish: {e}")
                raise
        
        # All retries failed
        self.logger.error(f"Failed to publish after {max_retries} attempts: {last_error}")
        raise last_error

    async def request(self, method: str, params: Dict[str, Any]) -> Any:
        """Send an RPC request and await the response."""
        self._check_initialized()
        if not self.connected:
            await self.connect()
        # request() requires a live websocket because it waits for a response.
        # If we don't have one, fail fast to avoid hanging until timeout.
        if not self._websocket:
            raise ConnectionError("WebSocket not available")

        req = format_jsonrpc_request(method=method, params=params)
        req_id = req.get("id")
        if not isinstance(req_id, int):
            # get_big_int_rpc_id should return an int; be strict so we can map responses
            raise ValueError(f"Invalid request id: {req_id}")

        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_rpc[req_id] = fut

        await self._send(req)

        try:
            payload = await asyncio.wait_for(fut, timeout=15.0)
        finally:
            self._pending_rpc.pop(req_id, None)

        if isinstance(payload, dict) and payload.get("error"):
            raise RuntimeError(payload["error"])
        return payload.get("result") if isinstance(payload, dict) else payload

    async def subscribe(
        self,
        topic: str,
        opts: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Subscribe to topic.
        
        Args:
            topic: Topic to subscribe to
            opts: Optional subscribe options
            
        Returns:
            Subscription ID
        """
        self._check_initialized()
        
        if not self.connected:
            await self.connect()
        
        # Check if already subscribed
        if topic in self._subscribed_topics:
            return self._subscribed_topics[topic]
        
        # Await subscription response so we can surface relay errors and be sure we're subscribed.
        sub_id = await self.request("irn_subscribe", {"topic": topic})
        self._subscribed_topics[topic] = str(sub_id) if sub_id is not None else str(get_big_int_rpc_id())
        
        # Fire-and-forget event emission
        asyncio.create_task(self.events.emit("subscribe", {"topic": topic, "id": self._subscribed_topics[topic]}))
        
        return self._subscribed_topics[topic]

    async def unsubscribe(
        self,
        topic: str,
        opts: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Unsubscribe from topic.
        
        Args:
            topic: Topic to unsubscribe from
            opts: Optional unsubscribe options
        """
        self._check_initialized()
        
        if topic not in self._subscribed_topics:
            return
        
        subscription_id = self._subscribed_topics[topic]
        
        await self.request("irn_unsubscribe", {"id": subscription_id, "topic": topic})
        
        del self._subscribed_topics[topic]
        # Fire-and-forget event emission
        asyncio.create_task(self.events.emit("unsubscribe", {"topic": topic}))

    async def _send(self, payload: Dict[str, Any]) -> None:
        """Send message through WebSocket with timeout.
        
        Args:
            payload: JSON-RPC payload
        """
        if not self._websocket:
            # Queue message if not connected
            self._message_queue.append(payload)
            return
        
        try:
            message = json.dumps(payload)
            # Add timeout to send operation
            await asyncio.wait_for(
                self._websocket.send(message),
                timeout=5.0,  # 5 second send timeout
            )
            self._last_heartbeat = asyncio.get_event_loop().time()
        except asyncio.TimeoutError as e:
            self.logger.error("Send timeout")
            self._message_queue.append(payload)
            raise TimeoutError("Send operation timed out") from e
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.error(f"Connection closed while sending: {e}")
            self._message_queue.append(payload)
            raise ConnectionError("WebSocket connection closed") from e
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            # Queue message for retry
            self._message_queue.append(payload)
            raise ConnectionError(f"Failed to send message: {e}") from e

    async def _receive_messages(self) -> None:
        """Receive messages from WebSocket."""
        if not self._websocket:
            return
        
        try:
            async for message in self._websocket:
                try:
                    # Any inbound frame indicates the connection is alive
                    self._last_heartbeat = asyncio.get_event_loop().time()
                    payload = json.loads(message)
                    await self._handle_message(payload)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse message: {e}")
                    # Continue processing other messages
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}", exc_info=True)
                    # Continue processing other messages
        except websockets.exceptions.ConnectionClosed as e:
            self._connected = False
            self.logger.info(f"WebSocket connection closed: {e}")
            await self.events.emit("disconnect", {})
            # Start reconnection if enabled
            if self._should_reconnect:
                await self._start_reconnect()
        except Exception as e:
            self.logger.error(f"Error receiving messages: {e}", exc_info=True)
            self._connected = False
            # Start reconnection if enabled
            if self._should_reconnect:
                await self._start_reconnect()

    async def _handle_message(self, payload: Dict[str, Any]) -> None:
        """Handle incoming message.
        
        Args:
            payload: JSON-RPC payload
        """
        # Handle subscription confirmation
        if payload.get("method") == "irn_subscription":
            params = payload.get("params", {})
            topic = params.get("data", {}).get("topic")
            message = params.get("data", {}).get("message")
            if os.getenv("WALLETKIT_WC_DEBUG") == "1":
                try:
                    data = params.get("data", {}) or {}
                    if isinstance(data, dict):
                        meta = {k: data.get(k) for k in ["topic", "tag", "publishedAt"] if k in data}
                        self.logger.debug(f"[WC_DEBUG] irn_subscription meta={meta}")
                except Exception as e:
                    # Debug logging errors should not break protocol flow
                    self.logger.debug(f"Error in debug logging: {e}")
                    pass
            
            if topic and message:
                # Fire-and-forget event emission
                asyncio.create_task(self.events.emit(
                    "message",
                    {
                        "topic": topic,
                        "message": message,
                    },
                ))
        
        # Handle other message types
        elif payload.get("id"):
            # Response to our request
            try:
                req_id = int(payload.get("id"))
                fut = self._pending_rpc.get(req_id)
                if fut and not fut.done():
                    fut.set_result(payload)
            except (ValueError, TypeError, KeyError) as e:
                # Invalid request ID format - log but continue
                self.logger.debug(f"Invalid request ID in response: {e}")
                pass
            # Fire-and-forget event emission
            asyncio.create_task(self.events.emit("response", payload))

    async def _process_message_queue(self) -> None:
        """Process queued messages."""
        while self._message_queue:
            message = self._message_queue.pop(0)
            try:
                await self._send(message)
            except (ConnectionError, TimeoutError) as e:
                self.logger.warning(f"Failed to send queued message: {e}")
                # Re-queue for retry
                self._message_queue.insert(0, message)
                break
            except Exception as e:
                self.logger.error(f"Unexpected error sending queued message: {e}")
                # Re-queue for retry
                self._message_queue.insert(0, message)
                break

    async def _start_reconnect(self) -> None:
        """Start reconnection process with exponential backoff."""
        if self._reconnect_task and not self._reconnect_task.done():
            return  # Already reconnecting
        
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())
    
    async def _reconnect_loop(self) -> None:
        """Reconnection loop with exponential backoff."""
        while self._should_reconnect and self._reconnect_attempts < self._max_reconnect_attempts:
            if self._connected:
                break  # Already connected
            
            # Calculate delay with exponential backoff
            delay = min(
                self._reconnect_delay * (2 ** self._reconnect_attempts),
                self._max_reconnect_delay
            )
            
            self.logger.info(
                f"Reconnecting in {delay}s (attempt {self._reconnect_attempts + 1}/{self._max_reconnect_attempts})"
            )
            await asyncio.sleep(delay)
            
            self._reconnect_attempts += 1
            
            try:
                await self._do_connect()
                self.logger.info("Reconnection successful")
                break
            except (ConnectionError, TimeoutError) as e:
                self.logger.warning(f"Reconnection attempt {self._reconnect_attempts} failed: {e}")
                if self._reconnect_attempts >= self._max_reconnect_attempts:
                    self.logger.error("Max reconnection attempts reached")
                    await self.events.emit("reconnect_failed", {
                        "attempts": self._reconnect_attempts,
                    })
            except Exception as e:
                self.logger.error(f"Unexpected error during reconnection: {e}", exc_info=True)
                if self._reconnect_attempts >= self._max_reconnect_attempts:
                    self.logger.error("Max reconnection attempts reached")
                    await self.events.emit("reconnect_failed", {
                        "attempts": self._reconnect_attempts,
                    })
    
    async def _heartbeat_monitor(self) -> None:
        """Monitor connection health with heartbeat."""
        while self._connected and self._should_reconnect:
            try:
                await asyncio.sleep(self._heartbeat_interval)
                
                if not self._connected:
                    break

                # Actively keep the WS alive (relay may not send frames unless there's traffic).
                if self._websocket:
                    try:
                        pong_waiter = await self._websocket.ping()
                        await asyncio.wait_for(pong_waiter, timeout=10.0)
                        self._last_heartbeat = asyncio.get_event_loop().time()
                    except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
                        # fall back to timeout check below
                        pass
                    except Exception as e:
                        # Log unexpected errors but continue with timeout check
                        self.logger.debug(f"Error in heartbeat ping: {e}")
                        pass
                
                current_time = asyncio.get_event_loop().time()
                if self._last_heartbeat:
                    time_since_heartbeat = current_time - self._last_heartbeat
                    if time_since_heartbeat > self._heartbeat_timeout:
                        self.logger.warning("Heartbeat timeout, disconnecting")
                        self._connected = False
                        if self._websocket:
                            try:
                                await self._websocket.close()
                            except (websockets.exceptions.ConnectionClosed, RuntimeError):
                                # Connection already closed or event loop closed
                                pass
                            except Exception as e:
                                self.logger.debug(f"Error closing WebSocket during heartbeat timeout: {e}")
                            self._websocket = None
                        await self.events.emit("disconnect", {})
                        if self._should_reconnect:
                            await self._start_reconnect()
                        break
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in heartbeat monitor: {e}", exc_info=True)
    
    def _check_initialized(self) -> None:
        """Check if relayer is initialized."""
        if not self._initialized:
            raise RuntimeError("Relayer not initialized. Call init() first.")

    def on(self, event: str, listener: Any) -> EventEmitter:
        """Register event listener."""
        return self.events.on(event, listener)

    def once(self, event: str, listener: Any) -> EventEmitter:
        """Register one-time event listener."""
        return self.events.once(event, listener)

    def off(self, event: str, listener: Any) -> EventEmitter:
        """Remove event listener."""
        return self.events.off(event, listener)

