# Dependency Deep Dive

## Purpose

This document provides an in-depth analysis of all dependencies that walletkit relies on, including WalletConnect Core, Utils, and their transitive dependencies. Understanding these dependencies is crucial for planning the Python port.

## Table of Contents

1. [WalletConnect Core Analysis](#walletconnect-core-analysis)
2. [WalletConnect Utils Analysis](#walletconnect-utils-analysis)
3. [Transitive Dependencies](#transitive-dependencies)
4. [Third-party Dependencies](#third-party-dependencies)
5. [What WalletKit Actually Uses](#what-walletkit-actually-uses)

## WalletConnect Core Analysis

**Package:** `@walletconnect/core`  
**Version:** 2.23.0 (used by walletkit)  
**Reference:** `tmp/@walletconnect-core/` (v2.23.1)

### Controllers Breakdown

#### Crypto Controller

**Purpose:** Cryptographic operations and key management

**Key Functionality:**
- Key generation (X25519)
- Encryption/decryption (ChaCha20-Poly1305)
- Client ID generation
- Keychain operations

**Dependencies:**
- `@walletconnect/keyvaluestorage` for key persistence
- Crypto libraries for operations

**Python Equivalents Needed:**
- `cryptography` library for X25519 and ChaCha20-Poly1305
- Storage backend for key persistence

#### Relayer Controller

**Purpose:** WebSocket-based message relaying

**Key Functionality:**
- WebSocket connection management
- Message publishing to topics
- Message subscription
- Connection lifecycle (connect, disconnect, reconnect)
- Message queuing and retry

**Dependencies:**
- `@walletconnect/jsonrpc-ws-connection` for WebSocket
- `@walletconnect/relay-api` for relay API
- `@walletconnect/relay-auth` for authentication

**Python Equivalents Needed:**
- `websockets` or `aiohttp` for WebSocket
- JSON-RPC message handling
- Connection management

#### Pairing Controller

**Purpose:** Pairing management

**Key Functionality:**
- Pairing creation from URI
- Pairing storage
- Pairing activation
- Pairing expiration management

**Dependencies:**
- Relayer for communication
- Expirer for expiration
- Storage for persistence

**Python Equivalents Needed:**
- URI parsing
- Storage backend
- Expiration tracking

#### History Controller

**Purpose:** JSON-RPC request/response history

**Key Functionality:**
- Track sent requests
- Track received responses
- History persistence
- History expiration

**Dependencies:**
- Storage for persistence
- Expirer for expiration

**Python Equivalents Needed:**
- Storage backend
- Expiration tracking

#### Expirer Controller

**Purpose:** Expiration management

**Key Functionality:**
- Track expiration times
- Automatic expiration
- Expiration events

**Dependencies:**
- Storage for persistence
- Heartbeat for timing

**Python Equivalents Needed:**
- Timer/async task management
- Storage backend

#### Verify Controller

**Purpose:** Verification utilities

**Key Functionality:**
- Domain verification
- Attestation verification
- Verification storage

**Dependencies:**
- Storage for persistence
- Network utilities for verification

**Python Equivalents Needed:**
- HTTP client for verification
- Storage backend

#### Echo Client

**Purpose:** Push notification client

**Key Functionality:**
- Device token registration
- Push notification handling

**Dependencies:**
- HTTP client for API calls

**Python Equivalents Needed:**
- HTTP client (e.g., `httpx` or `aiohttp`)

#### Events Client

**Purpose:** Telemetry and event tracking

**Key Functionality:**
- Event tracking
- Telemetry collection

**Dependencies:**
- HTTP client for telemetry

**Python Equivalents Needed:**
- HTTP client (optional, can be simplified)

### Storage Layer

**Package:** `@walletconnect/keyvaluestorage`

**Purpose:** Storage abstraction layer

**Key Functionality:**
- Key-value storage interface
- Async operations
- Multiple backend support (localStorage, IndexedDB, etc.)

**Python Equivalents Needed:**
- Storage abstraction
- Backends: file system, SQLite, in-memory
- Async operations

### WebSocket Connection Handling

**Package:** `@walletconnect/jsonrpc-ws-connection`

**Purpose:** WebSocket connection for JSON-RPC

**Key Functionality:**
- WebSocket connection management
- JSON-RPC message framing
- Reconnection logic
- Error handling

**Python Equivalents Needed:**
- WebSocket library with reconnection
- JSON-RPC message handling

### JSON-RPC Provider Implementation

**Package:** `@walletconnect/jsonrpc-provider`

**Purpose:** JSON-RPC provider abstraction

**Key Functionality:**
- JSON-RPC request/response handling
- Provider interface
- Error handling

**Python Equivalents Needed:**
- JSON-RPC client implementation
- Request/response handling

### Heartbeat Mechanism

**Package:** `@walletconnect/heartbeat`

**Purpose:** Heartbeat for timing operations

**Key Functionality:**
- Periodic heartbeat
- Timing utilities

**Python Equivalents Needed:**
- Async timer/periodic task
- `asyncio` for timing

### Logger System

**Package:** `@walletconnect/logger`

**Purpose:** Logging utilities

**Key Functionality:**
- Structured logging
- Log levels
- Log formatting
- Child loggers

**Python Equivalents Needed:**
- `logging` module or structured logging library
- Logger hierarchy

## WalletConnect Utils Analysis

**Package:** `@walletconnect/utils`  
**Version:** 2.23.1  
**Reference:** `tmp/@walletconnect-utils/`

### Which Utility Functions WalletKit Relies On

From code analysis, walletkit directly imports:
- `JsonRpcPayload` from `@walletconnect/jsonrpc-utils` (not utils, but related)
- Types from `@walletconnect/types`

However, Core and Sign Client use many utils functions.

### Crypto Operations Needed

**Module:** `src/crypto.ts`

**Key Functions:**
- Key generation
- Encryption/decryption
- Hash functions
- Signature operations

**Dependencies:**
- `@noble/ciphers` for ChaCha20-Poly1305
- `@noble/curves` for elliptic curves
- `@noble/hashes` for hashing

**Python Equivalents Needed:**
- `cryptography` library
- Or `pycryptodome` for crypto operations

### CAIP/CACAO Handling Requirements

**Modules:** `src/caip.ts`, `src/cacao.ts`

**Key Functions:**
- Chain ID parsing/formatting
- Account ID parsing/formatting
- CACAO creation/validation

**Python Equivalents Needed:**
- CAIP parsing library or custom implementation
- CACAO handling (may need to port)

### URI Parsing Needs

**Module:** `src/uri.ts`

**Key Functions:**
- WalletConnect URI parsing
- URI formatting
- URI validation

**Python Equivalents Needed:**
- Custom URI parser (WalletConnect-specific format)
- Or adapt existing URI parsing

### Validators

**Module:** `src/validators.ts`

**Key Functions:**
- Type validation
- Format validation
- Value validation

**Python Equivalents Needed:**
- `pydantic` for validation
- Or custom validators

### Namespace Handling

**Module:** `src/namespaces.ts`

**Key Functions:**
- Namespace parsing
- Namespace validation
- Namespace manipulation

**Python Equivalents Needed:**
- Custom namespace handling
- Or adapt from JS implementation

## Transitive Dependencies

### WalletConnect Packages

1. **`@walletconnect/jsonrpc-provider` (v1.0.14)**
   - JSON-RPC provider abstraction
   - Used by Core

2. **`@walletconnect/jsonrpc-utils` (v1.0.8)**
   - JSON-RPC utilities
   - Used by walletkit directly

3. **`@walletconnect/jsonrpc-types` (v1.0.4)**
   - JSON-RPC type definitions
   - Used by JSON-RPC packages

4. **`@walletconnect/jsonrpc-ws-connection` (v1.0.16)**
   - WebSocket connection for JSON-RPC
   - Used by Core Relayer

5. **`@walletconnect/keyvaluestorage` (v1.1.1)**
   - Storage abstraction
   - Used by Core

6. **`@walletconnect/logger` (v3.0.1)**
   - Logging utilities
   - Used by walletkit and Core

7. **`@walletconnect/relay-api` (v1.0.11)**
   - Relay API client
   - Used by Core Relayer

8. **`@walletconnect/relay-auth` (v1.1.0)**
   - Relay authentication
   - Used by Core Relayer

9. **`@walletconnect/types` (v2.23.1)**
   - TypeScript type definitions
   - Used throughout

10. **`@walletconnect/safe-json` (v1.0.2)**
    - Safe JSON parsing
    - Used by various packages

11. **`@walletconnect/time` (v1.0.2)**
    - Time utilities
    - Used by various packages

12. **`@walletconnect/window-getters` (v1.0.1)**
    - Browser window utilities
    - Used by various packages (may not be needed in Python)

13. **`@walletconnect/window-metadata` (v1.0.1)**
    - Browser metadata utilities
    - Used by various packages (may not be needed in Python)

### Sign Client Dependencies

**Package:** `@walletconnect/sign-client` (v2.23.0)

**Dependencies:**
- `@walletconnect/core` (already analyzed)
- `@walletconnect/types` (already analyzed)
- Other WalletConnect packages

## Third-party Dependencies

### Event System

**Package:** `events` (v3.3.0)

**Purpose:** EventEmitter implementation

**Python Equivalents:**
- Custom EventEmitter class using `asyncio.Event` and `asyncio.Queue`
- Or use existing Python event libraries

### Byte Array Utilities

**Package:** `uint8arrays` (v3.1.1)

**Purpose:** Byte array manipulation

**Python Equivalents:**
- `bytes` and `bytearray` (built-in)
- `array` module if needed

### Cryptographic Libraries

**Packages:**
- `@noble/ciphers` (v1.3.0) - ChaCha20-Poly1305
- `@noble/curves` (v1.9.7) - Elliptic curves
- `@noble/hashes` (v1.8.0) - Hash functions

**Python Equivalents:**
- `cryptography` library (comprehensive)
- Or `pycryptodome` for specific algorithms

### MessagePack

**Package:** `@msgpack/msgpack` (v3.1.2)

**Purpose:** MessagePack serialization

**Python Equivalents:**
- `msgpack` library

### Base Encoding

**Package:** `@scure/base` (v1.2.6)

**Purpose:** Base encoding utilities

**Python Equivalents:**
- `base64`, `base58` (via libraries)

### Other Utilities

**Packages:**
- `blakejs` (v1.2.1) - Blake hash
- `bs58` (v6.0.0) - Base58 encoding
- `ox` (v0.9.3) - Ethereum utilities
- `detect-browser` (v5.3.0) - Browser detection (not needed in Python)
- `es-toolkit` (v1.39.3) - Utility functions

**Python Equivalents:**
- Various libraries or custom implementations

## What WalletKit Actually Uses

### Direct Usage

1. **Core Instance:**
   - Injected in constructor
   - Used for: `core.pairing.pair()`, `core.crypto`, `core.echoClient`, `core.eventClient`

2. **Sign Client:**
   - Created in Engine
   - Used for: All session operations, request/response handling

3. **Types:**
   - Extensive use of types from `@walletconnect/types`

4. **JSON-RPC Utils:**
   - `JsonRpcPayload`, `JsonRpcResponse`, `ErrorResponse`

5. **Logger:**
   - Logger interface from `@walletconnect/logger`

### Indirect Usage (via Core/Sign Client)

1. **Storage:**
   - Used by Core for persistence
   - Used by Sign Client for session storage

2. **Crypto:**
   - Used by Core for encryption/decryption
   - Used in notifications utilities

3. **Relayer:**
   - Used by Core for WebSocket communication
   - Used by Sign Client for protocol communication

4. **Pairing:**
   - Used by Core for pairing management
   - Used by walletkit via `core.pairing.pair()`

## TODO

- [ ] Analyze exact API surface used from each dependency
- [ ] Document minimum required functionality from each dependency
- [ ] Research existing Python libraries that could replace dependencies
- [ ] Document protocol compliance requirements
- [ ] Analyze performance requirements
- [ ] Document platform-specific considerations (Node.js vs Python)

