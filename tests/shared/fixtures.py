"""Shared pytest fixtures for walletkit tests."""
from typing import Any

import pytest

from walletkit.core import Core
from walletkit.utils.storage import MemoryStorage


class SimpleLogger:
    """Simple logger implementation for testing."""

    def info(self, msg: str) -> None:
        """Log info message."""
        pass

    def debug(self, msg: str) -> None:
        """Log debug message."""
        pass

    def error(self, msg: str, *args: Any, exc_info: Any = None, **kwargs: Any) -> None:
        """Log error message."""
        pass

    def warning(self, msg: str) -> None:
        """Log warning message."""
        pass


@pytest.fixture
def storage():
    """Create storage instance."""
    return MemoryStorage()


@pytest.fixture
def logger():
    """Create logger instance."""
    return SimpleLogger()


@pytest.fixture
async def core(storage):
    """Create and initialize core instance."""
    core_instance = Core(storage=storage)
    await core_instance.start()
    return core_instance
