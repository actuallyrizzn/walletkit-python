"""Store implementation for managing key-value data with persistence."""
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from walletkit.types.logger import Logger
from walletkit.utils.storage import IKeyValueStorage

Key = TypeVar("Key")
Data = TypeVar("Data", bound=Dict[str, Any])


class Store(Generic[Key, Data]):
    """Generic key-value store with persistence."""

    def __init__(
        self,
        storage: IKeyValueStorage,
        logger: Logger,
        name: str,
        storage_prefix: str = "wc@2:core:",
        storage_version: str = "1.0",
        get_key: Optional[Callable[[Data], Key]] = None,
    ) -> None:
        """Initialize Store.
        
        Args:
            storage: Storage backend
            logger: Logger instance
            name: Store name
            storage_prefix: Storage key prefix
            storage_version: Storage version
            get_key: Optional function to extract key from data
        """
        self.storage = storage
        self.logger = logger
        self.name = name
        self.storage_prefix = storage_prefix
        self.storage_version = storage_version
        self.get_key = get_key
        
        self.map: Dict[Key, Data] = {}
        self.version = storage_version
        self._initialized = False
        self._cached: List[Data] = []
        self._recently_deleted: List[Key] = []
        self._recently_deleted_limit = 200

    @property
    def storage_key(self) -> str:
        """Get storage key for this store."""
        return f"{self.storage_prefix}{self.storage_version}//{self.name}"

    @property
    def length(self) -> int:
        """Get number of items in store."""
        return len(self.map)

    @property
    def keys(self) -> List[Key]:
        """Get all keys."""
        return list(self.map.keys())

    @property
    def values(self) -> List[Data]:
        """Get all values."""
        return list(self.map.values())

    async def init(self) -> None:
        """Initialize store and restore from persistence."""
        if not self._initialized:
            self.logger.info(f"Initializing store: {self.name}")
            
            await self._restore()
            
            # Restore cached items to map
            for value in self._cached:
                if value is None:
                    continue
                
                if self.get_key:
                    key = self.get_key(value)
                    self.map[key] = value
                elif isinstance(value, dict):
                    # Try to infer key from common patterns
                    if "id" in value:
                        self.map[value["id"]] = value  # type: ignore
                    elif "topic" in value:
                        self.map[value["topic"]] = value  # type: ignore
            
            self._cached = []
            self._initialized = True
            self.logger.info(f"Store initialized: {self.name} ({self.length} items)")

    async def set(self, key: Key, value: Data) -> None:
        """Set a value.
        
        Args:
            key: Key
            value: Value to store
        """
        self._check_initialized()
        
        if key in self.map:
            await self.update(key, value)
        else:
            self.logger.debug(f"Setting value: {key}")
            self.map[key] = value
            await self._persist()

    def get(self, key: Key) -> Data:
        """Get a value.
        
        Args:
            key: Key
            
        Returns:
            Value
            
        Raises:
            KeyError: If key not found
        """
        self._check_initialized()
        self.logger.debug(f"Getting value: {key}")
        
        value = self._get_data(key)
        return value

    def get_all(self, filter_dict: Optional[Dict[str, Any]] = None) -> List[Data]:
        """Get all values, optionally filtered.
        
        Args:
            filter_dict: Optional filter criteria
            
        Returns:
            List of values matching filter
        """
        self._check_initialized()
        
        if not filter_dict:
            return self.values
        
        # Filter values where all filter keys match
        result = []
        for value in self.values:
            if all(value.get(k) == v for k, v in filter_dict.items()):
                result.append(value)
        
        return result

    async def update(self, key: Key, update_dict: Dict[str, Any]) -> None:
        """Update a value.
        
        Args:
            key: Key
            update_dict: Dictionary of fields to update
        """
        self._check_initialized()
        self.logger.debug(f"Updating value: {key}")
        
        current = self._get_data(key)
        updated = {**current, **update_dict}
        self.map[key] = updated  # type: ignore
        await self._persist()

    async def delete(self, key: Key, reason: Optional[str] = None) -> None:
        """Delete a value.
        
        Args:
            key: Key
            reason: Optional deletion reason
        """
        self._check_initialized()
        
        if key not in self.map:
            return
        
        self.logger.debug(f"Deleting value: {key}" + (f" - {reason}" if reason else ""))
        del self.map[key]
        self._add_to_recently_deleted(key)
        await self._persist()

    def has(self, key: Key) -> bool:
        """Check if key exists.
        
        Args:
            key: Key
            
        Returns:
            True if key exists
        """
        self._check_initialized()
        return key in self.map

    # ---------- Private ----------------------------------------------- #

    def _add_to_recently_deleted(self, key: Key) -> None:
        """Add key to recently deleted list."""
        self._recently_deleted.append(key)
        # Limit size - remove oldest half when limit reached
        if len(self._recently_deleted) >= self._recently_deleted_limit:
            self._recently_deleted = self._recently_deleted[
                self._recently_deleted_limit // 2 :
            ]

    async def _persist(self) -> None:
        """Persist store to storage."""
        await self.storage.set_item(self.storage_key, self.values)

    async def _restore(self) -> None:
        """Restore store from storage."""
        try:
            persisted = await self.storage.get_item(self.storage_key)
            if persisted is None:
                return
            if not isinstance(persisted, list):
                return
            if not persisted:
                return
            if self.map:
                error_msg = f"Restore would override existing data in {self.name}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # Store in cache - will be processed in init() after restore
            self._cached = persisted
            self.logger.debug(f"Successfully restored {len(persisted)} items for {self.name}")
        except RuntimeError:
            # Re-raise restore override errors
            raise
        except Exception as e:
            self.logger.debug(f"Failed to restore value for {self.name}")
            self.logger.error(str(e))

    def _get_data(self, key: Key) -> Data:
        """Get data for key, with error handling.
        
        Args:
            key: Key
            
        Returns:
            Value
            
        Raises:
            KeyError: If key not found
        """
        if key in self.map:
            return self.map[key]
        
        if key in self._recently_deleted:
            error_msg = f"Record was recently deleted - {self.name}: {key}"
            self.logger.error(error_msg)
            raise KeyError(error_msg)
        
        error_msg = f"No matching key - {self.name}: {key}"
        self.logger.error(error_msg)
        raise KeyError(error_msg)

    def _check_initialized(self) -> None:
        """Check if store is initialized."""
        if not self._initialized:
            raise RuntimeError(f"{self.name} not initialized. Call init() first.")

