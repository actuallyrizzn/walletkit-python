"""Engine controller implementation."""
from typing import Any, Dict, Optional

from walletkit.controllers.sign_client import SignClient
from walletkit.types.client import Event, EventArguments, IWalletKit
from walletkit.types.engine import IWalletKitEngine


class Engine(IWalletKitEngine):
    """Engine controller wrapping SignClient."""

    def __init__(self, client: IWalletKit) -> None:
        """Initialize Engine.
        
        Args:
            client: WalletKit client instance
        """
        super().__init__(client)
        self.sign_client: Optional[SignClient] = None

    async def init(self) -> None:
        """Initialize engine and SignClient."""
        self.sign_client = await SignClient.init(
            core=self.client.core,
            metadata=self.client.metadata,
            sign_config=self.client.sign_config,
        )
        
        # Initialize event client if available
        if hasattr(self.client.core, "event_client") and self.client.core.event_client:
            try:
                await self.client.core.event_client.init()
            except Exception as error:
                self.client.logger.warn(str(error))

    async def pair(self, uri: str, activate_pairing: Optional[bool] = None) -> None:
        """Pair with URI.
        
        Args:
            uri: WalletConnect URI
            activate_pairing: Optional flag to activate pairing
        """
        await self.client.core.pairing.pair({"uri": uri})

    async def approve_session(
        self,
        id: int,
        namespaces: Dict[str, Any],
        session_properties: Optional[Dict[str, Any]] = None,
        scoped_properties: Optional[Dict[str, Any]] = None,
        session_config: Optional[Dict[str, Any]] = None,
        relay_protocol: Optional[str] = None,
        proposal_requests_responses: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Approve session proposal.
        
        Args:
            id: Proposal ID
            namespaces: Session namespaces
            session_properties: Optional session properties
            scoped_properties: Optional scoped properties
            session_config: Optional session config
            relay_protocol: Optional relay protocol
            proposal_requests_responses: Optional proposal request responses
            
        Returns:
            Session struct
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        result = await self.sign_client.approve({
            "id": id,
            "namespaces": namespaces,
            "sessionProperties": session_properties,
            "scopedProperties": scoped_properties,
            "sessionConfig": session_config,
            "relayProtocol": relay_protocol,
            "proposalRequestsResponses": proposal_requests_responses,
        })
        
        await result["acknowledged"]()
        topic = result["topic"]
        
        # Get session (placeholder - will use proper store later)
        return self.sign_client.session.get(topic, {})

    async def reject_session(self, id: int, reason: Dict[str, Any]) -> None:
        """Reject session proposal.
        
        Args:
            id: Proposal ID
            reason: Rejection reason
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        await self.sign_client.reject({"id": id, "reason": reason})

    async def update_session(
        self, topic: str, namespaces: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update session.
        
        Args:
            topic: Session topic
            namespaces: Updated namespaces
            
        Returns:
            Dict with 'acknowledged' callback
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        return await self.sign_client.update({"topic": topic, "namespaces": namespaces})

    async def extend_session(self, topic: str) -> Dict[str, Any]:
        """Extend session.
        
        Args:
            topic: Session topic
            
        Returns:
            Dict with 'acknowledged' callback
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        return await self.sign_client.extend({"topic": topic})

    async def respond_session_request(
        self, topic: str, response: Dict[str, Any]
    ) -> None:
        """Respond to session request.
        
        Args:
            topic: Session topic
            response: JSON-RPC response
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        await self.sign_client.respond({"topic": topic, "response": response})

    async def disconnect_session(self, topic: str, reason: Dict[str, Any]) -> None:
        """Disconnect session.
        
        Args:
            topic: Session topic
            reason: Disconnect reason
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        await self.sign_client.disconnect({"topic": topic, "reason": reason})

    async def emit_session_event(
        self, topic: str, event: Dict[str, Any], chain_id: str
    ) -> None:
        """Emit session event.
        
        Args:
            topic: Session topic
            event: Event data
            chain_id: Chain ID
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        await self.sign_client.emit({"topic": topic, "event": event, "chainId": chain_id})

    def get_active_sessions(self) -> Dict[str, Any]:
        """Get active sessions.
        
        Returns:
            Dict of active sessions keyed by topic
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        # Get all sessions from store
        sessions = self.sign_client.session.values
        return {session.get("topic", ""): session for session in sessions}

    def get_pending_session_proposals(self) -> Dict[int, Any]:
        """Get pending session proposals.
        
        Returns:
            Dict of pending proposals keyed by ID
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        proposals = self.sign_client.proposal.values
        return {proposal.get("id", 0): proposal for proposal in proposals}

    def get_pending_session_requests(self) -> list[Dict[str, Any]]:
        """Get pending session requests.
        
        Returns:
            List of pending requests
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        return self.sign_client.get_pending_session_requests()

    async def register_device_token(self, params: Dict[str, Any]) -> None:
        """Register device token.
        
        Args:
            params: Device token parameters
        """
        if hasattr(self.client.core, "echo_client") and self.client.core.echo_client:
            await self.client.core.echo_client.register_device_token(params)
        else:
            raise NotImplementedError("EchoClient not available")

    async def approve_session_authenticate(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Approve session authentication.
        
        Args:
            params: Approval parameters
            
        Returns:
            Dict with session
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        return await self.sign_client.approve_session_authenticate(params)

    async def reject_session_authenticate(
        self, id: int, reason: Dict[str, Any]
    ) -> None:
        """Reject session authentication.
        
        Args:
            id: Request ID
            reason: Rejection reason
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        await self.sign_client.reject_session_authenticate({"id": id, "reason": reason})

    def format_auth_message(self, request: Dict[str, Any], iss: str) -> str:
        """Format auth message.
        
        Args:
            request: Auth request
            iss: Issuer
            
        Returns:
            Formatted message
        """
        if not self.sign_client:
            raise RuntimeError("Engine not initialized. Call init() first.")
        
        return self.sign_client.format_auth_message({"request": request, "iss": iss})

    # ---------- Event Handlers ----------------------------------------------- #

    def on(self, event: Event, listener: Any) -> Any:  # EventEmitter
        """Register event listener."""
        self._set_event(event, "off")
        self._set_event(event, "on")
        return self.client.events.on(event, listener)

    def once(self, event: Event, listener: Any) -> Any:
        """Register one-time event listener."""
        self._set_event(event, "off")
        self._set_event(event, "once")
        return self.client.events.once(event, listener)

    def off(self, event: Event, listener: Any) -> Any:
        """Remove event listener."""
        self._set_event(event, "off")
        return self.client.events.off(event, listener)

    def remove_listener(self, event: Event, listener: Any) -> Any:
        """Remove event listener."""
        self._set_event(event, "removeListener")
        return self.client.events.remove_listener(event, listener)

    # ---------- Private ----------------------------------------------- #

    def _on_session_request(self, event: Dict[str, Any]) -> None:
        """Handle session request event."""
        self.client.events.emit("session_request", event)

    def _on_session_proposal(self, event: Dict[str, Any]) -> None:
        """Handle session proposal event."""
        self.client.events.emit("session_proposal", event)

    def _on_session_delete(self, event: Dict[str, Any]) -> None:
        """Handle session delete event."""
        self.client.events.emit("session_delete", event)

    def _on_proposal_expire(self, event: Dict[str, Any]) -> None:
        """Handle proposal expire event."""
        self.client.events.emit("proposal_expire", event)

    def _on_session_request_expire(self, event: Dict[str, Any]) -> None:
        """Handle session request expire event."""
        self.client.events.emit("session_request_expire", event)

    def _on_session_authenticate(self, event: Dict[str, Any]) -> None:
        """Handle session authenticate event."""
        self.client.events.emit("session_authenticate", event)

    def _set_event(
        self, event: Event, action: str
    ) -> None:  # "on" | "off" | "once" | "removeListener"
        """Set up event forwarding from SignClient to WalletKit."""
        if not self.sign_client:
            return
        
        event_map = {
            "session_request": (self._on_session_request,),
            "session_proposal": (self._on_session_proposal,),
            "session_delete": (self._on_session_delete,),
            "proposal_expire": (self._on_proposal_expire,),
            "session_request_expire": (self._on_session_request_expire,),
            "session_authenticate": (self._on_session_authenticate,),
        }
        
        if event in event_map:
            handler = event_map[event][0]
            if action == "on":
                self.sign_client.events.on(event, handler)
            elif action == "off":
                self.sign_client.events.off(event, handler)
            elif action == "once":
                self.sign_client.events.once(event, handler)
            elif action == "removeListener":
                self.sign_client.events.remove_listener(event, handler)

