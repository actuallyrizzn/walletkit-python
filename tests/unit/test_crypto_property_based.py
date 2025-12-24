"""Property-based tests for crypto operations."""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck

from walletkit.utils.crypto_utils import derive_sym_key, encrypt_message, decrypt_message, generate_key_pair


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
@given(
    message=st.text(min_size=1, max_size=1000)
)
def test_crypto_encrypt_decrypt_roundtrip(message):
    """Property-based test: encrypt then decrypt should return original message."""
    # Generate key pairs
    key_a = generate_key_pair()
    key_b = generate_key_pair()
    
    # Derive symmetric key
    sym_key = derive_sym_key(key_a["privateKey"], key_b["publicKey"])
    
    # Encrypt
    encrypted = encrypt_message(sym_key, message)
    
    # Decrypt
    decrypted = decrypt_message(sym_key, encrypted)
    
    # Should match original
    assert decrypted == message


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=20)
@given(
    message1=st.text(min_size=1, max_size=100),
    message2=st.text(min_size=1, max_size=100)
)
def test_crypto_encrypt_different_data_different_output(message1, message2):
    """Property-based test: different messages should produce different encrypted output."""
    if message1 == message2:
        pytest.skip("Messages are the same")
    
    # Generate key pairs
    key_a = generate_key_pair()
    key_b = generate_key_pair()
    
    # Derive symmetric key
    sym_key = derive_sym_key(key_a["privateKey"], key_b["publicKey"])
    
    # Encrypt both
    encrypted1 = encrypt_message(sym_key, message1)
    encrypted2 = encrypt_message(sym_key, message2)
    
    # Should be different (very high probability due to nonce)
    assert encrypted1 != encrypted2


def test_crypto_sym_key_derivation_deterministic():
    """Test: symmetric key derivation should be deterministic."""
    # Generate two key pairs
    key_a = generate_key_pair()
    key_b = generate_key_pair()
    
    # Derive symmetric key twice with same inputs
    derived1 = derive_sym_key(key_a["privateKey"], key_b["publicKey"])
    derived2 = derive_sym_key(key_a["privateKey"], key_b["publicKey"])
    
    # Should be the same
    assert derived1 == derived2
    
    # Different key pair should produce different symmetric key
    key_c = generate_key_pair()
    derived3 = derive_sym_key(key_a["privateKey"], key_c["publicKey"])
    assert derived1 != derived3
