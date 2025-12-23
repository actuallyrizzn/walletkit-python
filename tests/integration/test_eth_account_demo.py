"""Demo test showing Ethereum account creation and signing."""
import pytest
from walletkit.utils.ethereum_signing import (
    generate_test_account,
    sign_personal_message,
    get_address_from_private_key,
)


def test_generate_test_account():
    """Test generating a test Ethereum account."""
    account = generate_test_account()
    
    assert "private_key" in account
    assert "address" in account
    assert len(account["private_key"]) == 64  # 32 bytes in hex
    assert account["address"].startswith("0x")
    assert len(account["address"]) == 42  # 0x + 40 hex chars
    
    print(f"\n[OK] Generated test account:")
    print(f"   Address: {account['address']}")
    print(f"   Private Key: {account['private_key'][:20]}... (hidden)")


def test_sign_message():
    """Test signing a message with the test account."""
    account = generate_test_account()
    message = "Hello Venice.ai - this is a test token"
    
    signature = sign_personal_message(account["private_key"], message)
    
    assert signature.startswith("0x")
    assert len(signature) == 132  # 0x + 130 hex chars (65 bytes)
    
    print(f"\n[OK] Signed message:")
    print(f"   Message: {message}")
    print(f"   Signature: {signature[:30]}...")
    print(f"   Address: {account['address']}")


def test_address_from_private_key():
    """Test getting address from private key."""
    account = generate_test_account()
    private_key = account["private_key"]
    expected_address = account["address"]
    
    derived_address = get_address_from_private_key(private_key)
    
    assert derived_address == expected_address
    assert derived_address.startswith("0x")
    
    print(f"\n[OK] Address derivation:")
    print(f"   Private Key: {private_key[:20]}...")
    print(f"   Derived Address: {derived_address}")


def test_venice_ai_signing_flow():
    """Simulate the venice.ai signing flow."""
    # Step 1: Generate account (or load from env in production)
    account = generate_test_account()
    print(f"\n[KEY] Test Account Created:")
    print(f"   Address: {account['address']}")
    
    # Step 2: Venice.ai sends a token to sign
    venice_token = "venice.ai authentication token: 1234567890abcdef"
    print(f"\n[TOKEN] Venice.ai Token:")
    print(f"   Token: {venice_token}")
    
    # Step 3: Sign the token
    signature = sign_personal_message(account["private_key"], venice_token)
    print(f"\n[SIGN] Signature Created:")
    print(f"   Signature: {signature}")
    
    # Step 4: Verify (in real scenario, venice.ai would verify)
    assert signature.startswith("0x")
    assert len(signature) == 132
    
    print(f"\n[OK] Complete! This signature would be sent to venice.ai")
    print(f"   Venice.ai would verify it matches address: {account['address']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

