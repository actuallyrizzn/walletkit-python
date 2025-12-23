"""Engine type definitions."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from walletkit.types.client import Event, EventArguments, IWalletKit


class IWalletKitEngine(ABC):
    """Abstract WalletKit Engine interface."""

    @property
    @abstractmethod
    def sign_client(self) -> Any:  # ISignClient
        """Sign client instance."""
        ...

    def __init__(self, client: IWalletKit) -> None:
        """Initialize engine with client."""
        self.client = client

    @abstractmethod
    async def init(self) -> None:
        """Initialize engine."""
        ...

    @abstractmethod
    async def pair(self, uri: str, activate_pairing: Optional[bool] = None) -> None:
        """Pair with URI."""
        ...

    @abstractmethod
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
        """Approve session proposal."""
        ...

    @abstractmethod
    async def reject_session(self, id: int, reason: Dict[str, Any]) -> None:
        """Reject session proposal."""
        ...

    @abstractmethod
    async def update_session(
        self, topic: str, namespaces: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update session."""
        ...

    @abstractmethod
    async def extend_session(self, topic: str) -> Dict[str, Any]:
        """Extend session."""
        ...

    @abstractmethod
    async def respond_session_request(
        self, topic: str, response: Dict[str, Any]
    ) -> None:
        """Respond to session request."""
        ...

    @abstractmethod
    async def disconnect_session(self, topic: str, reason: Dict[str, Any]) -> None:
        """Disconnect session."""
        ...

    @abstractmethod
    async def emit_session_event(
        self, topic: str, event: Dict[str, Any], chain_id: str
    ) -> None:
        """Emit session event."""
        ...

    @abstractmethod
    def get_active_sessions(self) -> Dict[str, Any]:
        """Get active sessions."""
        ...

    @abstractmethod
    def get_pending_session_proposals(self) -> Dict[int, Any]:
        """Get pending session proposals."""
        ...

    @abstractmethod
    def get_pending_session_requests(self) -> list[Dict[str, Any]]:
        """Get pending session requests."""
        ...

    @abstractmethod
    async def register_device_token(self, params: Dict[str, Any]) -> None:
        """Register device token."""
        ...

    @abstractmethod
    async def approve_session_authenticate(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Approve session authentication."""
        ...

    @abstractmethod
    def format_auth_message(self, request: Dict[str, Any], iss: str) -> str:
        """Format auth message."""
        ...

    @abstractmethod
    async def reject_session_authenticate(
        self, id: int, reason: Dict[str, Any]
    ) -> None:
        """Reject session authentication."""
        ...

    @abstractmethod
    def on(self, event: Event, listener: Any) -> Any:  # EventEmitter
        """Register event listener."""
        ...

    @abstractmethod
    def once(self, event: Event, listener: Any) -> Any:
        """Register one-time event listener."""
        ...

    @abstractmethod
    def off(self, event: Event, listener: Any) -> Any:
        """Remove event listener."""
        ...

    @abstractmethod
    def remove_listener(self, event: Event, listener: Any) -> Any:
        """Remove event listener."""
        ...

