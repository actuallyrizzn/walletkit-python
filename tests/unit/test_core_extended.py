"""Extended tests for Core."""
import pytest

from walletkit.core import Core
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create storage instance."""
    return MemoryStorage()


@pytest.mark.asyncio
async def test_core_initialization(storage):
    """Test Core initialization."""
    core = Core(storage=storage)
    
    assert core.crypto is not None
    assert core.relayer is not None
    assert core.pairing is not None
    assert core.expirer is not None
    assert core.event_client is not None
    assert core.echo_client is not None


@pytest.mark.asyncio
async def test_core_start(storage):
    """Test Core start method."""
    core = Core(storage=storage)
    await core.start()
    
    # After start, components should be initialized
    assert core.crypto._initialized
    assert core.expirer._initialized


@pytest.mark.asyncio
async def test_core_logger(storage):
    """Test Core logger property."""
    core = Core(storage=storage)
    
    assert core.logger is not None
    assert hasattr(core.logger, "info")
    assert hasattr(core.logger, "debug")
    assert hasattr(core.logger, "error")


@pytest.mark.asyncio
async def test_core_storage(storage):
    """Test Core storage property."""
    core = Core(storage=storage)
    
    assert core.storage == storage


@pytest.mark.asyncio
async def test_core_storage_prefix(storage):
    """Test Core storage prefix."""
    custom_prefix = "custom:prefix:"
    core = Core(storage=storage, storage_prefix=custom_prefix)
    
    assert core.storage_prefix == custom_prefix

