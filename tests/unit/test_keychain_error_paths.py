"""Error path tests for KeyChain."""
import pytest

from walletkit.controllers.keychain import KeyChain
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create storage instance."""
    return MemoryStorage()


@pytest.mark.asyncio
async def test_keychain_get_before_init(storage):
    """Test that get raises error before init."""
    keychain = KeyChain(storage)
    
    with pytest.raises(RuntimeError, match="not initialized"):
        keychain.get("test")


@pytest.mark.asyncio
async def test_keychain_set_before_init(storage):
    """Test that set raises error before init."""
    keychain = KeyChain(storage)
    
    with pytest.raises(RuntimeError, match="not initialized"):
        await keychain.set("test", "value")


@pytest.mark.asyncio
async def test_keychain_delete_before_init(storage):
    """Test that delete raises error before init."""
    keychain = KeyChain(storage)
    
    with pytest.raises(RuntimeError, match="not initialized"):
        await keychain.delete("test")


@pytest.mark.asyncio
async def test_keychain_has_before_init(storage):
    """Test that has raises error before init."""
    keychain = KeyChain(storage)
    
    with pytest.raises(RuntimeError, match="not initialized"):
        keychain.has("test")

