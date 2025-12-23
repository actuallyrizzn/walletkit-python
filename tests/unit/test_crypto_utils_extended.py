"""Extended tests for crypto utilities."""
import pytest

from walletkit.utils.crypto_utils import (
    generate_random_bytes32,
    derive_sym_key,
    hash_message,
    hash_key,
    generate_key_pair,
    bytes_to_hex,
    hex_to_bytes,
)


def test_generate_random_bytes32():
    """Test generating random bytes."""
    key1 = generate_random_bytes32()
    key2 = generate_random_bytes32()
    
    # Returns hex string, so 32 bytes = 64 hex characters
    assert len(key1) == 64
    assert len(key2) == 64
    assert key1 != key2  # Should be different


def test_hash_message():
    """Test message hashing."""
    data = "test data"
    hash1 = hash_message(data)
    hash2 = hash_message(data)
    
    assert isinstance(hash1, str)
    assert hash1 == hash2  # Same input should produce same hash
    
    # Different input should produce different hash
    hash3 = hash_message("different data")
    assert hash1 != hash3


def test_hash_key():
    """Test key hashing."""
    key = generate_random_bytes32()
    hash1 = hash_key(key)
    hash2 = hash_key(key)
    
    assert isinstance(hash1, str)
    assert hash1 == hash2  # Same input should produce same hash
    
    # Different input should produce different hash
    key2 = generate_random_bytes32()
    hash3 = hash_key(key2)
    assert hash1 != hash3


def test_derive_sym_key():
    """Test symmetric key derivation."""
    private_key = generate_random_bytes32()
    public_key = generate_random_bytes32()
    
    sym_key1 = derive_sym_key(private_key, public_key)
    sym_key2 = derive_sym_key(private_key, public_key)
    
    # Returns hex string, so 32 bytes = 64 hex characters
    assert len(sym_key1) == 64
    assert sym_key1 == sym_key2  # Same inputs should produce same key


def test_generate_key_pair():
    """Test generating X25519 key pair."""
    keypair1 = generate_key_pair()
    keypair2 = generate_key_pair()
    
    assert "privateKey" in keypair1
    assert "publicKey" in keypair1
    assert len(keypair1["privateKey"]) == 64  # 32 bytes = 64 hex chars
    assert len(keypair1["publicKey"]) == 64
    
    # Should generate different keys
    assert keypair1["privateKey"] != keypair2["privateKey"]
    assert keypair1["publicKey"] != keypair2["publicKey"]


def test_bytes_hex_conversion():
    """Test bytes to hex and hex to bytes conversion."""
    original = b"test data"
    
    hex_str = bytes_to_hex(original)
    assert isinstance(hex_str, str)
    assert len(hex_str) == len(original) * 2
    
    converted_back = hex_to_bytes(hex_str)
    assert converted_back == original

