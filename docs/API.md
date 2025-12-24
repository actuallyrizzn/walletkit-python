# WalletKit Python API Reference

Complete API documentation for the WalletKit Python SDK.

## Table of Contents

1. [Core](#core)
2. [WalletKit Client](#walletkit-client)
3. [SignClient](#signclient)
4. [Controllers](#controllers)
5. [Utilities](#utilities)

## Core

### `Core`

Main orchestrator for all WalletConnect controllers.

#### Initialization

```python
from walletkit import Core
from walletkit.utils.storage import MemoryStorage

storage = MemoryStorage()
core = Core(
    project_id="your-project-id",
    relay_url="wss://relay.walletconnect.com",  # Optional
    storage=storage,  # Optional, defaults to MemoryStorage
    logger=None,  # Optional, defaults to SimpleLogger
    storage_prefix="wc@2:core:",  # Optional
)

await core.start()
```

#### Properties

- `core.crypto` - Crypto controller instance
- `core.relayer` - Relayer controller instance
- `core.pairing` - Pairing controller instance
- `core.expirer` - Expirer controller instance
- `core.event_client` - EventClient instance
- `core.echo_client` - EchoClient instance
- `core.storage` - Storage backend
- `core.logger` - Logger instance
- `core.events` - EventEmitter for core events

#### Methods

- `await core.start()` - Initialize all controllers

## WalletKit Client

### `WalletKit`

Main client API for wallet and dApp integration.

#### Initialization

```python
from walletkit import WalletKit, Core
from walletkit.utils.storage import MemoryStorage

storage = MemoryStorage()
core = Core(project_id="your-project-id", storage=storage)
await core.start()

wallet = await WalletKit.init({
    "core": core,
    "metadata": {
        "name": "My Wallet",
        "description": "Wallet Description",
        "url": "https://mywallet.com",
        "icons": ["https://mywallet.com/icon.png"],
    },
})
```

#### Methods

##### Pairing

- `await wallet.pair(uri: str)` - Pair with a WalletConnect URI

##### Session Management

- `await wallet.approve_session(id: int, namespaces: dict, ...)` - Approve a session proposal
- `await wallet.reject_session(id: int, reason: dict)` - Reject a session proposal
- `wallet.get_active_sessions()` - Get all active sessions
- `wallet.get_pending_session_proposals()` - Get pending proposals
- `await wallet.update_session(topic: str, namespaces: dict)` - Update session namespaces
- `await wallet.extend_session(topic: str)` - Extend session expiry
- `await wallet.disconnect_session(topic: str, reason: dict)` - Disconnect a session

##### Request Handling

- `wallet.get_pending_session_requests()` - Get pending session requests
- `await wallet.respond_session_request(topic: str, response: dict)` - Respond to a request

##### Events

- `wallet.on(event: str, listener: callable)` - Register event listener
- `wallet.once(event: str, listener: callable)` - Register one-time listener
- `wallet.off(event: str, listener: callable)` - Remove event listener

#### Events

- `session_proposal` - Emitted when a session proposal is received
- `session_approve` - Emitted when a session is approved
- `session_reject` - Emitted when a session is rejected
- `session_request` - Emitted when a session request is received
- `session_update` - Emitted when a session is updated
- `session_extend` - Emitted when a session is extended
- `session_delete` - Emitted when a session is deleted
- `session_authenticate` - Emitted when authentication is requested

## SignClient

### `SignClient`

Low-level Sign Protocol client.

#### Methods

##### Session Proposal

- `await sign_client.approve(params: dict)` - Approve session proposal
  - `params.id` - Proposal ID
  - `params.namespaces` - Session namespaces
  - Returns: `{"topic": str, "acknowledged": callable}`

- `await sign_client.reject(params: dict)` - Reject session proposal
  - `params.id` - Proposal ID
  - `params.reason` - Rejection reason

##### Session Management

- `await sign_client.update(params: dict)` - Update session
  - `params.topic` - Session topic
  - `params.namespaces` - Updated namespaces

- `await sign_client.extend(params: dict)` - Extend session
  - `params.topic` - Session topic

- `await sign_client.disconnect(params: dict)` - Disconnect session
  - `params.topic` - Session topic
  - `params.reason` - Disconnect reason

##### Request/Response

- `await sign_client.respond(params: dict)` - Respond to request
  - `params.topic` - Session topic
  - `params.response` - JSON-RPC response

- `sign_client.get_pending_session_requests()` - Get pending requests

##### Events

- `await sign_client.emit(params: dict)` - Emit session event
  - `params.topic` - Session topic
  - `params.event` - Event data
  - `params.chainId` - Chain ID

##### Authentication

- `await sign_client.approve_session_authenticate(params: dict)` - Approve auth
  - `params.id` - Auth request ID
  - `params.auths` - List of auth objects (CACAO)

- `await sign_client.reject_session_authenticate(params: dict)` - Reject auth
  - `params.id` - Auth request ID
  - `params.reason` - Rejection reason

- `sign_client.format_auth_message(params: dict)` - Format auth message
  - `params.request` - Auth request payload
  - `params.iss` - Issuer (e.g., "did:pkh:eip155:1:0x...")
  - Returns: Formatted message string

## Controllers

### `Relayer`

WebSocket communication controller.

#### Methods

- `await relayer.init()` - Initialize relayer
- `await relayer.connect(relay_url: str = None)` - Connect to relay
- `await relayer.disconnect()` - Disconnect from relay
- `await relayer.publish(topic: str, message: str, opts: dict = None)` - Publish message
- `await relayer.subscribe(topic: str, opts: dict = None)` - Subscribe to topic
- `await relayer.unsubscribe(topic: str, opts: dict = None)` - Unsubscribe from topic

#### Properties

- `relayer.connected` - Connection status
- `relayer.connecting` - Connecting status

#### Events

- `connect` - Emitted on connection
- `disconnect` - Emitted on disconnection
- `message` - Emitted on message receipt
- `subscribe` - Emitted on subscription
- `unsubscribe` - Emitted on unsubscription

### `Crypto`

Encryption/decryption controller.

#### Methods

- `await crypto.init()` - Initialize crypto
- `await crypto.encode(topic: str, payload: dict)` - Encode message
- `await crypto.decode(topic: str, encoded: str)` - Decode message
- `await crypto.set_sym_key(sym_key: bytes, override_topic: str = None)` - Set symmetric key

### `Pairing`

Pairing management controller.

#### Methods

- `await pairing.init()` - Initialize pairing
- `await pairing.create(params: dict)` - Create pairing
  - `params.methods` - List of supported methods
  - Returns: `{"uri": str, "topic": str}`

### `Expirer`

Expiration management controller.

#### Methods

- `await expirer.init()` - Initialize expirer
- `expirer.set(key: str | int, expiry: int)` - Set expiration
- `expirer.has(key: str | int)` - Check if key has expiration
- `expirer.get(key: str | int)` - Get expiration
- `expirer.delete(key: str | int)` - Delete expiration

## Utilities

### Storage

#### `MemoryStorage`

In-memory storage backend.

```python
from walletkit.utils.storage import MemoryStorage

storage = MemoryStorage()
await storage.set_item("key", "value")
value = await storage.get_item("key")
await storage.remove_item("key")
```

#### `FileStorage`

File-based storage backend.

```python
from walletkit.utils.storage import FileStorage

storage = FileStorage(data_dir="./data")
await storage.set_item("key", "value")
```

### Events

#### `EventEmitter`

Async event emitter.

```python
from walletkit.utils.events import EventEmitter

emitter = EventEmitter()

# Register listener
emitter.on("event", async def handler(data):
    print(data)

# Emit event
await emitter.emit("event", {"key": "value"})

# One-time listener
emitter.once("event", handler)

# Remove listener
emitter.off("event", handler)
```

### JSON-RPC

#### Utilities

```python
from walletkit.utils.jsonrpc import (
    format_jsonrpc_request,
    format_jsonrpc_result,
    format_jsonrpc_error,
    get_big_int_rpc_id,
)

# Create request
request = format_jsonrpc_request(
    method="eth_sendTransaction",
    params={"to": "0x...", "value": "0x0"},
)

# Create result
result = format_jsonrpc_result(id=1, result="0x123")

# Create error
error = format_jsonrpc_error(id=1, code=-32000, message="Error")
```

### Crypto Utils

```python
from walletkit.utils.crypto_utils import (
    generate_random_bytes32,
    derive_sym_key,
    encrypt,
    decrypt,
)

# Generate random bytes
key = generate_random_bytes32()

# Derive symmetric key
sym_key = derive_sym_key(shared_secret, salt)

# Encrypt/decrypt
encrypted = encrypt(data, key, nonce)
decrypted = decrypt(encrypted, key, nonce)
```

### URI

```python
from walletkit.utils.uri import parse_uri, format_uri

# Parse URI
parsed = parse_uri("wc:topic@version?relay-protocol=irn&symKey=...")

# Format URI
uri = format_uri(topic, version, relay_protocol, sym_key)
```

## Error Handling

### Common Exceptions

- `ValueError` - Invalid parameters
- `KeyError` - Missing keys/records
- `RuntimeError` - Initialization errors
- `TimeoutError` - Operation timeout
- `ConnectionError` - Connection failures

### Example

```python
try:
    await wallet.approve_session(id=proposal_id, namespaces={...})
except ValueError as e:
    print(f"Invalid parameters: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Best Practices

1. **Always initialize Core before use:**
   ```python
   await core.start()
   ```

2. **Handle events asynchronously:**
   ```python
   @wallet.on("session_proposal")
   async def on_proposal(event):
       # Handle proposal
   ```

3. **Clean up on shutdown:**
   ```python
   await core.relayer.disconnect()
   ```

4. **Use proper error handling:**
   ```python
   try:
       await wallet.pair(uri)
   except Exception as e:
       logger.error(f"Pairing failed: {e}")
   ```

5. **Store sessions persistently:**
   ```python
   storage = FileStorage(data_dir="./wallet_data")
   ```

## Type Hints

The SDK uses Python type hints throughout. Enable type checking with `mypy`:

```bash
mypy src/walletkit
```

## Testing

See `tests/` directory for comprehensive test examples.

## License

This documentation is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License (CC-BY-SA-4.0). See [LICENSE-DOCS](../LICENSE-DOCS) for details.
