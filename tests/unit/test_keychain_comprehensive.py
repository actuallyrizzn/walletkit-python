"""Comprehensive tests for KeyChain."""
import pytest

from walletkit.controllers.keychain import KeyChain


@pytest.mark.asyncio
async def test_keychain_storage_key(storage):
    """Test storage key property."""
    keychain = KeyChain(storage, "test_prefix", "2.0")
    await keychain.init()
    
    assert keychain.storage_key == "test_prefix2.0//keychain"


@pytest.mark.asyncio
async def test_keychain_init_restores_from_storage(storage, logger):
    """Test that keychain restores from storage on init."""
    # First instance - set a key
    keychain1 = KeyChain(storage, logger, "test")
    await keychain1.init()
    
    from walletkit.utils.crypto_utils import generate_random_bytes32
    key = generate_random_bytes32()
    await keychain1.set("restored_key", key)
    
    # Second instance - should restore the key
    keychain2 = KeyChain(storage, logger, "test")
    await keychain2.init()
    
    assert keychain2.has("restored_key")
    assert keychain2.get("restored_key") == key


@pytest.mark.asyncio
async def test_keychain_multiple_keys(storage, logger):
    """Test managing multiple keys."""
    keychain = KeyChain(storage, logger, "test")
    await keychain.init()
    
    from walletkit.utils.crypto_utils import generate_random_bytes32
    key1 = generate_random_bytes32()
    key2 = generate_random_bytes32()
    key3 = generate_random_bytes32()
    
    await keychain.set("key1", key1)
    await keychain.set("key2", key2)
    await keychain.set("key3", key3)
    
    assert keychain.has("key1")
    assert keychain.has("key2")
    assert keychain.has("key3")
    
    assert keychain.get("key1") == key1
    assert keychain.get("key2") == key2
    assert keychain.get("key3") == key3


@pytest.mark.asyncio
async def test_keychain_update_existing_key(storage, logger):
    """Test updating an existing key."""
    keychain = KeyChain(storage, logger, "test")
    await keychain.init()
    
    from walletkit.utils.crypto_utils import generate_random_bytes32
    key1 = generate_random_bytes32()
    key2 = generate_random_bytes32()
    
    await keychain.set("test_key", key1)
    assert keychain.get("test_key") == key1
    
    await keychain.set("test_key", key2)
    assert keychain.get("test_key") == key2
    assert keychain.get("test_key") != key1

