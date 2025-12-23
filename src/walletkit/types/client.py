"""Client type definitions."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Literal, Optional, Protocol, TypedDict

from walletkit.utils.events import EventEmitter

# Event types
Event = Literal[
    "session_proposal",
    "session_request",
    "session_delete",
    "proposal_expire",
    "session_request_expire",
    "session_authenticate",
]


class BaseEventArgs(TypedDict, total=False):
    """Base event arguments."""

    id: int
    topic: str
    params: Any


class ProposalExpire(TypedDict):
    """Proposal expire event."""

    id: int


class SessionRequestExpire(TypedDict):
    """Session request expire event."""

    id: int


# Type aliases for complex types (will be defined more fully later)
SessionRequest = Dict[str, Any]  # TODO: Define properly
SessionProposal = Dict[str, Any]  # TODO: Define properly
SessionDelete = Dict[str, Any]  # TODO: Define properly
SessionAuthenticate = Dict[str, Any]  # TODO: Define properly
SignConfig = Optional[Dict[str, Any]]  # TODO: Define properly
Metadata = Dict[str, Any]  # TODO: Define properly


class EventArguments(TypedDict, total=False):
    """Event arguments mapping."""

    session_proposal: SessionProposal
    session_request: SessionRequest
    session_delete: SessionDelete
    proposal_expire: ProposalExpire
    session_request_expire: SessionRequestExpire
    session_authenticate: SessionAuthenticate


class Options(TypedDict, total=False):
    """WalletKit initialization options."""

    core: Any  # ICore - will define properly later
    metadata: Metadata
    name: Optional[str]
    signConfig: Optional[SignConfig]


class INotifications(Protocol):
    """Notifications interface."""

    async def decrypt_message(
        self,
        topic: str,
        encrypted_message: str,
        storage_options: Optional[Dict[str, Any]] = None,
        storage: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Decrypt a message."""
        ...

    async def get_metadata(
        self,
        topic: str,
        storage_options: Optional[Dict[str, Any]] = None,
        storage: Optional[Any] = None,
    ) -> Metadata:
        """Get session metadata."""
        ...


class IWalletKit(ABC):
    """Abstract WalletKit interface."""

    name: str  # Not a property, just an attribute
    engine: Any  # IWalletKitEngine
    events: EventEmitter
    logger: Any  # Logger
    core: Any  # ICore
    metadata: Metadata
    sign_config: Optional[SignConfig]

    def __init__(self, opts: Options) -> None:
        """Initialize with options."""
        # Base class doesn't need to do anything
        pass

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
    async def update_session(self, topic: str, namespaces: Dict[str, Any]) -> Dict[str, Any]:
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
    def on(
        self, event: Event, listener: Any
    ) -> EventEmitter:  # TODO: Proper type for listener
        """Register event listener."""
        ...

    @abstractmethod
    def once(self, event: Event, listener: Any) -> EventEmitter:
        """Register one-time event listener."""
        ...

    @abstractmethod
    def off(self, event: Event, listener: Any) -> EventEmitter:
        """Remove event listener."""
        ...

    @abstractmethod
    def remove_listener(self, event: Event, listener: Any) -> EventEmitter:
        """Remove event listener."""
        ...

