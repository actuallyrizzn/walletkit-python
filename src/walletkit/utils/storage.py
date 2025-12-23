"""Storage abstraction layer."""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional


class IKeyValueStorage(ABC):
    """Abstract storage interface."""

    @abstractmethod
    async def get_item(self, key: str) -> Optional[Any]:
        """Get an item from storage.
        
        Args:
            key: Storage key
            
        Returns:
            Stored value or None
        """
        pass

    @abstractmethod
    async def set_item(self, key: str, value: Any) -> None:
        """Set an item in storage.
        
        Args:
            key: Storage key
            value: Value to store
        """
        pass

    @abstractmethod
    async def remove_item(self, key: str) -> None:
        """Remove an item from storage.
        
        Args:
            key: Storage key
        """
        pass

    @abstractmethod
    async def get_keys(self) -> list[str]:
        """Get all storage keys.
        
        Returns:
            List of keys
        """
        pass


class FileStorage(IKeyValueStorage):
    """File-based storage implementation."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """Initialize file storage.
        
        Args:
            storage_path: Path to storage directory
        """
        if storage_path is None:
            storage_path = Path.home() / ".walletkit"
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Any] = {}
        self._load_cache()

    def _get_file_path(self, key: str) -> Path:
        """Get file path for a key.
        
        Args:
            key: Storage key
            
        Returns:
            File path
        """
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.storage_path / f"{safe_key}.json"

    def _load_cache(self) -> None:
        """Load all files into cache."""
        if not self.storage_path.exists():
            return

        for file_path in self.storage_path.glob("*.json"):
            try:
                key = file_path.stem.replace("_", "/")
                with open(file_path, "r") as f:
                    self._cache[key] = json.load(f)
            except Exception:
                pass

    async def get_item(self, key: str) -> Optional[Any]:
        """Get an item from storage."""
        if key in self._cache:
            return self._cache[key]

        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                value = json.load(f)
                self._cache[key] = value
                return value
        except Exception:
            return None

    async def set_item(self, key: str, value: Any) -> None:
        """Set an item in storage."""
        self._cache[key] = value
        file_path = self._get_file_path(key)

        try:
            with open(file_path, "w") as f:
                json.dump(value, f)
        except Exception as e:
            # Remove from cache if write failed
            self._cache.pop(key, None)
            raise e

    async def remove_item(self, key: str) -> None:
        """Remove an item from storage."""
        self._cache.pop(key, None)
        file_path = self._get_file_path(key)

        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

    async def get_keys(self) -> list[str]:
        """Get all storage keys."""
        keys = set(self._cache.keys())

        if self.storage_path.exists():
            for file_path in self.storage_path.glob("*.json"):
                key = file_path.stem.replace("_", "/")
                keys.add(key)

        return list(keys)


class MemoryStorage(IKeyValueStorage):
    """In-memory storage implementation."""

    def __init__(self) -> None:
        """Initialize memory storage."""
        self._storage: dict[str, Any] = {}

    async def get_item(self, key: str) -> Optional[Any]:
        """Get an item from storage."""
        return self._storage.get(key)

    async def set_item(self, key: str, value: Any) -> None:
        """Set an item in storage."""
        self._storage[key] = value

    async def remove_item(self, key: str) -> None:
        """Remove an item from storage."""
        self._storage.pop(key, None)

    async def get_keys(self) -> list[str]:
        """Get all storage keys."""
        return list(self._storage.keys())

