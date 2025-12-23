"""Edge case test for KeyChain delete."""
import pytest

from walletkit.controllers.keychain import KeyChain
from walletkit.utils.storage import MemoryStorage


@pytest.fixture
def storage():
    """Create storage instance."""
    return MemoryStorage()


@pytest.mark.asyncio
async def test_keychain_delete_nonexistent_key(storage):
    """Test deleting non-existent key doesn't raise error."""
    keychain = KeyChain(storage)
    await keychain.init()
    
    # Should not raise error
    await keychain.delete("nonexistent_key")

