"""Tests for Crypto controller."""
import json

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


@pytest.mark.asyncio
async def test_crypto_has_keys(crypto):
    """Test has_keys method."""
    public_key = await crypto.generate_key_pair()
    assert crypto.has_keys(public_key) is True
    assert crypto.has_keys("nonexistent") is False


@pytest.mark.asyncio
async def test_crypto_get_client_id(crypto):
    """Test get_client_id method."""
    client_id = await crypto.get_client_id()
    assert client_id is not None
    # WalletConnect relay-auth uses a did:key issuer
    assert isinstance(client_id, str)
    assert client_id.startswith("did:key:")
    
    # Should return same ID on subsequent calls
    client_id2 = await crypto.get_client_id()
    assert client_id == client_id2


@pytest.mark.asyncio
async def test_crypto_sign_jwt(crypto):
    """Test sign_jwt method."""
    jwt = await crypto.sign_jwt("https://relay.walletconnect.com")
    assert jwt is not None
    assert isinstance(jwt, str)
    parts = jwt.split(".")
    assert len(parts) == 3

    import base64

    def b64url_decode(s: str) -> bytes:
        pad = "=" * ((4 - (len(s) % 4)) % 4)
        return base64.urlsafe_b64decode((s + pad).encode("utf-8"))

    header = json.loads(b64url_decode(parts[0]).decode("utf-8"))
    payload = json.loads(b64url_decode(parts[1]).decode("utf-8"))

    assert header["alg"] == "EdDSA"
    assert header["typ"] == "JWT"
    assert payload["aud"] == "https://relay.walletconnect.com"
    assert payload["iss"].startswith("did:key:")


@pytest.mark.asyncio
async def test_crypto_generate_shared_key(crypto):
    """Test generate_shared_key method."""
    # Generate two key pairs
    public_key1 = await crypto.generate_key_pair()
    public_key2 = await crypto.generate_key_pair()
    
    # Generate shared key
    topic = await crypto.generate_shared_key(public_key1, public_key2)
    assert topic is not None
    assert crypto.has_keys(topic)


@pytest.mark.asyncio
async def test_crypto_generate_shared_key_with_override(crypto):
    """Test generate_shared_key with override topic."""
    public_key1 = await crypto.generate_key_pair()
    public_key2 = await crypto.generate_key_pair()
    
    override_topic = "custom_topic"
    topic = await crypto.generate_shared_key(public_key1, public_key2, override_topic=override_topic)
    assert topic == override_topic


@pytest.mark.asyncio
async def test_crypto_delete_key_pair(crypto):
    """Test delete_key_pair method."""
    public_key = await crypto.generate_key_pair()
    assert crypto.has_keys(public_key) is True
    
    await crypto.delete_key_pair(public_key)
    assert crypto.has_keys(public_key) is False


@pytest.mark.asyncio
async def test_crypto_delete_sym_key(crypto):
    """Test delete_sym_key method."""
    sym_key = "a" * 64
    topic = await crypto.set_sym_key(sym_key)
    assert crypto.has_keys(topic) is True
    
    await crypto.delete_sym_key(topic)
    assert crypto.has_keys(topic) is False


@pytest.mark.asyncio
async def test_crypto_encode_type2(crypto):
    """Test encode with TYPE_2 envelope."""
    from walletkit.utils.crypto_utils import TYPE_2
    
    payload = {"jsonrpc": "2.0", "method": "test", "id": 1}
    encoded = await crypto.encode("dummy_topic", payload, opts={"type": TYPE_2})
    
    assert encoded is not None
    # TYPE_2 is unencrypted, should be able to decode without key
    from walletkit.utils.crypto_utils import decode_type_two_envelope
    decoded = decode_type_two_envelope(encoded)
    assert json.loads(decoded) == payload


@pytest.mark.asyncio
async def test_crypto_encode_type1(crypto):
    """Test encode with TYPE_1 envelope."""
    from walletkit.utils.crypto_utils import TYPE_1
    
    # Generate key pairs
    sender_public = await crypto.generate_key_pair()
    receiver_public = await crypto.generate_key_pair()
    
    payload = {"jsonrpc": "2.0", "method": "test", "id": 1}
    encoded = await crypto.encode(
        "dummy_topic",
        payload,
        opts={
            "type": TYPE_1,
            "senderPublicKey": sender_public,
            "receiverPublicKey": receiver_public,
        }
    )
    
    assert encoded is not None


@pytest.mark.asyncio
async def test_crypto_encode_type1_missing_keys(crypto):
    """Test encode TYPE_1 with missing keys."""
    from walletkit.utils.crypto_utils import TYPE_1
    
    payload = {"jsonrpc": "2.0", "method": "test", "id": 1}
    
    with pytest.raises(ValueError, match="Type 1 envelope requires"):
        await crypto.encode(
            "dummy_topic",
            payload,
            opts={"type": TYPE_1}
        )


@pytest.mark.asyncio
async def test_crypto_decode_type2(crypto):
    """Test decode with TYPE_2 envelope."""
    from walletkit.utils.crypto_utils import TYPE_2, encode_type_two_envelope
    
    payload = {"jsonrpc": "2.0", "method": "test", "id": 1}
    encoded = encode_type_two_envelope(json.dumps(payload))
    
    decoded = await crypto.decode("dummy_topic", encoded, opts={"type": TYPE_2})
    assert decoded == payload


@pytest.mark.asyncio
async def test_crypto_decode_type1(crypto):
    """Test decode with TYPE_1 envelope."""
    from walletkit.utils.crypto_utils import TYPE_1
    
    # Generate key pairs and set up shared key
    sender_public = await crypto.generate_key_pair()
    receiver_public = await crypto.generate_key_pair()
    
    # Generate shared key
    topic = await crypto.generate_shared_key(sender_public, receiver_public)
    
    # Encode with TYPE_1
    payload = {"jsonrpc": "2.0", "method": "test", "id": 1}
    encoded = await crypto.encode(
        topic,
        payload,
        opts={
            "type": TYPE_1,
            "senderPublicKey": sender_public,
            "receiverPublicKey": receiver_public,
        }
    )
    
    # Decode
    decoded = await crypto.decode(
        topic,
        encoded,
        opts={
            "type": TYPE_1,
            "receiverPublicKey": receiver_public,
        }
    )
    assert decoded == payload


@pytest.mark.asyncio
async def test_crypto_encode_base64url(crypto):
    """Test encode with base64url encoding."""
    from walletkit.utils.crypto_utils import BASE64URL
    
    sym_key = "a" * 64
    topic = await crypto.set_sym_key(sym_key)
    
    payload = {"jsonrpc": "2.0", "method": "test", "id": 1}
    encoded = await crypto.encode(topic, payload, opts={"encoding": BASE64URL})
    
    assert encoded is not None
    # Should be able to decode
    decoded = await crypto.decode(topic, encoded, opts={"encoding": BASE64URL})
    assert decoded == payload


@pytest.mark.asyncio
async def test_crypto_check_initialized(storage, logger):
    """Test _check_initialized raises error when not initialized."""
    crypto = Crypto(storage, logger)
    
    with pytest.raises(RuntimeError, match="not initialized"):
        await crypto.generate_key_pair()
    
    with pytest.raises(RuntimeError, match="not initialized"):
        await crypto.set_sym_key("a" * 64)
    
    with pytest.raises(RuntimeError, match="not initialized"):
        crypto.has_keys("key")
