"""Extended tests for EchoClient."""
import pytest

from walletkit.controllers.echo_client import EchoClient
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create storage instance."""
    return MemoryStorage()


@pytest.fixture
def logger():
    """Create logger instance."""
    class SimpleLogger:
        def info(self, msg: str) -> None:
            pass

        def debug(self, msg: str) -> None:
            pass

        def error(self, msg: str) -> None:
            pass

    return SimpleLogger()


@pytest.fixture
async def echo_client(storage, logger):
    """Create and initialize EchoClient."""
    client = EchoClient(storage, logger)
    await client.init()
    return client


@pytest.mark.asyncio
async def test_echo_client_initialization(echo_client):
    """Test EchoClient initialization."""
    assert echo_client._initialized


@pytest.mark.asyncio
async def test_echo_client_register_device_token(echo_client):
    """Test registering device token."""
    # Should not raise error (stub implementation)
    await echo_client.register_device_token(
        client_id="test_client",
        token="test_token",
        enabled=True,
    )

