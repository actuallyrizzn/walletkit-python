"""EventEmitter implementation for async event handling."""
import asyncio
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional


class EventEmitter:
    """Event emitter supporting both sync and async listeners."""

    def __init__(self) -> None:
        """Initialize the event emitter."""
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)
        self._once_listeners: Dict[str, List[Callable]] = defaultdict(list)

    def on(self, event: str, listener: Callable) -> "EventEmitter":
        """Register an event listener.
        
        Args:
            event: Event name
            listener: Listener function (can be sync or async)
            
        Returns:
            Self for chaining
        """
        self._listeners[event].append(listener)
        return self

    def once(self, event: str, listener: Callable) -> "EventEmitter":
        """Register a one-time event listener.
        
        Args:
            event: Event name
            listener: Listener function (can be sync or async)
            
        Returns:
            Self for chaining
        """
        self._once_listeners[event].append(listener)
        return self

    async def emit(self, event: str, *args: Any, **kwargs: Any) -> bool:
        """Emit an event to all registered listeners.
        
        Args:
            event: Event name
            *args: Positional arguments to pass to listeners
            **kwargs: Keyword arguments to pass to listeners
            
        Returns:
            True if listeners were called, False otherwise
        """
        if event not in self._listeners and event not in self._once_listeners:
            return False

        # Call regular listeners
        for listener in self._listeners.get(event, []):
            if asyncio.iscoroutinefunction(listener):
                await listener(*args, **kwargs)
            else:
                listener(*args, **kwargs)

        # Call once listeners and remove them
        once_listeners = self._once_listeners.pop(event, [])
        for listener in once_listeners:
            if asyncio.iscoroutinefunction(listener):
                await listener(*args, **kwargs)
            else:
                listener(*args, **kwargs)

        return True

    def off(self, event: str, listener: Callable) -> "EventEmitter":
        """Remove an event listener.
        
        Args:
            event: Event name
            listener: Listener function to remove
            
        Returns:
            Self for chaining
        """
        if event in self._listeners:
            try:
                self._listeners[event].remove(listener)
            except ValueError:
                pass

        if event in self._once_listeners:
            try:
                self._once_listeners[event].remove(listener)
            except ValueError:
                pass

        return self

    def remove_listener(self, event: str, listener: Callable) -> "EventEmitter":
        """Remove an event listener (alias for off).
        
        Args:
            event: Event name
            listener: Listener function to remove
            
        Returns:
            Self for chaining
        """
        return self.off(event, listener)

    def remove_all_listeners(self, event: Optional[str] = None) -> "EventEmitter":
        """Remove all listeners for an event, or all events.
        
        Args:
            event: Event name, or None to remove all
            
        Returns:
            Self for chaining
        """
        if event is None:
            self._listeners.clear()
            self._once_listeners.clear()
        else:
            self._listeners.pop(event, None)
            self._once_listeners.pop(event, None)

        return self

    def listener_count(self, event: str) -> int:
        """Get the number of listeners for an event.
        
        Args:
            event: Event name
            
        Returns:
            Number of listeners
        """
        return len(self._listeners.get(event, [])) + len(self._once_listeners.get(event, []))

