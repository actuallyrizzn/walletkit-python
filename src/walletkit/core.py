"""Core WalletConnect implementation."""
from typing import Any, Optional

from walletkit.controllers.crypto import Crypto
from walletkit.controllers.echo_client import EchoClient
from walletkit.controllers.event_client import EventClient
from walletkit.controllers.expirer import Expirer
from walletkit.controllers.keychain import KeyChain
from walletkit.utils.events import EventEmitter
from walletkit.utils.storage import IKeyValueStorage, MemoryStorage


class Core:
    """Core WalletConnect protocol implementation."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        relay_url: Optional[str] = None,
        relay_origin: Optional[str] = None,
        storage: Optional[IKeyValueStorage] = None,
        logger: Any = None,  # Logger
        storage_prefix: str = "wc@2:core:",
    ) -> None:
        """Initialize Core.
        
        Args:
            project_id: WalletConnect project ID
            relay_url: Relay server URL
            relay_origin: Optional Origin header value to send during WebSocket handshake
            storage: Storage backend (defaults to MemoryStorage)
            logger: Logger instance
            storage_prefix: Storage key prefix
        """
        self.protocol = "wc"
        self.version = 2
        self.project_id = project_id
        self.relay_url = relay_url or "wss://relay.walletconnect.com"
        self.relay_origin = relay_origin
        self.storage = storage or MemoryStorage()
        self.logger = logger or self._create_default_logger()
        self.storage_prefix = storage_prefix
        
        self.events = EventEmitter()
        self.crypto = Crypto(self.storage, self.logger, storage_prefix=storage_prefix)
        
        # Initialize controllers
        from walletkit.controllers.pairing import Pairing
        from walletkit.controllers.relayer import Relayer
        
        self.relayer = Relayer(
            self,
            self.logger,
            relay_url=self.relay_url,
            project_id=self.project_id,
            origin=self.relay_origin,
        )
        self.expirer = Expirer(self.storage, self.logger, storage_prefix=storage_prefix)
        self.event_client = EventClient(self.storage, self.logger, telemetry_enabled=False, storage_prefix=storage_prefix)
        self.echo_client = EchoClient(self.storage, self.logger, storage_prefix=storage_prefix)
        self.pairing = Pairing(self, self.logger)
        
        self._initialized = False

    async def start(self) -> None:
        """Start Core (initialize all subsystems)."""
        if self._initialized:
            return
        
        await self.crypto.init()
        await self.relayer.init()
        await self.expirer.init()
        await self.event_client.init()
        await self.echo_client.init()
        await self.pairing.init()
        
        self._initialized = True
        self.logger.info("Core Initialization Success")

    def _create_default_logger(self) -> Any:
        """Create default logger.
        
        Returns:
            Logger instance
        """
        # Simple logger implementation
        class SimpleLogger:
            def trace(self, msg: str) -> None:
                pass

            def debug(self, msg: str) -> None:
                print(f"[DEBUG] {msg}")

            def info(self, msg: str) -> None:
                print(f"[INFO] {msg}")

            def warn(self, msg: str, *args: Any) -> None:
                print(f"[WARN] {msg}")

            def warning(self, msg: str, *args: Any) -> None:
                """Alias for warn for compatibility."""
                self.warn(msg, *args)

            def error(self, msg: str, *args: Any) -> None:
                print(f"[ERROR] {msg}")

        return SimpleLogger()

