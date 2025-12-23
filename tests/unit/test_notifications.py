"""Tests for Notifications utility."""
import pytest

from walletkit.utils.notifications import Notifications, decrypt_message, get_metadata
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create storage instance."""
    return MemoryStorage()


@pytest.mark.asyncio
async def test_decrypt_message(storage):
    """Test decrypting a message."""
    # This is a placeholder test - real decryption requires proper setup
    # with crypto keys and encrypted messages
    from walletkit.core import Core
    
    core = Core(storage=storage)
    await core.start()
    
    # Create a topic and set up crypto
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    topic = await core.crypto.set_sym_key(sym_key)
    
    # Create a test message
    test_payload = {"jsonrpc": "2.0", "id": 1, "method": "test", "params": {}}
    
    # Encode it
    encoded = await core.crypto.encode(topic, test_payload)
    
    # Decrypt it using notifications
    decoded = await decrypt_message(topic, encoded, storage=storage)
    
    assert decoded == test_payload


@pytest.mark.asyncio
async def test_get_metadata(storage):
    """Test getting session metadata."""
    from walletkit.core import Core
    from walletkit.controllers.session_store import SessionStore
    
    core = Core(storage=storage)
    await core.start()
    
    # Create a session store and add a session
    session_store = SessionStore(core.storage, core.logger)
    await session_store.init()
    
    metadata = {
        "name": "Test Dapp",
        "description": "Test Description",
        "url": "https://example.com",
        "icons": ["https://example.com/icon.png"],
    }
    
    session = {
        "topic": "test_topic",
        "peer": {"metadata": metadata},
        "expiry": 1234567890,
    }
    
    await session_store.set("test_topic", session)
    
    # Get metadata using notifications
    retrieved = await get_metadata("test_topic", storage=storage)
    
    assert retrieved == metadata


@pytest.mark.asyncio
async def test_notifications_class(storage):
    """Test Notifications class methods."""
    from walletkit.core import Core
    
    core = Core(storage=storage)
    await core.start()
    
    # Test decrypt_message
    from walletkit.utils.crypto_utils import generate_random_bytes32
    sym_key = generate_random_bytes32()
    topic = await core.crypto.set_sym_key(sym_key)
    
    test_payload = {"jsonrpc": "2.0", "id": 1, "method": "test"}
    encoded = await core.crypto.encode(topic, test_payload)
    
    decoded = await Notifications.decrypt_message(topic, encoded, storage=storage)
    assert decoded == test_payload
    
    # Test get_metadata
    from walletkit.controllers.session_store import SessionStore
    
    session_store = SessionStore(core.storage, core.logger)
    await session_store.init()
    
    metadata = {"name": "Test", "url": "https://test.com"}
    session = {"topic": "test_topic2", "peer": {"metadata": metadata}}
    await session_store.set("test_topic2", session)
    
    retrieved = await Notifications.get_metadata("test_topic2", storage=storage)
    assert retrieved == metadata

