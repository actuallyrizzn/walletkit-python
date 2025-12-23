"""KeyChain implementation."""
from typing import Optional

from walletkit.utils.storage import IKeyValueStorage


class KeyChain:
    """KeyChain for storing cryptographic keys."""

    def __init__(
        self,
        storage: IKeyValueStorage,
        storage_prefix: str = "wc@2:core:",
        storage_version: str = "1.0",
    ) -> None:
        """Initialize KeyChain.
        
        Args:
            storage: Storage backend
            storage_prefix: Storage key prefix
            storage_version: Storage version
        """
        self.storage = storage
        self.storage_prefix = storage_prefix
        self.storage_version = storage_version
        self.keychain: dict[str, str] = {}
        self._initialized = False

    @property
    def storage_key(self) -> str:
        """Get storage key for keychain."""
        return f"{self.storage_prefix}{self.storage_version}//keychain"

    async def init(self) -> None:
        """Initialize keychain from storage."""
        if not self._initialized:
            keychain_data = await self.storage.get_item(self.storage_key)
            if keychain_data:
                self.keychain = keychain_data
            self._initialized = True

    def has(self, tag: str) -> bool:
        """Check if key exists.
        
        Args:
            tag: Key tag
            
        Returns:
            True if key exists
        """
        self._check_initialized()
        return tag in self.keychain

    async def set(self, tag: str, key: str) -> None:
        """Set a key.
        
        Args:
            tag: Key tag
            key: Key value
        """
        self._check_initialized()
        self.keychain[tag] = key
        await self._persist()

    def get(self, tag: str) -> str:
        """Get a key.
        
        Args:
            tag: Key tag
            
        Returns:
            Key value
            
        Raises:
            KeyError: If key doesn't exist
        """
        self._check_initialized()
        if tag not in self.keychain:
            raise KeyError(f"Key not found: {tag}")
        return self.keychain[tag]

    async def delete(self, tag: str) -> None:
        """Delete a key.
        
        Args:
            tag: Key tag
        """
        self._check_initialized()
        if tag in self.keychain:
            del self.keychain[tag]
            await self._persist()

    async def _persist(self) -> None:
        """Persist keychain to storage."""
        await self.storage.set_item(self.storage_key, self.keychain)

    def _check_initialized(self) -> None:
        """Check if keychain is initialized."""
        if not self._initialized:
            raise RuntimeError("KeyChain not initialized. Call init() first.")

