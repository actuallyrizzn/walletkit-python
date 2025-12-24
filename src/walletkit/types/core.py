"""Core type definitions."""
from typing import TYPE_CHECKING, Optional, Protocol

from walletkit.types.logger import Logger
from walletkit.utils.events import EventEmitter
from walletkit.utils.storage import IKeyValueStorage

if TYPE_CHECKING:
    from walletkit.controllers.crypto import Crypto
    from walletkit.controllers.echo_client import EchoClient
    from walletkit.controllers.event_client import EventClient
    from walletkit.controllers.expirer import Expirer
    from walletkit.controllers.pairing import Pairing
    from walletkit.controllers.relayer import Relayer


class ICore(Protocol):
    """Core interface protocol.
    
    This protocol defines the interface that Core implementations must satisfy.
    It provides access to all controllers and core configuration.
    """

    # Configuration attributes
    protocol: str
    version: int
    project_id: Optional[str]
    relay_url: str
    relay_origin: Optional[str]
    storage: IKeyValueStorage
    logger: Logger
    storage_prefix: str
    events: EventEmitter

    # Controllers
    crypto: "Crypto"
    relayer: "Relayer"
    expirer: "Expirer"
    event_client: "EventClient"
    echo_client: "EchoClient"
    pairing: "Pairing"

    # Methods
    async def start(self) -> None:
        """Start Core (initialize all subsystems)."""
        ...
