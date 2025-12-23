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


@pytest.mark.asyncio
async def test_core_start_idempotent(storage):
    """Test Core start is idempotent."""
    core = Core(storage=storage)
    await core.start()
    assert core._initialized is True
    
    # Start again should not re-initialize
    await core.start()
    assert core._initialized is True


@pytest.mark.asyncio
async def test_core_default_logger_methods(storage):
    """Test Core default logger methods."""
    core = Core(storage=storage)
    logger = core.logger
    
    # Test all logger methods
    logger.trace("trace message")
    logger.debug("debug message")
    logger.info("info message")
    logger.warn("warn message")
    logger.warning("warning message")
    logger.error("error message")
    
    # All methods should exist and be callable
    assert hasattr(logger, "trace")
    assert hasattr(logger, "debug")
    assert hasattr(logger, "warn")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")
    assert hasattr(logger, "info")
