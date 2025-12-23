"""Expirer controller for tracking and managing expirations."""
import asyncio
import time
from typing import Any, Callable, Dict, List, Optional

from walletkit.utils.events import EventEmitter
from walletkit.utils.storage import IKeyValueStorage

# Expirer events
EXPIRER_EVENTS = {
    "created": "expirer_created",
    "expired": "expirer_expired",
    "deleted": "expirer_deleted",
    "sync": "expirer_sync",
}

# Storage constants
EXPIRER_CONTEXT = "expirer"
EXPIRER_STORAGE_VERSION = "1.0"


def format_topic_target(topic: str) -> str:
    """Format topic as expirer target.
    
    Args:
        topic: Topic string
        
    Returns:
        Formatted target string
    """
    return f"topic:{topic}"


def format_id_target(id: int) -> str:
    """Format ID as expirer target.
    
    Args:
        id: Numeric ID
        
    Returns:
        Formatted target string
    """
    return f"id:{id}"


def format_target(key: str | int) -> str:
    """Format key as expirer target.
    
    Args:
        key: Topic string or numeric ID
        
    Returns:
        Formatted target string
    """
    if isinstance(key, str):
        return format_topic_target(key)
    elif isinstance(key, int):
        return format_id_target(key)
    else:
        raise ValueError(f"Unknown target type: {type(key)}")


def parse_expirer_target(target: str) -> Dict[str, Any]:
    """Parse expirer target string.
    
    Args:
        target: Formatted target string (e.g., "topic:abc" or "id:123")
        
    Returns:
        Dict with 'type' and 'value'
    """
    if ":" not in target:
        raise ValueError(f"Invalid target format: {target}")
    
    target_type, value = target.split(":", 1)
    
    if target_type == "topic":
        return {"type": "topic", "value": value}
    elif target_type == "id":
        return {"type": "id", "value": int(value)}
    else:
        raise ValueError(f"Unknown target type: {target_type}")


class Expiration:
    """Represents an expiration entry."""

    def __init__(self, target: str, expiry: int) -> None:
        """Initialize expiration.
        
        Args:
            target: Formatted target string
            expiry: Expiry timestamp in seconds (unix epoch)
        """
        self.target = target
        self.expiry = expiry


class Expirer:
    """Expirer controller for tracking expirations."""

    def __init__(
        self,
        storage: IKeyValueStorage,
        logger: Any,
        storage_prefix: str = "wc@2:core:",
        storage_version: str = EXPIRER_STORAGE_VERSION,
    ) -> None:
        """Initialize Expirer.
        
        Args:
            storage: Storage backend
            logger: Logger instance
            storage_prefix: Storage key prefix
            storage_version: Storage version
        """
        self.storage = storage
        self.logger = logger
        self.storage_prefix = storage_prefix
        self.storage_version = storage_version
        self.name = EXPIRER_CONTEXT
        
        self.expirations: Dict[str, Expiration] = {}
        self.events = EventEmitter()
        self._initialized = False
        self._cached: List[Dict[str, Any]] = []
        self._check_task: Optional[asyncio.Task] = None
        self._check_interval = 1.0  # Check every second

    @property
    def storage_key(self) -> str:
        """Get storage key for expirer."""
        return f"{self.storage_prefix}{self.storage_version}//{self.name}"

    @property
    def length(self) -> int:
        """Get number of tracked expirations."""
        return len(self.expirations)

    @property
    def keys(self) -> List[str]:
        """Get all target keys."""
        return list(self.expirations.keys())

    @property
    def values(self) -> List[Expiration]:
        """Get all expiration values."""
        return list(self.expirations.values())

    async def init(self) -> None:
        """Initialize expirer and restore from storage."""
        if not self._initialized:
            self.logger.info(f"Initializing {self.name}")
            await self._restore()
            
            # Restore cached expirations
            for exp_data in self._cached:
                target = exp_data.get("target")
                expiry = exp_data.get("expiry")
                if target and expiry is not None:
                    self.expirations[target] = Expiration(target, expiry)
            
            self._cached = []
            
            # Start expiry checking task
            self._check_task = asyncio.create_task(self._check_loop())
            
            # Register event listeners
            self._register_event_listeners()
            
            self._initialized = True
            self.logger.info(f"{self.name} initialized ({self.length} expirations)")

    async def cleanup(self) -> None:
        """Cleanup expirer and stop checking."""
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            self._check_task = None

    def has(self, key: str | int) -> bool:
        """Check if expiration exists for key.
        
        Args:
            key: Topic string or numeric ID
            
        Returns:
            True if expiration exists
        """
        self._check_initialized()
        try:
            target = format_target(key)
            return target in self.expirations
        except Exception:
            return False

    def set(self, key: str | int, expiry: int) -> None:
        """Set expiration for key.
        
        Args:
            key: Topic string or numeric ID
            expiry: Expiry timestamp in seconds (unix epoch)
        """
        self._check_initialized()
        target = format_target(key)
        expiration = Expiration(target, expiry)
        self.expirations[target] = expiration
        
        # Check if already expired
        self._check_expiry(target, expiration)
        
        # Emit created event (fire and forget)
        asyncio.create_task(self.events.emit(EXPIRER_EVENTS["created"], {
            "target": target,
            "expiration": expiration,
        }))

    def get(self, key: str | int) -> Expiration:
        """Get expiration for key.
        
        Args:
            key: Topic string or numeric ID
            
        Returns:
            Expiration object
            
        Raises:
            KeyError: If expiration not found
        """
        self._check_initialized()
        target = format_target(key)
        if target not in self.expirations:
            raise KeyError(f"No expiration found for {target}")
        return self.expirations[target]

    def delete(self, key: str | int) -> None:
        """Delete expiration for key.
        
        Args:
            key: Topic string or numeric ID
        """
        self._check_initialized()
        if self.has(key):
            target = format_target(key)
            expiration = self.expirations[target]
            del self.expirations[target]
            
            # Emit deleted event (fire and forget)
            asyncio.create_task(self.events.emit(EXPIRER_EVENTS["deleted"], {
                "target": target,
                "expiration": expiration,
            }))

    def on(self, event: str, listener: Callable[[Any], None]) -> None:
        """Register event listener.
        
        Args:
            event: Event name
            listener: Event listener function
        """
        self.events.on(event, listener)

    def once(self, event: str, listener: Callable[[Any], None]) -> None:
        """Register one-time event listener.
        
        Args:
            event: Event name
            listener: Event listener function
        """
        self.events.once(event, listener)

    def off(self, event: str, listener: Callable[[Any], None]) -> None:
        """Unregister event listener.
        
        Args:
            event: Event name
            listener: Event listener function
        """
        self.events.off(event, listener)

    def remove_listener(self, event: str, listener: Callable[[Any], None]) -> None:
        """Remove event listener.
        
        Args:
            event: Event name
            listener: Event listener function
        """
        self.events.remove_listener(event, listener)

    # ---------- Private ----------------------------------------------- #

    async def _check_loop(self) -> None:
        """Background task to periodically check for expired items."""
        while True:
            try:
                await asyncio.sleep(self._check_interval)
                self._check_expirations()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in expiry check loop: {e}")

    def _check_expirations(self) -> None:
        """Check all expirations for expiry."""
        # Note: In real implementation, would check if relayer is connected
        # For now, always check
        for target, expiration in list(self.expirations.items()):
            self._check_expiry(target, expiration)

    def _check_expiry(self, target: str, expiration: Expiration) -> None:
        """Check if expiration has expired.
        
        Args:
            target: Target string
            expiration: Expiration object
        """
        now_s = int(time.time())
        if expiration.expiry <= now_s:
            self._expire(target, expiration)

    def _expire(self, target: str, expiration: Expiration) -> None:
        """Mark expiration as expired.
        
        Args:
            target: Target string
            expiration: Expiration object
        """
        if target in self.expirations:
            del self.expirations[target]
            # Emit expired event (fire and forget)
            asyncio.create_task(self.events.emit(EXPIRER_EVENTS["expired"], {
                "target": target,
                "expiration": expiration,
            }))

    def _register_event_listeners(self) -> None:
        """Register internal event listeners for persistence."""
        async def on_created(event: Dict[str, Any]) -> None:
            self.logger.debug(f"Expiration created: {event.get('target')}")
            await self._persist()

        async def on_expired(event: Dict[str, Any]) -> None:
            self.logger.debug(f"Expiration expired: {event.get('target')}")
            await self._persist()

        async def on_deleted(event: Dict[str, Any]) -> None:
            self.logger.debug(f"Expiration deleted: {event.get('target')}")
            await self._persist()

        self.events.on(EXPIRER_EVENTS["created"], on_created)
        self.events.on(EXPIRER_EVENTS["expired"], on_expired)
        self.events.on(EXPIRER_EVENTS["deleted"], on_deleted)
        
        # Also emit sync event after persist
        async def on_sync() -> None:
            self.events.emit(EXPIRER_EVENTS["sync"])
        
        # Note: sync event is emitted in _persist, no need to listen here

    async def _persist(self) -> None:
        """Persist expirations to storage."""
        expirations_data = [
            {"target": exp.target, "expiry": exp.expiry}
            for exp in self.expirations.values()
        ]
        await self.storage.set_item(self.storage_key, expirations_data)
        await self.events.emit(EXPIRER_EVENTS["sync"])

    async def _restore(self) -> None:
        """Restore expirations from storage."""
        try:
            persisted = await self.storage.get_item(self.storage_key)
            if persisted is None:
                return
            if not isinstance(persisted, list):
                return
            if not persisted:
                return
            if self.expirations:
                error_msg = f"Restore would override existing data in {self.name}"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            self._cached = persisted
            self.logger.debug(f"Successfully restored {len(persisted)} expirations")
        except RuntimeError:
            # Re-raise restore override errors
            raise
        except Exception as e:
            self.logger.debug(f"Failed to restore {self.name}")
            self.logger.error(str(e))

    def _check_initialized(self) -> None:
        """Check if expirer is initialized."""
        if not self._initialized:
            raise RuntimeError(f"{self.name} not initialized. Call init() first.")

