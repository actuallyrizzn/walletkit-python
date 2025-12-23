"""Extended tests for KeyChain."""
import pytest

from walletkit.controllers.keychain import KeyChain
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
async def keychain(storage, logger):
    """Create and initialize keychain."""
    keychain = KeyChain(storage, logger, "test")
    await keychain.init()
    return keychain


@pytest.mark.asyncio
async def test_keychain_get_nonexistent(keychain):
    """Test getting non-existent key raises KeyError."""
    with pytest.raises(KeyError):
        keychain.get("nonexistent_key")


@pytest.mark.asyncio
async def test_keychain_set_get(keychain):
    """Test setting and getting a key."""
    from walletkit.utils.crypto_utils import generate_random_bytes32
    key = generate_random_bytes32()
    
    await keychain.set("test_key", key)
    retrieved = keychain.get("test_key")
    
    assert retrieved == key


@pytest.mark.asyncio
async def test_keychain_delete(keychain):
    """Test deleting a key."""
    from walletkit.utils.crypto_utils import generate_random_bytes32
    key = generate_random_bytes32()
    
    await keychain.set("test_key", key)
    assert keychain.has("test_key")
    
    await keychain.delete("test_key")
    assert not keychain.has("test_key")
    
    with pytest.raises(KeyError):
        keychain.get("test_key")


@pytest.mark.asyncio
async def test_keychain_persistence(storage, logger):
    """Test keychain persistence across instances."""
    keychain1 = KeyChain(storage, logger, "test")
    await keychain1.init()
    
    from walletkit.utils.crypto_utils import generate_random_bytes32
    key = generate_random_bytes32()
    
    await keychain1.set("persistent_key", key)
    # KeyChain persists automatically on set
    
    # Create new instance with same storage
    keychain2 = KeyChain(storage, logger, "test")
    await keychain2.init()
    
    # Should be able to retrieve the key
    assert keychain2.has("persistent_key")
    assert keychain2.get("persistent_key") == key

