"""Tests for Crypto controller."""
import pytest

from walletkit.controllers.crypto import Crypto
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
        def error(self, msg: str) -> None:
            pass

    return SimpleLogger()


@pytest.fixture
async def crypto(storage, logger):
    """Create and initialize crypto controller."""
    crypto = Crypto(storage, logger)
    await crypto.init()
    return crypto


@pytest.mark.asyncio
async def test_crypto_init(crypto):
    """Test crypto initialization."""
    assert crypto._initialized is True


@pytest.mark.asyncio
async def test_crypto_generate_key_pair(crypto):
    """Test key pair generation."""
    public_key = await crypto.generate_key_pair()
    assert len(public_key) == 64
    assert crypto.has_keys(public_key)


@pytest.mark.asyncio
async def test_crypto_set_get_sym_key(crypto):
    """Test symmetric key operations."""
    sym_key = "a" * 64  # 32 bytes hex
    topic = await crypto.set_sym_key(sym_key)
    assert topic is not None
    assert crypto.has_keys(topic)


@pytest.mark.asyncio
async def test_crypto_encode_decode(crypto):
    """Test encode/decode operations."""
    # Set up symmetric key
    sym_key = "a" * 64
    topic = await crypto.set_sym_key(sym_key)
    
    # Encode
    payload = {"jsonrpc": "2.0", "method": "test", "id": 1}
    encoded = await crypto.encode(topic, payload)
    assert encoded is not None
    
    # Decode
    decoded = await crypto.decode(topic, encoded)
    assert decoded == payload

