"""ProposalStore for managing pending session proposals."""
from typing import Any, Dict

from walletkit.controllers.store import Store
from walletkit.utils.storage import IKeyValueStorage


class ProposalStore(Store[int, Dict[str, Any]]):
    """Store for managing pending session proposals by ID."""

    def __init__(
        self,
        storage: IKeyValueStorage,
        logger: Any,
        storage_prefix: str = "wc@2:core:",
        storage_version: str = "1.0",
    ) -> None:
        """Initialize ProposalStore.
        
        Args:
            storage: Storage backend
            logger: Logger instance
            storage_prefix: Storage key prefix
            storage_version: Storage version
        """
        def get_key(proposal: Dict[str, Any]) -> int:
            """Extract ID from proposal."""
            return proposal.get("id", 0)

        super().__init__(
            storage=storage,
            logger=logger,
            name="proposal",
            storage_prefix=storage_prefix,
            storage_version=storage_version,
            get_key=get_key,
        )

