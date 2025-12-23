"""Extended tests for EventClient."""
import pytest

from walletkit.controllers.event_client import EventClient
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
async def event_client(storage, logger):
    """Create and initialize EventClient."""
    client = EventClient(storage, logger, telemetry_enabled=False)
    await client.init()
    return client


@pytest.mark.asyncio
async def test_event_client_initialization(event_client):
    """Test EventClient initialization."""
    assert event_client._initialized
    assert not event_client.telemetry_enabled


@pytest.mark.asyncio
async def test_event_client_send_event(event_client):
    """Test sending events."""
    from walletkit.controllers.event_client import Event
    import time
    
    # Create event objects
    event = Event(
        event_id="test_id",
        event_type="test_event",
        timestamp=int(time.time() * 1000),
        props={"test": "data"},
    )
    
    # Should not raise error even if telemetry is disabled
    await event_client.send_event([event])


@pytest.mark.asyncio
async def test_event_client_with_telemetry(storage, logger):
    """Test EventClient with telemetry enabled."""
    client = EventClient(storage, logger, telemetry_enabled=True)
    await client.init()
    
    assert client.telemetry_enabled

