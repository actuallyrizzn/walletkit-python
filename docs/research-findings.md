# Research Findings

## Purpose

This document contains the detailed research findings from analyzing the reference implementations, codebase, and protocol details needed for the Python port.

## Table of Contents

1. [SignClient API Analysis](#signclient-api-analysis)
2. [Core Controllers Deep Dive](#core-controllers-deep-dive)
3. [Protocol Message Formats](#protocol-message-formats)
4. [Crypto Implementation Details](#crypto-implementation-details)
5. [Python Library Research](#python-library-research)
6. [Key Findings Summary](#key-findings-summary)

## SignClient API Analysis

### API Surface Used by WalletKit Engine

Based on analysis of `packages/walletkit/src/controllers/engine.ts`, here are the exact SignClient methods used:

#### Initialization

```typescript
SignClient.init({
  core: ICore,
  metadata: CoreTypes.Metadata,
  signConfig?: SignClientTypes.Options["signConfig"]
}): Promise<ISignClient>
```

**Returns:** `ISignClient` instance

**Properties Accessed:**
- `signClient.core.eventClient.init()` - Initializes event client

#### Session Operations

**1. `approve(params)`**
```typescript
signClient.approve({
  id: number,
  namespaces: Record<string, SessionTypes.Namespace>,
  sessionProperties?: ProposalTypes.SessionProperties,
  scopedProperties?: ProposalTypes.ScopedProperties,
  sessionConfig?: SessionTypes.SessionConfig,
  relayProtocol?: string,
  proposalRequestsResponses?: EngineTypes.ApproveParams["proposalRequestsResponses"]
}): Promise<{ topic: string, acknowledged: () => Promise<void> }>
```

**Returns:** Object with `topic` and `acknowledged` function

**2. `reject(params)`**
```typescript
signClient.reject({
  id: number,
  reason: ErrorResponse
}): Promise<void>
```

**3. `update(params)`**
```typescript
signClient.update({
  topic: string,
  namespaces: SessionTypes.Namespaces
}): Promise<{ acknowledged: () => Promise<void> }>
```

**4. `extend(params)`**
```typescript
signClient.extend({
  topic: string
}): Promise<{ acknowledged: () => Promise<void> }>
```

**5. `disconnect(params)`**
```typescript
signClient.disconnect({
  topic: string,
  reason: ErrorResponse
}): Promise<void>
```

**6. `respond(params)`**
```typescript
signClient.respond({
  topic: string,
  response: JsonRpcResponse
}): Promise<void>
```

**7. `emit(params)`**
```typescript
signClient.emit({
  topic: string,
  event: any, // SessionEvent
  chainId: string
}): Promise<void>
```

#### Query Methods

**1. `session.get(topic)`**
```typescript
signClient.session.get(topic: string): SessionTypes.Struct
```

**2. `session.getAll()`**
```typescript
signClient.session.getAll(): SessionTypes.Struct[]
```

**3. `proposal.getAll()`**
```typescript
signClient.proposal.getAll(): Record<number, ProposalTypes.Struct>
```

**4. `getPendingSessionRequests()`**
```typescript
signClient.getPendingSessionRequests(): PendingRequestTypes.Struct[]
```

#### Authentication

**1. `approveSessionAuthenticate(params)`**
```typescript
signClient.approveSessionAuthenticate(
  params: AuthTypes.ApproveSessionAuthenticateParams
): Promise<{ session: SessionTypes.Struct | undefined }>
```

**2. `rejectSessionAuthenticate(params)`**
```typescript
signClient.rejectSessionAuthenticate({
  id: number,
  reason: ErrorResponse
}): Promise<void>
```

**3. `formatAuthMessage(params)`**
```typescript
signClient.formatAuthMessage({
  request: AuthTypes.BaseAuthRequestParams,
  iss: string
}): string
```

#### Events

**Event System:**
```typescript
signClient.events.on(event: string, listener: Function): EventEmitter
signClient.events.off(event: string, listener: Function): EventEmitter
```

**Events Emitted:**
- `session_proposal`
- `session_request`
- `session_delete`
- `proposal_expire`
- `session_request_expire`
- `session_authenticate`

#### Properties

- `signClient.core` - Access to Core instance
- `signClient.signConfig` - Sign configuration

### SignClient Implementation Strategy

Since we don't have SignClient source in `tmp/`, we have two options:

1. **Minimal Implementation:** Implement only the API surface used by Engine
2. **Full Port:** Port entire SignClient (would need source code)

**Recommendation:** Start with minimal implementation based on API surface analysis above.

## Core Controllers Deep Dive

### Pairing Controller

**File:** `tmp/@walletconnect-core/src/controllers/pairing.ts`

#### Key Methods Used by WalletKit

**1. `pair(params)`**
```typescript
pair(params: { uri: string, activatePairing?: boolean }): Promise<PairingTypes.Struct>
```

**Process:**
1. Validates URI format
2. Parses URI to extract: topic, symKey, relay, expiryTimestamp, methods
3. Checks if pairing already exists
4. Creates/updates pairing in storage
5. Sets symmetric key in crypto keychain
6. Subscribes to topic via relayer
7. Returns pairing struct

**Dependencies:**
- `core.crypto.setSymKey()` - Set symmetric key
- `core.relayer.subscribe()` - Subscribe to topic
- `core.expirer.set()` - Set expiration
- `core.pairings.set()` - Store pairing
- `parseUri()` from utils - Parse WalletConnect URI

#### Internal Methods

- `sendRequest()` - Send JSON-RPC request
- `sendResult()` - Send JSON-RPC result
- `sendError()` - Send JSON-RPC error
- `deletePairing()` - Delete pairing and cleanup

#### Events

- `PAIRING_EVENTS.create` - Pairing created
- `PAIRING_EVENTS.delete` - Pairing deleted
- `PAIRING_EVENTS.expire` - Pairing expired
- `PAIRING_EVENTS.ping` - Pairing ping

### Crypto Controller

**File:** `tmp/@walletconnect-core/src/controllers/crypto.ts`

#### Key Methods Used by WalletKit

**1. `init()`**
```typescript
init(): Promise<void>
```
Initializes keychain.

**2. `encode(topic, payload, opts?)`**
```typescript
encode(
  topic: string,
  payload: JsonRpcPayload,
  opts?: { type?: number, senderPublicKey?: string, receiverPublicKey?: string, encoding?: string }
): Promise<string>
```

**Process:**
1. Validates encoding options
2. Stringifies payload to JSON
3. Checks envelope type (Type 1 or Type 2)
4. Type 2: Direct encoding (no encryption)
5. Type 1: 
   - Generates shared key from public keys
   - Gets symmetric key for topic
   - Encrypts message using ChaCha20-Poly1305
6. Returns encoded/encrypted message

**3. `decode(topic, encoded, opts?)`**
```typescript
decode(
  topic: string,
  encoded: string,
  opts?: { encoding?: string }
): Promise<JsonRpcPayload>
```

**Process:**
1. Validates decoding options
2. Checks envelope type
3. Type 2: Direct decode
4. Type 1:
   - Generates shared key from public keys
   - Gets symmetric key for topic
   - Decrypts message
5. Parses JSON payload
6. Returns payload

**4. `setSymKey(symKey, overrideTopic?)`**
```typescript
setSymKey(symKey: string, overrideTopic?: string): Promise<string>
```
Sets symmetric key in keychain, returns topic.

**5. `deleteSymKey(topic)`**
```typescript
deleteSymKey(topic: string): Promise<void>
```
Deletes symmetric key from keychain.

**6. `getClientId()`**
```typescript
getClientId(): Promise<string>
```
Generates/retrieves client ID from seed.

#### Crypto Algorithms

- **Key Exchange:** X25519 (from `@walletconnect/utils`)
- **Encryption:** ChaCha20-Poly1305 (from `@walletconnect/utils`)
- **Key Derivation:** `deriveSymKey()` from utils
- **Hashing:** SHA-256 for key hashing

#### Keychain

Uses `KeyChain` class for key storage:
- `keychain.set(topic, key)` - Store key
- `keychain.get(topic)` - Get key
- `keychain.del(topic)` - Delete key
- `keychain.has(topic)` - Check if key exists

### Relayer Controller

**File:** `tmp/@walletconnect-core/src/controllers/relayer.ts`

#### Key Methods Used by WalletKit

**1. `subscribe(topic, opts?)`**
```typescript
subscribe(
  topic: string,
  opts?: {
    transportType?: string,
    internal?: { throwOnFailedPublish?: boolean }
  }
): Promise<string>
```

**Process:**
1. Establishes WebSocket connection if needed
2. Subscribes to topic via subscriber
3. Returns subscription ID

**2. `publish(topic, message, opts?)`**
```typescript
publish(
  topic: string,
  message: string,
  opts?: RelayerTypes.PublishOptions
): Promise<void>
```

**Process:**
1. Publishes message to topic via publisher
2. Records message event

**3. `unsubscribe(topic, opts?)`**
```typescript
unsubscribe(
  topic: string,
  opts?: RelayerTypes.UnsubscribeOptions
): Promise<void>
```

#### WebSocket Connection

**Connection Process:**
1. Creates JWT token using `core.crypto.signJWT(relayUrl)`
2. Formats relay URL with auth
3. Creates `JsonRpcProvider` with `WsConnection`
4. Connects to WebSocket
5. Handles reconnection logic

**Reconnection:**
- Automatic reconnection on disconnect
- Exponential backoff
- Max 6 connection attempts
- Heartbeat timeout: 35 seconds (30s + 5s buffer)

**Message Flow:**
1. Incoming messages via WebSocket
2. Parsed as JSON-RPC payloads
3. Emitted as `RELAYER_EVENTS.message` events
4. Messages tracked for deduplication

## Protocol Message Formats

### WalletConnect URI Format

**Format:**
```
wc:{topic}@{version}?symKey={symKey}&relay-protocol={protocol}&expiryTimestamp={timestamp}&methods={methods}
```

**Example:**
```
wc:abc123@2?symKey=def456&relay-protocol=irn&expiryTimestamp=1234567890
```

**Parsing (from `tmp/@walletconnect-utils/src/uri.ts`):**
- Protocol: `wc`
- Topic: extracted from URI
- Version: extracted from URI
- Query params: symKey, relay-protocol, expiryTimestamp, methods

### JSON-RPC Message Format

**Request:**
```json
{
  "id": 1,
  "jsonrpc": "2.0",
  "method": "wc_sessionPropose",
  "params": { ... }
}
```

**Response:**
```json
{
  "id": 1,
  "jsonrpc": "2.0",
  "result": { ... }
}
```

**Error:**
```json
{
  "id": 1,
  "jsonrpc": "2.0",
  "error": {
    "code": -32000,
    "message": "Error message"
  }
}
```

### Encrypted Message Format

**Type 1 Envelope (Encrypted):**
- Encrypted using ChaCha20-Poly1305
- Contains: type byte, sender public key, encrypted payload
- Base64 encoded

**Type 2 Envelope (Unencrypted):**
- Direct JSON string
- Base64 encoded

**Encoding Process:**
1. Determine envelope type
2. Type 1: Encrypt with symmetric key
3. Type 2: Direct encode
4. Base64 encode result

### Session Proposal Format

```typescript
{
  id: number,
  params: {
    requiredNamespaces: Record<string, Namespace>,
    optionalNamespaces?: Record<string, Namespace>,
    relays: Array<{ protocol: string }>,
    proposer: {
      publicKey: string,
      metadata: Metadata
    },
    expiryTimestamp: number
  }
}
```

### Session Request Format

```typescript
{
  id: number,
  topic: string,
  params: {
    request: {
      method: string,
      params: any
    },
    chainId: string
  }
}
```

## Crypto Implementation Details

### Algorithms

**1. Key Exchange: X25519**
- Used for: Generating shared symmetric keys
- Implementation: `@walletconnect/utils` → `@noble/curves`
- Process:
  1. Generate key pair (public/private)
  2. Derive shared key from self private + peer public
  3. Hash shared key to get symmetric key

**2. Encryption: ChaCha20-Poly1305**
- Used for: Encrypting/decrypting messages
- Implementation: `@walletconnect/utils` → `@noble/ciphers`
- Process:
  1. Get symmetric key for topic
  2. Encrypt message with ChaCha20-Poly1305
  3. Include sender public key in envelope
  4. Base64 encode result

**3. Hashing: SHA-256**
- Used for: Hashing keys to generate topics
- Implementation: `@walletconnect/utils` → `@noble/hashes`

### Key Management

**Client Seed:**
- Stored in keychain as `CRYPTO_CLIENT_SEED`
- Used to generate client ID
- Used for JWT signing

**Symmetric Keys:**
- Stored by topic in keychain
- Generated from shared key (X25519) or provided directly
- Used for message encryption/decryption

**Key Pairs:**
- Generated on demand
- Private key stored in keychain by public key
- Used for key exchange

### JWT Signing

**Purpose:** Authenticate with relay server

**Process:**
1. Get client seed
2. Generate key pair from seed
3. Create JWT with:
   - `sub`: Random session identifier
   - `aud`: Relay URL
   - `ttl`: 1 day
4. Sign with private key
5. Return JWT string

## Python Library Research

### Search Results

**No existing Python WalletConnect libraries found:**
- PyPI search: No results for "walletconnect"
- GitHub search: No active Python implementations found
- The web search returned results for a different "SignClient" (NuGet package)

**Conclusion:** We need to build from scratch or port the JavaScript implementation.

### Recommended Python Libraries

**WebSocket:**
- `websockets` - Async WebSocket library
- Version: Latest
- Features: Async/await, reconnection support

**Crypto:**
- `cryptography` - Comprehensive crypto library
- Version: Latest
- Features: X25519, ChaCha20-Poly1305 support

**JSON-RPC:**
- Custom implementation recommended
- Need WalletConnect-specific handling

**Storage:**
- `aiosqlite` - Async SQLite
- Or file-based JSON storage

**HTTP:**
- `aiohttp` - Async HTTP client
- For relay API calls

**MessagePack:**
- `msgpack` - MessagePack serialization

**Base Encoding:**
- `base58` - Base58 encoding
- `base64` - Built-in

## Key Findings Summary

### Critical Findings

1. **SignClient API:** Complete API surface documented from usage analysis
2. **Core Controllers:** Full implementation details available in reference code
3. **Protocol:** Message formats understood from reference implementation
4. **Crypto:** Exact algorithms and processes documented
5. **No Python Libraries:** Need to build from scratch

### Implementation Readiness

**Ready to Start:**
- ✅ Core controllers (Pairing, Crypto, Relayer) - Full reference available
- ✅ Protocol message formats - Understood
- ✅ Crypto implementation - Algorithms known
- ✅ Event system - Pattern clear

**Needs More Work:**
- ⚠️ SignClient - API surface known, but need to implement or find source
- ⚠️ Type definitions - Need to port from `@walletconnect/types`
- ⚠️ Test environment - Need to set up

### Recommended Next Steps

1. **Start with Core Implementation:**
   - Implement Pairing controller
   - Implement Crypto controller
   - Implement Relayer controller
   - Implement minimal Core class

2. **Implement SignClient Wrapper:**
   - Based on API surface analysis
   - Can refine as we learn more

3. **Port WalletKit:**
   - Once Core and SignClient are ready
   - Port Engine and Client

4. **Testing:**
   - Set up test environment
   - Port tests
   - Integration testing

## TODO

- [ ] Get SignClient source code if possible
- [ ] Document all type definitions needed
- [ ] Create detailed implementation specs for each controller
- [ ] Set up test environment
- [ ] Create proof-of-concept for critical components

