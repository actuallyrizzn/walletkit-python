"""Tests for crypto utilities."""
import base64
import pytest

from walletkit.utils.crypto_utils import (
    BASE64,
    TYPE_0,
    TYPE_1,
    encode_type_byte,
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


def test_encode_type_byte_is_single_raw_byte():
    """WalletConnect type byte must be a single raw byte (not ASCII digit)."""
    assert encode_type_byte(0) == b"\x00"
    assert encode_type_byte(1) == b"\x01"
    assert encode_type_byte(2) == b"\x02"


def test_envelope_type_byte_roundtrip_base64():
    """Ensure base64 envelope decodes to the correct raw type byte at position 0."""
    sym_key = generate_random_bytes32()
    msg = "hello"

    enc0 = encrypt_message(sym_key, msg, type_val=TYPE_0, encoding=BASE64)
    raw0 = base64.b64decode(enc0)
    assert raw0[0] == 0

    kp = generate_key_pair()
    enc1 = encrypt_message(sym_key, msg, type_val=TYPE_1, sender_public_key=kp["publicKey"], encoding=BASE64)
    raw1 = base64.b64decode(enc1)
    assert raw1[0] == 1


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


def test_encrypt_decrypt_base64url():
    """Test encryption/decryption with base64url encoding."""
    from walletkit.utils.crypto_utils import BASE64URL
    
    sym_key = generate_random_bytes32()
    message = "test message"
    
    encrypted = encrypt_message(sym_key, message, encoding=BASE64URL)
    decrypted = decrypt_message(sym_key, encrypted, encoding=BASE64URL)
    
    assert decrypted == message


def test_encrypt_message_type1_missing_key():
    """Test encrypt_message type 1 with missing sender key."""
    sym_key = generate_random_bytes32()
    
    with pytest.raises(ValueError, match="Missing sender public key"):
        encrypt_message(
            sym_key,
            "test",
            type_val=TYPE_1,
            sender_public_key=None,
        )


def test_decrypt_message_error():
    """Test decrypt_message error handling."""
    sym_key = generate_random_bytes32()
    
    # Use a valid base64 string that will fail during decryption
    # Create a valid base64 envelope but with wrong key
    from walletkit.utils.crypto_utils import encrypt_message, TYPE_0
    wrong_key = generate_random_bytes32()
    encrypted = encrypt_message(wrong_key, "test", type_val=TYPE_0)
    
    # Try to decrypt with different key - should fail
    with pytest.raises(ValueError, match="Failed to decrypt"):
        decrypt_message(sym_key, encrypted)


def test_encode_decode_type_two():
    """Test type 2 envelope encoding/decoding."""
    from walletkit.utils.crypto_utils import (
        encode_type_two_envelope,
        decode_type_two_envelope,
    )
    
    message = "test message"
    encoded = encode_type_two_envelope(message)
    decoded = decode_type_two_envelope(encoded)
    
    assert decoded == message


def test_encode_decode_type_two_base64url():
    """Test type 2 envelope with base64url encoding."""
    from walletkit.utils.crypto_utils import (
        encode_type_two_envelope,
        decode_type_two_envelope,
        BASE64URL,
    )
    
    message = "test message"
    encoded = encode_type_two_envelope(message, encoding=BASE64URL)
    decoded = decode_type_two_envelope(encoded, encoding=BASE64URL)
    
    assert decoded == message


def test_get_payload_type():
    """Test get_payload_type function."""
    from walletkit.utils.crypto_utils import get_payload_type, TYPE_0, TYPE_1, TYPE_2
    
    sym_key = generate_random_bytes32()
    message = "test"
    
    # Test TYPE_0
    encrypted = encrypt_message(sym_key, message, type_val=TYPE_0)
    payload_type = get_payload_type(encrypted)
    assert payload_type == TYPE_0
    
    # Test TYPE_1
    key_pair = generate_key_pair()
    encrypted = encrypt_message(
        sym_key,
        message,
        type_val=TYPE_1,
        sender_public_key=key_pair["publicKey"],
    )
    payload_type = get_payload_type(encrypted)
    assert payload_type == TYPE_1
    
    # Test TYPE_2
    from walletkit.utils.crypto_utils import encode_type_two_envelope
    encoded = encode_type_two_envelope(message)
    payload_type = get_payload_type(encoded)
    assert payload_type == TYPE_2


def test_get_payload_sender_public_key():
    """Test get_payload_sender_public_key function."""
    from walletkit.utils.crypto_utils import get_payload_sender_public_key
    
    key_pair = generate_key_pair()
    key_pair_b = generate_key_pair()
    sym_key = derive_sym_key(key_pair["privateKey"], key_pair_b["publicKey"])
    
    # TYPE_1 should have sender public key
    encrypted = encrypt_message(
        sym_key,
        "test",
        type_val=TYPE_1,
        sender_public_key=key_pair["publicKey"],
    )
    sender_key = get_payload_sender_public_key(encrypted)
    assert sender_key == key_pair["publicKey"]
    
    # TYPE_0 should not have sender public key
    encrypted = encrypt_message(sym_key, "test", type_val=TYPE_0)
    sender_key = get_payload_sender_public_key(encrypted)
    assert sender_key is None


def test_encrypt_message_with_iv():
    """Test encrypt_message with custom IV."""
    from walletkit.utils.crypto_utils import generate_random_bytes32
    
    sym_key = generate_random_bytes32()
    iv = generate_random_bytes32()[:24]  # 12 bytes in hex = 24 chars
    
    message = "test message"
    encrypted1 = encrypt_message(sym_key, message, iv=iv)
    encrypted2 = encrypt_message(sym_key, message, iv=iv)
    
    # Same IV should produce same encrypted result
    assert encrypted1 == encrypted2
