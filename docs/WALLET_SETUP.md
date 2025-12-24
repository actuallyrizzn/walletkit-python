# Wallet Setup for Integration Testing

## What You Need

**YES, you need an actual Ethereum wallet with private keys to sign messages.**

Here's what's happening:

1. **WalletConnect Protocol** (handled by your WalletKit library):
   - Connects to venice.ai via WalletConnect
   - Handles the pairing and session establishment
   - Encrypts/decrypts messages using X25519 keys

2. **Ethereum Signing** (separate, requires private keys):
   - When venice.ai asks you to sign a token, you need to actually sign it
   - This requires an Ethereum private key
   - The signature proves you own the address

## What's Installed

✅ **eth-account** - Python library for Ethereum signing
- Installed in your venv
- Can sign messages with private keys
- Generates Ethereum addresses from private keys

## How It Works

### 1. Private Key → Address

```python
from walletkit.utils.ethereum_signing import get_address_from_private_key

private_key = "0x..." # Your private key (64 hex chars)
address = get_address_from_private_key(private_key)
# Returns: "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
```

### 2. Signing Messages

```python
from walletkit.utils.ethereum_signing import sign_personal_message

private_key = "0x..." # Your private key
message = "Hello Venice.ai" # The token venice.ai wants signed
signature = sign_personal_message(private_key, message)
# Returns: "0x1234abcd..." (65 bytes, 130 hex chars)
```

### 3. In Your Test

The test automatically:
1. Generates a test Ethereum account (or uses one you provide)
2. Uses that account's private key to sign messages
3. Returns signatures to venice.ai via WalletConnect

## Using Your Own Private Key

**For testing**, you can use a test account (automatically generated).

**For production/testing with real accounts**, you need to:

1. **Get a private key**:
   - From MetaMask: Settings → Security & Privacy → Show Private Key
   - From a hardware wallet (export if supported)
   - Generate a new one (for testing only!)

2. **Set it in your test**:

```python
# In test_venice_ai_example.py, modify the fixture:

@pytest.fixture
def ethereum_account():
    """Use your own private key."""
    private_key = os.getenv("ETHEREUM_PRIVATE_KEY", "")
    if not private_key:
        # Fallback to test account
        return generate_test_account()
    
    return {
        "private_key": private_key,
        "address": get_address_from_private_key(private_key),
    }
```

3. **Set environment variable**:

```powershell
$env:ETHEREUM_PRIVATE_KEY = "0x1234567890abcdef..." # Your private key
```

## Security Warning

⚠️ **NEVER commit private keys to git**
⚠️ **NEVER share private keys**
⚠️ **Test accounts are fine for testing, but use real accounts carefully**

## What Venice.ai Does

1. Venice.ai displays WalletConnect QR code
2. Your wallet connects via WalletConnect
3. Venice.ai sends a `personal_sign` request with a token
4. Your wallet signs the token with the private key
5. Venice.ai verifies the signature matches the address
6. Venice.ai generates an API key for that address

## The Flow

```
Venice.ai                    Your Wallet
    |                            |
    |-- WalletConnect URI ------>|
    |                            | (WalletKit handles connection)
    |<-- Session Approved -------|
    |                            |
    |-- personal_sign(token) ---->|
    |                            | (eth-account signs with private key)
    |<-- signature --------------|
    |                            |
    | (Venice.ai verifies signature)
    | (Generates API key)
```

## Files Created

- `src/walletkit/utils/ethereum_signing.py` - Signing utilities
- `tests/integration/test_venice_ai_example.py` - Updated with real signing
- `requirements-dev.txt` - Updated with eth-account

## Running the Test

```powershell
# Set your WalletConnect Project ID
$env:WALLETCONNECT_PROJECT_ID = "your-project-id"

# Optional: Use your own private key (otherwise generates test account)
$env:ETHEREUM_PRIVATE_KEY = "0x..." 

# Run the test
pytest tests/integration/test_venice_ai_example.py -v -s
```

The test will:
1. Open venice.ai in a browser
2. Extract WalletConnect URI
3. Connect your wallet
4. When venice.ai requests signing, actually sign with the private key
5. Return the signature

## License

This documentation is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License (CC-BY-SA-4.0). See [LICENSE-DOCS](../LICENSE-DOCS) for details.

