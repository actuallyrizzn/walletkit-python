"""SessionStore for managing active sessions."""
from typing import Any, Dict

from walletkit.controllers.store import Store
from walletkit.utils.storage import IKeyValueStorage


class SessionStore(Store[str, Dict[str, Any]]):
    """Store for managing active sessions by topic."""

    def __init__(
        self,
        storage: IKeyValueStorage,
        logger: Any,
        storage_prefix: str = "wc@2:core:",
        storage_version: str = "1.0",
    ) -> None:
        """Initialize SessionStore.
        
        Args:
            storage: Storage backend
            logger: Logger instance
            storage_prefix: Storage key prefix
            storage_version: Storage version
        """
        def get_key(session: Dict[str, Any]) -> str:
            """Extract topic from session."""
            return session.get("topic", "")

        super().__init__(
            storage=storage,
            logger=logger,
            name="session",
            storage_prefix=storage_prefix,
            storage_version=storage_version,
            get_key=get_key,
        )

