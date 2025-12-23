# Dependencies Analysis

## Purpose

This document analyzes the JavaScript dependencies of walletkit and provides a strategy for porting or replacing them with Python equivalents. It considers the reference implementations in `tmp/` and evaluates different porting approaches.

## Table of Contents

1. [JavaScript Dependencies](#javascript-dependencies)
2. [Python Alternatives](#python-alternatives)
3. [Porting Strategy](#porting-strategy)
4. [Dependency Tree](#dependency-tree)
5. [Platform Considerations](#platform-considerations)

## JavaScript Dependencies

### Direct Dependencies

From `packages/walletkit/package.json`:

1. **`@walletconnect/core` (v2.23.0)**
   - **Purpose:** Core WalletConnect protocol implementation
   - **Usage:** Injected into WalletKit constructor, used for pairing, crypto, echo, events
   - **Reference:** `tmp/@walletconnect-core/` (v2.23.1)
   - **Complexity:** High - Full protocol implementation

2. **`@walletconnect/sign-client` (v2.23.0)**
   - **Purpose:** Sign protocol client
   - **Usage:** Wrapped by Engine controller, used for all session operations
   - **Complexity:** High - Full sign protocol implementation

3. **`@walletconnect/types` (v2.23.0)**
   - **Purpose:** TypeScript type definitions
   - **Usage:** Type imports throughout codebase
   - **Complexity:** Low - Type definitions only

4. **`@walletconnect/jsonrpc-provider` (v1.0.14)**
   - **Purpose:** JSON-RPC provider abstraction
   - **Usage:** Used by Core (transitive)
   - **Complexity:** Medium - JSON-RPC implementation

5. **`@walletconnect/jsonrpc-utils` (v1.0.8)**
   - **Purpose:** JSON-RPC utilities
   - **Usage:** Direct imports for JsonRpcPayload, JsonRpcResponse, ErrorResponse
   - **Complexity:** Low - Utility functions

6. **`@walletconnect/logger` (v3.0.0)**
   - **Purpose:** Logging utilities
   - **Usage:** Logger interface
   - **Complexity:** Low - Logging wrapper

### Transitive Dependencies (from Core)

1. **`@walletconnect/keyvaluestorage` (v1.1.1)**
   - Storage abstraction layer
   - Multiple backend support

2. **`@walletconnect/relay-api` (v1.0.11)**
   - Relay API client
   - HTTP client for relay operations

3. **`@walletconnect/relay-auth` (v1.1.0)**
   - Relay authentication
   - JWT handling

4. **`@walletconnect/heartbeat` (v1.2.2)**
   - Heartbeat mechanism
   - Timing utilities

5. **`@walletconnect/jsonrpc-ws-connection` (v1.0.16)**
   - WebSocket connection for JSON-RPC
   - Connection management

6. **`@walletconnect/jsonrpc-types` (v1.0.4)**
   - JSON-RPC type definitions

7. **`@walletconnect/safe-json` (v1.0.2)**
   - Safe JSON parsing

8. **`@walletconnect/time` (v1.0.2)**
   - Time utilities

9. **`@walletconnect/utils` (v2.23.1)**
   - Utility functions
   - **Reference:** `tmp/@walletconnect-utils/`

10. **`@walletconnect/window-getters` (v1.0.1)**
    - Browser window utilities (not needed in Python)

11. **`@walletconnect/window-metadata` (v1.0.1)**
    - Browser metadata utilities (not needed in Python)

### Third-party Dependencies

1. **`events` (v3.3.0)** - EventEmitter (Node.js)
2. **`uint8arrays` (v3.1.1)** - Byte array utilities
3. **`es-toolkit` (v1.39.3)** - Utility functions

### Crypto Dependencies (from Utils)

1. **`@noble/ciphers` (v1.3.0)** - ChaCha20-Poly1305
2. **`@noble/curves` (v1.9.7)** - Elliptic curves
3. **`@noble/hashes` (v1.8.0)** - Hash functions
4. **`@msgpack/msgpack` (v3.1.2)** - MessagePack
5. **`@scure/base` (v1.2.6)** - Base encoding
6. **`blakejs` (v1.2.1)** - Blake hash
7. **`bs58` (v6.0.0)** - Base58 encoding
8. **`ox` (v0.9.3)** - Ethereum utilities

## Python Alternatives

### Existing Python WalletConnect Libraries

**Research Needed:** Check if any Python WalletConnect libraries exist:
- Search PyPI for "walletconnect"
- Check GitHub for Python WalletConnect implementations
- Evaluate if any can be used or adapted

**Status:** TODO - Research required

### Core Functionality Replacements

#### 1. Event System

**JavaScript:** `events` (EventEmitter)

**Python Options:**
- Custom EventEmitter class (recommended)
- `pydispatch` library
- `blinker` library

**Recommendation:** Custom implementation for full control and API compatibility.

#### 2. WebSocket

**JavaScript:** `@walletconnect/jsonrpc-ws-connection`

**Python Options:**
- `websockets` library (recommended)
- `aiohttp` WebSocket support
- `websocket-client` (synchronous)

**Recommendation:** `websockets` for async/await support and reconnection handling.

#### 3. Storage

**JavaScript:** `@walletconnect/keyvaluestorage`

**Python Options:**
- File-based storage (JSON)
- SQLite via `aiosqlite`
- In-memory storage
- Redis via `aioredis`

**Recommendation:** Abstract storage interface with file and SQLite backends initially.

#### 4. Crypto

**JavaScript:** `@noble/*` libraries

**Python Options:**
- `cryptography` library (recommended)
- `pycryptodome` (alternative)

**Recommendation:** `cryptography` for comprehensive algorithm support.

#### 5. JSON-RPC

**JavaScript:** `@walletconnect/jsonrpc-provider`, `@walletconnect/jsonrpc-utils`

**Python Options:**
- Custom JSON-RPC implementation (recommended)
- `jsonrpc-async` library
- `jsonrpcclient` library

**Recommendation:** Custom implementation for WalletConnect-specific needs.

#### 6. Logging

**JavaScript:** `@walletconnect/logger`

**Python Options:**
- `logging` module (standard library)
- `structlog` for structured logging

**Recommendation:** `logging` with custom formatter.

#### 7. MessagePack

**JavaScript:** `@msgpack/msgpack`

**Python:** `msgpack` library

#### 8. Base Encoding

**JavaScript:** `@scure/base`, `bs58`

**Python:**
- `base64` (standard library)
- `base58` library

#### 9. HTTP Client

**JavaScript:** Built-in `fetch` or libraries

**Python Options:**
- `aiohttp` (recommended)
- `httpx` (alternative)

**Recommendation:** `aiohttp` for async support.

## Porting Strategy

### Option 1: Port Core and Utils to Python First, Then WalletKit

**Approach:**
1. Port `@walletconnect/core` to Python
2. Port `@walletconnect/utils` to Python
3. Port `@walletconnect/sign-client` to Python
4. Port `@reown/walletkit` to Python

**Pros:**
- Full feature parity
- Can be used by other Python projects
- Maintains architecture consistency

**Cons:**
- Large effort
- May port unused functionality
- Longer timeline

**Recommendation:** Consider if full WalletConnect Python SDK is desired.

### Option 2: Create Minimal Python Implementations of Only What WalletKit Needs

**Approach:**
1. Analyze what walletkit actually uses from Core/Utils
2. Create minimal Python implementations
3. Port walletkit to use these minimal implementations

**Pros:**
- Faster to implement
- Smaller codebase
- Focus on walletkit needs only

**Cons:**
- May miss edge cases
- Less reusable
- May need to expand later

**Recommendation:** Good starting point, can expand later if needed.

### Option 3: Use Existing Python WebSocket/JSON-RPC Libraries and Build Compatibility Layer

**Approach:**
1. Use existing Python libraries (websockets, aiohttp, etc.)
2. Build compatibility layer to match WalletConnect API
3. Port walletkit to use compatibility layer

**Pros:**
- Leverage existing libraries
- Faster initial implementation
- Less code to maintain

**Cons:**
- May not match API exactly
- Compatibility layer complexity
- May need protocol-specific implementations

**Recommendation:** Hybrid approach - use existing libraries where possible, custom implementations where needed.

### Recommended Strategy: Hybrid Approach

**Phase 1: Minimal Core Implementation**
- Implement only what walletkit needs from Core
- Use existing Python libraries where possible
- Custom implementations for WalletConnect-specific needs

**Phase 2: Expand as Needed**
- Add functionality as requirements emerge
- Maintain compatibility with WalletConnect protocol

**Phase 3: Consider Full Port (Optional)**
- If demand exists, consider full Core/Utils port
- Can be separate project or expansion

## Dependency Tree

### What Needs to be Ported

```
walletkit (Python)
├── Core (minimal Python implementation)
│   ├── Crypto Controller
│   ├── Relayer Controller
│   ├── Pairing Controller
│   ├── Storage Abstraction
│   └── Event System
├── Sign Client (minimal Python implementation)
│   └── Uses Core
├── Utils (minimal Python implementation)
│   ├── JSON-RPC utilities
│   ├── URI parsing
│   └── Crypto utilities (as needed)
└── Python Libraries
    ├── websockets (WebSocket)
    ├── cryptography (Crypto)
    ├── aiohttp (HTTP)
    ├── msgpack (MessagePack)
    └── base58 (Base58 encoding)
```

### Priority Order for Porting

1. **High Priority:**
   - Event system (EventEmitter)
   - Storage abstraction
   - JSON-RPC utilities
   - WebSocket connection
   - Crypto operations (minimal)

2. **Medium Priority:**
   - Core controllers (Crypto, Relayer, Pairing)
   - Sign Client wrapper
   - URI parsing
   - CAIP utilities

3. **Low Priority:**
   - Echo client (push notifications)
   - Events client (telemetry)
   - Advanced utilities

## Platform Considerations

### Node.js vs Python

**Node.js Specific:**
- `events` package (built-in)
- Browser APIs (window, localStorage) - not needed in Python
- Node.js streams - not needed

**Python Specific:**
- `asyncio` for async operations
- File system operations
- Platform-specific storage backends

### Browser vs Server

**Current Implementation:**
- Designed for Node.js and browser
- Uses browser storage APIs
- Uses browser WebSocket APIs

**Python Implementation:**
- Server-side focused
- File-based or database storage
- Native WebSocket support

### Compatibility

**Protocol Compatibility:**
- Must maintain WalletConnect protocol compatibility
- Message formats must match
- Crypto operations must be compatible

**API Compatibility:**
- Try to maintain similar API surface
- Python naming conventions (snake_case)
- Type hints instead of TypeScript types

## TODO

- [ ] Research existing Python WalletConnect libraries
- [ ] Analyze exact API surface needed from each dependency
- [ ] Create detailed porting plan for each dependency
- [ ] Evaluate performance requirements
- [ ] Document protocol compliance requirements
- [ ] Create proof-of-concept for critical components

