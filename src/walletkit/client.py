"""WalletKit client implementation."""
from typing import Any, Dict, Optional

from walletkit.constants.client import CLIENT_CONTEXT
from walletkit.controllers.engine import Engine
from walletkit.core import Core
from walletkit.types.client import IWalletKit, Metadata, Options, SignConfig
from walletkit.utils.decorators import handle_errors
from walletkit.utils.events import EventEmitter
from walletkit.utils.notifications import Notifications


class WalletKit(IWalletKit):
    """WalletKit client - main API for wallet integration."""
    
    # Static notifications utility
    notifications = Notifications()

    def __init__(self, opts: Options) -> None:
        """Initialize WalletKit client.
        
        Args:
            opts: Initialization options
        """
        # Initialize base class (IWalletKit doesn't have __init__ in Python ABC)
        self.metadata = opts["metadata"]
        self.name = opts.get("name") or CLIENT_CONTEXT
        self.sign_config = opts.get("signConfig")
        self.core = opts["core"]
        self.logger = self.core.logger
        self.events = EventEmitter()
        self.engine = Engine(self)
        self.notifications = Notifications()
        self._initialized = False

    @classmethod
    async def init(cls, opts: Options) -> "WalletKit":
        """Initialize WalletKit client.
        
        Args:
            opts: Initialization options
            
        Returns:
            Initialized WalletKit instance
        """
        client = cls(opts)
        await client._initialize()
        return client

    async def _initialize(self) -> None:
        """Internal initialization."""
        self.logger.info("Initializing WalletKit")
        try:
            await self.engine.init()
            self._initialized = True
            self.logger.info("WalletKit Initialization Success")
        except Exception as error:
            self.logger.error("WalletKit Initialization Failure")
            self.logger.error(str(error))
            raise

    # ---------- Events ----------------------------------------------- #

    def on(self, event: str, listener: Any) -> EventEmitter:
        """Register event listener."""
        return self.engine.on(event, listener)

    def once(self, event: str, listener: Any) -> EventEmitter:
        """Register one-time event listener."""
        return self.engine.once(event, listener)

    def off(self, event: str, listener: Any) -> EventEmitter:
        """Remove event listener."""
        return self.engine.off(event, listener)

    def remove_listener(self, event: str, listener: Any) -> EventEmitter:
        """Remove event listener."""
        return self.engine.remove_listener(event, listener)

    # ---------- Engine Methods ----------------------------------------------- #

    @handle_errors
    async def pair(self, uri: str, activate_pairing: Optional[bool] = None) -> None:
        """Pair with URI.
        
        Args:
            uri: WalletConnect URI
            activate_pairing: Optional flag to activate pairing
        """
        await self.engine.pair(uri, activate_pairing)

    @handle_errors
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
        return await self.engine.approve_session(
            id=id,
            namespaces=namespaces,
            session_properties=session_properties,
            scoped_properties=scoped_properties,
            session_config=session_config,
            relay_protocol=relay_protocol,
            proposal_requests_responses=proposal_requests_responses,
        )

    @handle_errors
    async def reject_session(self, id: int, reason: Dict[str, Any]) -> None:
        """Reject session proposal.
        
        Args:
            id: Proposal ID
            reason: Rejection reason
        """
        await self.engine.reject_session(id, reason)

    @handle_errors
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
        return await self.engine.update_session(topic, namespaces)

    @handle_errors
    async def extend_session(self, topic: str) -> Dict[str, Any]:
        """Extend session.
        
        Args:
            topic: Session topic
            
        Returns:
            Dict with 'acknowledged' callback
        """
        return await self.engine.extend_session(topic)

    @handle_errors
    async def respond_session_request(
        self, topic: str, response: Dict[str, Any]
    ) -> None:
        """Respond to session request.
        
        Args:
            topic: Session topic
            response: JSON-RPC response
        """
        await self.engine.respond_session_request(topic, response)

    @handle_errors
    async def disconnect_session(self, topic: str, reason: Dict[str, Any]) -> None:
        """Disconnect session.
        
        Args:
            topic: Session topic
            reason: Disconnect reason
        """
        await self.engine.disconnect_session(topic, reason)

    @handle_errors
    async def emit_session_event(
        self, topic: str, event: Dict[str, Any], chain_id: str
    ) -> None:
        """Emit session event.
        
        Args:
            topic: Session topic
            event: Event data
            chain_id: Chain ID
        """
        await self.engine.emit_session_event(topic, event, chain_id)

    @handle_errors
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get active sessions.
        
        Returns:
            Dict of active sessions keyed by topic
        """
        return self.engine.get_active_sessions()

    @handle_errors
    def get_pending_session_proposals(self) -> Dict[int, Any]:
        """Get pending session proposals.
        
        Returns:
            Dict of pending proposals keyed by ID
        """
        return self.engine.get_pending_session_proposals()

    @handle_errors
    def get_pending_session_requests(self) -> list[Dict[str, Any]]:
        """Get pending session requests.
        
        Returns:
            List of pending requests
        """
        return self.engine.get_pending_session_requests()

    @handle_errors
    async def register_device_token(self, params: Dict[str, Any]) -> None:
        """Register device token.
        
        Args:
            params: Device token parameters
        """
        await self.engine.register_device_token(params)

    @handle_errors
    async def approve_session_authenticate(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Approve session authentication.
        
        Args:
            params: Approval parameters
            
        Returns:
            Dict with session
        """
        return await self.engine.approve_session_authenticate(params)

    @handle_errors
    def format_auth_message(self, request: Dict[str, Any], iss: str) -> str:
        """Format auth message.
        
        Args:
            request: Auth request
            iss: Issuer
            
        Returns:
            Formatted message
        """
        return self.engine.format_auth_message(request, iss)

    @handle_errors
    async def reject_session_authenticate(
        self, id: int, reason: Dict[str, Any]
    ) -> None:
        """Reject session authentication.
        
        Args:
            id: Request ID
            reason: Rejection reason
        """
        await self.engine.reject_session_authenticate(id, reason)

