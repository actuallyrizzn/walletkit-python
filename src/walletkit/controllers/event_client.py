"""EventClient for telemetry and event tracking."""
from typing import Any, Dict, List, Optional
from uuid import uuid4

from walletkit.utils.storage import IKeyValueStorage

# Event client constants
EVENT_CLIENT_CONTEXT = "event-client"
EVENT_CLIENT_STORAGE_VERSION = "1.0"


class Event:
    """Represents a telemetry event."""

    def __init__(
        self,
        event_id: str,
        event_type: str,
        timestamp: int,
        props: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize event.
        
        Args:
            event_id: Unique event ID
            event_type: Event type
            timestamp: Event timestamp
            props: Event properties
        """
        self.event_id = event_id
        self.event_type = event_type
        self.timestamp = timestamp
        self.props = props or {}
        self.traces: List[str] = []
        self.error: Optional[str] = None

    def add_trace(self, trace: str) -> None:
        """Add trace to event.
        
        Args:
            trace: Trace message
        """
        self.traces.append(trace)

    def set_error(self, error: str) -> None:
        """Set error on event.
        
        Args:
            error: Error message
        """
        self.error = error
        self.props["type"] = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.
        
        Returns:
            Event as dictionary
        """
        return {
            "eventId": self.event_id,
            "eventType": self.event_type,
            "timestamp": self.timestamp,
            "props": self.props,
            "traces": self.traces,
            "error": self.error,
        }


class EventClient:
    """EventClient for telemetry and event tracking."""

    def __init__(
        self,
        storage: IKeyValueStorage,
        logger: Any,
        telemetry_enabled: bool = False,
        storage_prefix: str = "wc@2:core:",
        storage_version: str = EVENT_CLIENT_STORAGE_VERSION,
    ) -> None:
        """Initialize EventClient.
        
        Args:
            storage: Storage backend
            logger: Logger instance
            telemetry_enabled: Whether telemetry is enabled
            storage_prefix: Storage key prefix
            storage_version: Storage version
        """
        self.storage = storage
        self.logger = logger
        self.telemetry_enabled = telemetry_enabled
        self.storage_prefix = storage_prefix
        self.storage_version = storage_version
        self.context = EVENT_CLIENT_CONTEXT
        
        self.events: Dict[str, Event] = {}
        self._initialized = False

    @property
    def storage_key(self) -> str:
        """Get storage key for events."""
        return f"{self.storage_prefix}{self.storage_version}//{self.context}"

    async def init(self) -> None:
        """Initialize EventClient."""
        if not self._initialized:
            if self.telemetry_enabled:
                await self._restore()
            self._initialized = True

    def create_event(
        self,
        event_type: str,
        timestamp: Optional[int] = None,
        props: Optional[Dict[str, Any]] = None,
    ) -> Event:
        """Create a new event.
        
        Args:
            event_type: Event type
            timestamp: Optional timestamp (defaults to current time)
            props: Optional event properties
            
        Returns:
            Created event
        """
        import time
        
        event_id = str(uuid4())
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        
        event = Event(event_id, event_type, timestamp, props)
        self.events[event_id] = event
        
        return event

    def get_event(self, event_id: str) -> Optional[Event]:
        """Get event by ID.
        
        Args:
            event_id: Event ID
            
        Returns:
            Event if found, None otherwise
        """
        return self.events.get(event_id)

    def delete_event(self, event_id: str) -> None:
        """Delete event.
        
        Args:
            event_id: Event ID
        """
        if event_id in self.events:
            del self.events[event_id]

    async def send_event(self, events: List[Event]) -> None:
        """Send events (telemetry).
        
        Args:
            events: List of events to send
        """
        if not self.telemetry_enabled:
            return
        
        # In a real implementation, this would send to telemetry endpoint
        # For now, just log if enabled
        if events:
            self.logger.debug(f"Sending {len(events)} telemetry events")

    async def _restore(self) -> None:
        """Restore events from storage."""
        try:
            persisted = await self.storage.get_item(self.storage_key)
            if persisted is None:
                return
            if not isinstance(persisted, list):
                return
            
            for event_data in persisted:
                event_id = event_data.get("eventId")
                if event_id:
                    event = Event(
                        event_id,
                        event_data.get("eventType", ""),
                        event_data.get("timestamp", 0),
                        event_data.get("props", {}),
                    )
                    event.traces = event_data.get("traces", [])
                    event.error = event_data.get("error")
                    self.events[event_id] = event
        except Exception as e:
            self.logger.debug(f"Failed to restore events: {e}")

    async def _persist(self) -> None:
        """Persist events to storage."""
        if not self.telemetry_enabled:
            return
        
        events_data = [event.to_dict() for event in self.events.values()]
        await self.storage.set_item(self.storage_key, events_data)

