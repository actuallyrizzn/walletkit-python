"""Decorators for common patterns."""
import functools
import inspect
from typing import Any, Callable, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def handle_errors(func: F) -> F:
    """Decorator to handle errors and log them.
    
    Catches exceptions, logs them using the instance's logger, and re-raises.
    Works with both sync and async methods.
    
    Args:
        func: Function or method to wrap
        
    Returns:
        Wrapped function with error handling
    """
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            """Async wrapper for error handling."""
            try:
                return await func(self, *args, **kwargs)
            except Exception as error:
                if hasattr(self, "logger"):
                    self.logger.error(str(error))
                raise
        
        return cast(F, async_wrapper)
    else:
        @functools.wraps(func)
        def sync_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            """Sync wrapper for error handling."""
            try:
                return func(self, *args, **kwargs)
            except Exception as error:
                if hasattr(self, "logger"):
                    self.logger.error(str(error))
                raise
        
        return cast(F, sync_wrapper)


def require_initialized(func: F) -> F:
    """Decorator to require initialization before method execution.
    
    Checks if the instance has `_initialized` attribute set to True.
    Raises RuntimeError if not initialized.
    
    Args:
        func: Method to wrap
        
    Returns:
        Wrapped method with initialization check
    """
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        """Wrapper that checks initialization."""
        if not getattr(self, "_initialized", False):
            class_name = self.__class__.__name__
            raise RuntimeError(f"{class_name} not initialized")
        return func(self, *args, **kwargs)
    
    return cast(F, wrapper)
