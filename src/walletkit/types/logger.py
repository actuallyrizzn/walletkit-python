"""Logger type definitions."""
from typing import Any, Protocol


class Logger(Protocol):
    """Logger interface protocol.
    
    This protocol defines the interface that any logger implementation
    must satisfy. It's compatible with standard library logging, structlog,
    loguru, and other logging libraries.
    """

    def trace(self, msg: str) -> None:
        """Log trace message.
        
        Args:
            msg: Message to log
        """
        ...

    def debug(self, msg: str) -> None:
        """Log debug message.
        
        Args:
            msg: Message to log
        """
        ...

    def info(self, msg: str) -> None:
        """Log info message.
        
        Args:
            msg: Message to log
        """
        ...

    def warn(self, msg: str, *args: Any) -> None:
        """Log warning message.
        
        Args:
            msg: Message to log
            *args: Additional arguments
        """
        ...

    def warning(self, msg: str, *args: Any) -> None:
        """Log warning message (alias for warn).
        
        Args:
            msg: Message to log
            *args: Additional arguments
        """
        ...

    def error(self, msg: str, *args: Any) -> None:
        """Log error message.
        
        Args:
            msg: Message to log
            *args: Additional arguments
        """
        ...
