"""Tests for crypto utilities."""
import pytest

from walletkit.utils.crypto_utils import (
    BASE64,
    TYPE_0,
    TYPE_1,
    decrypt_message,
    derive_sym_key,
    encrypt_message,
    generate_key_pair,
    generate_random_bytes32,
    hash_key,
)


def test_generate_key_pair():
    """Test key pair generation."""
    key_pair = generate_key_pair()
    assert "privateKey" in key_pair
    assert "publicKey" in key_pair
    assert len(key_pair["privateKey"]) == 64  # 32 bytes = 64 hex chars
    assert len(key_pair["publicKey"]) == 64


def test_generate_random_bytes32():
    """Test random bytes generation."""
    random = generate_random_bytes32()
    assert len(random) == 64  # 32 bytes = 64 hex chars
    assert random != generate_random_bytes32()  # Should be different


def test_derive_sym_key():
    """Test symmetric key derivation."""
    key_pair_a = generate_key_pair()
    key_pair_b = generate_key_pair()
    
    sym_key = derive_sym_key(key_pair_a["privateKey"], key_pair_b["publicKey"])
    assert len(sym_key) == 64
    
    # Should be same when reversed
    sym_key2 = derive_sym_key(key_pair_b["privateKey"], key_pair_a["publicKey"])
    assert sym_key == sym_key2


def test_hash_key():
    """Test key hashing."""
    key = generate_random_bytes32()
    hashed = hash_key(key)
    assert len(hashed) == 64
    assert hashed != key


def test_encrypt_decrypt():
    """Test encryption and decryption."""
    sym_key = generate_random_bytes32()
    message = "test message"
    
    encrypted = encrypt_message(sym_key, message)
    decrypted = decrypt_message(sym_key, encrypted)
    
    assert decrypted == message


def test_encrypt_decrypt_type1():
    """Test type 1 envelope encryption."""
    key_pair_a = generate_key_pair()
    key_pair_b = generate_key_pair()
    
    # Derive shared key
    sym_key = derive_sym_key(key_pair_a["privateKey"], key_pair_b["publicKey"])
    
    message = "test message"
    encrypted = encrypt_message(
        sym_key,
        message,
        type_val=TYPE_1,
        sender_public_key=key_pair_a["publicKey"],
    )
    
    decrypted = decrypt_message(sym_key, encrypted)
    assert decrypted == message

