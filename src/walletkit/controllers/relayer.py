"""Relayer controller implementation."""
import asyncio
import json
from typing import Any, Dict, Optional

import websockets
from websockets.client import WebSocketClientProtocol

from walletkit.utils.events import EventEmitter
from walletkit.utils.jsonrpc import format_jsonrpc_request, get_big_int_rpc_id


class Relayer:
    """Relayer controller for WebSocket communication."""

    def __init__(
        self,
        core: Any,  # ICore
        logger: Any,  # Logger
        relay_url: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> None:
        """Initialize Relayer.
        
        Args:
            core: Core instance
            logger: Logger instance
            relay_url: Relay server URL
            project_id: WalletConnect project ID
        """
        self.core = core
        self.logger = logger
        self.relay_url = relay_url or "wss://relay.walletconnect.com"
        self.project_id = project_id
        
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
        self._receive_task: Optional[asyncio.Task] = None

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
        
        try:
            # Format relay URL with project ID if available
            url = self.relay_url
            if self.project_id:
                url = f"{url}?projectId={self.project_id}"
            
            self.logger.info(f"Connecting to relay: {url}")
            self._websocket = await websockets.connect(url)
            self._connected = True
            self._connecting = False
            
            # Start receiving messages
            self._receive_task = asyncio.create_task(self._receive_messages())
            
            # Process queued messages
            await self._process_message_queue()
            
            self.events.emit("connect", {})
            self.logger.info("Connected to relay")
        except Exception as e:
            self._connecting = False
            self._connected = False
            self.logger.error(f"Failed to connect to relay: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from relay server."""
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        
        self._connected = False
        self.events.emit("disconnect", {})

    async def publish(
        self,
        topic: str,
        message: str,
        opts: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Publish message to topic.
        
        Args:
            topic: Topic to publish to
            message: Message to publish (JSON string)
            opts: Optional publish options
        """
        self._check_initialized()
        
        if not self.connected:
            await self.connect()
        
        payload = {
            "method": "irn_publish",
            "params": {
                "topic": topic,
                "message": message,
            },
        }
        
        request = format_jsonrpc_request(
            method=payload["method"],
            params=payload["params"],
        )
        
        await self._send(request)

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
        
        request_id = str(get_big_int_rpc_id())
        payload = {
            "method": "irn_subscribe",
            "params": {
                "topic": topic,
            },
        }
        
        request = format_jsonrpc_request(
            method=payload["method"],
            params=payload["params"],
            request_id=request_id,
        )
        
        await self._send(request)
        
        # Store subscription
        self._subscribed_topics[topic] = request_id
        
        self.events.emit("subscribe", {"topic": topic, "id": request_id})
        
        return request_id

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
        
        payload = {
            "method": "irn_unsubscribe",
            "params": {
                "id": subscription_id,
                "topic": topic,
            },
        }
        
        request = format_jsonrpc_request(
            method=payload["method"],
            params=payload["params"],
        )
        
        await self._send(request)
        
        del self._subscribed_topics[topic]
        self.events.emit("unsubscribe", {"topic": topic})

    async def _send(self, payload: Dict[str, Any]) -> None:
        """Send message through WebSocket.
        
        Args:
            payload: JSON-RPC payload
        """
        if not self._websocket:
            # Queue message if not connected
            self._message_queue.append(payload)
            return
        
        try:
            message = json.dumps(payload)
            await self._websocket.send(message)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            # Queue message for retry
            self._message_queue.append(payload)
            raise

    async def _receive_messages(self) -> None:
        """Receive messages from WebSocket."""
        if not self._websocket:
            return
        
        try:
            async for message in self._websocket:
                try:
                    payload = json.loads(message)
                    await self._handle_message(payload)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    self.logger.error(f"Error handling message: {e}")
        except websockets.exceptions.ConnectionClosed:
            self._connected = False
            self.events.emit("disconnect", {})
        except Exception as e:
            self.logger.error(f"Error receiving messages: {e}")
            self._connected = False

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
            
            if topic and message:
                self.events.emit(
                    "message",
                    {
                        "topic": topic,
                        "message": message,
                    },
                )
        
        # Handle other message types
        elif payload.get("id"):
            # Response to our request
            self.events.emit("response", payload)

    async def _process_message_queue(self) -> None:
        """Process queued messages."""
        while self._message_queue:
            message = self._message_queue.pop(0)
            try:
                await self._send(message)
            except Exception as e:
                self.logger.error(f"Failed to send queued message: {e}")
                # Re-queue for retry
                self._message_queue.insert(0, message)
                break

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

