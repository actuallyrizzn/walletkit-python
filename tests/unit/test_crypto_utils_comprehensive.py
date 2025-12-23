"""Comprehensive tests for crypto utilities."""
import pytest

from walletkit.utils.crypto_utils import (
    generate_key_pair,
    derive_sym_key,
    hash_key,
    hash_message,
    bytes_to_hex,
    hex_to_bytes,
    generate_random_bytes32,
    to_base64url,
    from_base64url,
)


def test_to_base64url_from_base64url():
    """Test base64url conversion."""
    import base64
    
    # Test with a simple string that will encode properly
    original = "test data"
    base64_str = base64.b64encode(original.encode()).decode()
    
    base64url = to_base64url(base64_str)
    assert "+" not in base64url
    assert "/" not in base64url
    assert "=" not in base64url
    
    converted_back = from_base64url(base64url)
    # Should decode back to original base64
    decoded = base64.b64decode(converted_back).decode()
    assert decoded == original


def test_hash_key_consistency():
    """Test that hash_key produces consistent results."""
    key = generate_random_bytes32()
    
    hash1 = hash_key(key)
    hash2 = hash_key(key)
    
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) > 0


def test_hash_message_consistency():
    """Test that hash_message produces consistent results."""
    message = "test message"
    
    hash1 = hash_message(message)
    hash2 = hash_message(message)
    
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) > 0


def test_derive_sym_key_consistency():
    """Test that derive_sym_key produces consistent results."""
    private_key = generate_random_bytes32()
    public_key = generate_random_bytes32()
    
    sym_key1 = derive_sym_key(private_key, public_key)
    sym_key2 = derive_sym_key(private_key, public_key)
    
    assert sym_key1 == sym_key2
    assert len(sym_key1) == 64  # 32 bytes = 64 hex chars


def test_derive_sym_key_with_keypair():
    """Test deriving symmetric key with a proper key pair."""
    # Generate a key pair
    keypair1 = generate_key_pair()
    keypair2 = generate_key_pair()
    
    # Derive shared keys
    sym_key1 = derive_sym_key(keypair1["privateKey"], keypair2["publicKey"])
    sym_key2 = derive_sym_key(keypair2["privateKey"], keypair1["publicKey"])
    
    # Should produce same shared key (X25519 is commutative)
    assert sym_key1 == sym_key2
    assert len(sym_key1) == 64

