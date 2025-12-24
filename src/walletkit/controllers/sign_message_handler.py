"""Message handler for SignClient protocol messages."""
import os
from typing import Any, Dict, Optional

from walletkit.utils.jsonrpc import is_jsonrpc_response


class SignMessageHandler:
    """Handles WalletConnect Sign Protocol messages."""
    
    def __init__(self, sign_client: Any) -> None:
        """Initialize message handler.
        
        Args:
            sign_client: SignClient instance to delegate to
        """
        self.sign_client = sign_client
    
    async def handle_protocol_message(self, topic: str, payload: Dict[str, Any]) -> None:
        """Handle protocol message.
        
        Args:
            topic: Message topic
            payload: Decoded JSON-RPC payload
        """
        method = payload.get("method")
        params = payload.get("params", {})
        request_id = payload.get("id")
        
        if method == "wc_sessionPropose":
            await self._handle_session_propose(topic, params, request_id)
        elif method == "wc_sessionSettle":
            await self._handle_session_settle(topic, params, request_id)
        elif method == "wc_sessionRequest":
            await self._handle_session_request(topic, params, request_id)
        elif method == "wc_sessionUpdate":
            await self._handle_session_update(topic, params, request_id)
        elif method == "wc_sessionExtend":
            await self._handle_session_extend(topic, params, request_id)
        elif method == "wc_sessionDelete":
            await self._handle_session_delete(topic, params, request_id)
        elif method == "wc_sessionEvent":
            await self._handle_session_event(topic, params, request_id)
        elif method == "wc_sessionAuthenticate":
            await self._handle_session_authenticate(topic, params, request_id)
    
    async def _handle_session_propose(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session proposal."""
        # Delegate to SignClient method
        await self.sign_client._handle_session_propose(topic, params, request_id)
    
    async def _handle_session_settle(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session settlement."""
        await self.sign_client._handle_session_settle(topic, params, request_id)
    
    async def _handle_session_request(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session request."""
        await self.sign_client._handle_session_request(topic, params, request_id)
    
    async def _handle_session_update(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session update."""
        await self.sign_client._handle_session_update(topic, params, request_id)
    
    async def _handle_session_extend(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session extend."""
        await self.sign_client._handle_session_extend(topic, params, request_id)
    
    async def _handle_session_delete(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session delete."""
        await self.sign_client._handle_session_delete(topic, params, request_id)
    
    async def _handle_session_event(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session event."""
        await self.sign_client._handle_session_event(topic, params, request_id)
    
    async def _handle_session_authenticate(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session authenticate."""
        await self.sign_client._handle_session_authenticate(topic, params, request_id)
