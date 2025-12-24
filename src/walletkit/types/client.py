"""Client type definitions."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Literal, Optional, Protocol, TypedDict

from walletkit.types.core import ICore
from walletkit.types.logger import Logger
from walletkit.utils.events import EventEmitter

# Re-export for backward compatibility
__all__ = [
    "BaseEventArgs",
    "Event",
    "EventArguments",
    "IWalletKit",
    "INotifications",
    "Metadata",
    "Options",
    "ProposalExpire",
    "ProposalParams",
    "RequestParams",
    "AuthParams",
    "SessionAuthenticate",
    "SessionDelete",
    "SessionProposal",
    "SessionRequest",
    "SessionRequestExpire",
    "SignConfig",
]

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


# TypedDict definitions for WalletConnect protocol types


class Metadata(TypedDict):
    """Wallet/DApp metadata following WalletConnect spec."""

    name: str
    description: str
    url: str
    icons: list[str]


class ProposalParams(TypedDict, total=False):
    """Session proposal parameters."""

    id: int
    proposer: Dict[str, Any]
    requiredNamespaces: Dict[str, Any]
    optionalNamespaces: Optional[Dict[str, Any]]
    relays: list[Dict[str, Any]]
    pairingTopic: Optional[str]


class SessionProposal(TypedDict, total=False):
    """Session proposal event data."""

    id: int
    topic: str
    params: ProposalParams


class RequestParams(TypedDict, total=False):
    """Session request parameters."""

    request: Dict[str, Any]
    chainId: Optional[str]


class SessionRequest(TypedDict, total=False):
    """Session request event data."""

    id: int
    topic: str
    params: RequestParams


class SessionDelete(TypedDict, total=False):
    """Session delete event data."""

    id: int
    topic: str


class AuthParams(TypedDict, total=False):
    """Session authenticate parameters."""

    requester: Dict[str, Any]
    authPayload: Dict[str, Any]
    cached: Optional[bool]


class SessionAuthenticate(TypedDict, total=False):
    """Session authenticate event data."""

    id: int
    topic: str
    params: AuthParams


class SignConfig(TypedDict, total=False):
    """Sign configuration options.
    
    Note: This TypedDict allows additional fields beyond those defined here.
    Use Dict[str, Any] for full flexibility if needed.
    """

    disableRequestQueue: Optional[bool]
    maxRequestQueueSize: Optional[int]
    requestTimeout: Optional[int]


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

    core: ICore
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
    logger: Logger
    core: ICore
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

