"""RequestStore for managing pending session requests."""
from typing import Any, Dict, List

from walletkit.utils.storage import IKeyValueStorage


class RequestStore:
    """Store for managing pending session requests.
    
    Note: Requests are stored as a list, not a map, since they don't have
    a single unique key (they're identified by topic + request ID).
    """

    def __init__(
        self,
        storage: IKeyValueStorage,
        logger: Any,
        storage_prefix: str = "wc@2:core:",
        storage_version: str = "1.0",
    ) -> None:
        """Initialize RequestStore.
        
        Args:
            storage: Storage backend
            logger: Logger instance
            storage_prefix: Storage key prefix
            storage_version: Storage version
        """
        self.storage = storage
        self.logger = logger
        self.name = "pending_request"
        self.storage_prefix = storage_prefix
        self.storage_version = storage_version
        
        self.requests: List[Dict[str, Any]] = []
        self._initialized = False

    @property
    def storage_key(self) -> str:
        """Get storage key for this store."""
        return f"{self.storage_prefix}{self.storage_version}//{self.name}"

    @property
    def length(self) -> int:
        """Get number of pending requests."""
        return len(self.requests)

    async def init(self) -> None:
        """Initialize store and restore from persistence."""
        if not self._initialized:
            self.logger.info(f"Initializing {self.name}")
            await self._restore()
            self._initialized = True
            self.logger.info(f"{self.name} initialized ({self.length} requests)")

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all pending requests.
        
        Returns:
            List of pending requests
        """
        self._check_initialized()
        return self.requests.copy()

    def get_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Get requests for a specific topic.
        
        Args:
            topic: Session topic
            
        Returns:
            List of requests for topic
        """
        self._check_initialized()
        return [req for req in self.requests if req.get("topic") == topic]

    def get_by_id(self, id: int) -> Dict[str, Any]:
        """Get request by ID.
        
        Args:
            id: Request ID
            
        Returns:
            Request dict
            
        Raises:
            KeyError: If request not found
        """
        self._check_initialized()
        for req in self.requests:
            request_data = req.get("request", {})
            if request_data.get("id") == id:
                return req
        
        raise KeyError(f"Request not found: {id}")

    async def add(self, request: Dict[str, Any]) -> None:
        """Add a pending request.
        
        Args:
            request: Request dict with 'topic' and 'request' keys
        """
        self._check_initialized()
        self.logger.debug(f"Adding pending request: {request.get('request', {}).get('id')}")
        self.requests.append(request)
        await self._persist()

    async def delete(self, id: int) -> None:
        """Delete a pending request by ID.
        
        Args:
            id: Request ID
        """
        self._check_initialized()
        original_length = len(self.requests)
        self.requests = [
            req
            for req in self.requests
            if req.get("request", {}).get("id") != id
        ]
        
        if len(self.requests) < original_length:
            self.logger.debug(f"Deleted pending request: {id}")
            await self._persist()

    async def delete_by_topic(self, topic: str) -> None:
        """Delete all requests for a topic.
        
        Args:
            topic: Session topic
        """
        self._check_initialized()
        original_length = len(self.requests)
        self.requests = [req for req in self.requests if req.get("topic") != topic]
        
        if len(self.requests) < original_length:
            self.logger.debug(f"Deleted requests for topic: {topic}")
            await self._persist()

    async def _persist(self) -> None:
        """Persist requests to storage."""
        await self.storage.set_item(self.storage_key, self.requests)

    async def _restore(self) -> None:
        """Restore requests from storage."""
        try:
            persisted = await self.storage.get_item(self.storage_key)
            if persisted is None:
                return
            if not isinstance(persisted, list):
                return
            if not persisted:
                return
            if self.requests:
                error_msg = f"Restore would override existing data in {self.name}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            self.requests = persisted
            self.logger.debug(f"Successfully restored {len(persisted)} requests")
        except Exception as e:
            self.logger.debug(f"Failed to restore {self.name}")
            self.logger.error(str(e))

    def _check_initialized(self) -> None:
        """Check if store is initialized."""
        if not self._initialized:
            raise RuntimeError(f"{self.name} not initialized. Call init() first.")

