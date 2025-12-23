# Architecture Analysis

## Purpose

This document provides a detailed analysis of the current TypeScript/JavaScript WalletKit codebase structure, components, design patterns, and how they relate to the reference implementations in `tmp/`.

## Table of Contents

1. [Codebase Structure](#codebase-structure)
2. [Core Components](#core-components)
3. [Reference Implementation Analysis](#reference-implementation-analysis)
4. [Dependency Analysis](#dependency-analysis)
5. [Design Patterns](#design-patterns)
6. [Event System](#event-system)

## Codebase Structure

### Main Package: `packages/walletkit/`

```
packages/walletkit/
├── src/
│   ├── client.ts              # Main WalletKit client class
│   ├── index.ts              # Public API exports
│   ├── constants/            # Constants and configuration
│   ├── controllers/          # Business logic controllers
│   │   └── engine.ts         # Engine controller (wraps SignClient)
│   ├── types/                # TypeScript type definitions
│   │   ├── client.ts         # Client types and interfaces
│   │   └── engine.ts         # Engine types and interfaces
│   └── utils/                # Utility functions
│       └── notifications.ts   # Notification utilities
└── test/                     # Test files
```

## Core Components

### 1. WalletKit Client (`src/client.ts`)

The main entry point for the SDK.

**Key Features:**
- Extends `IWalletKit` abstract class
- Uses EventEmitter for event handling
- Delegates core functionality to Engine controller
- Static `init()` method for async initialization

**Properties:**
- `name`: Client context name
- `core`: WalletConnect Core instance (from `@walletconnect/core`)
- `logger`: Logger instance
- `events`: EventEmitter instance
- `engine`: Engine controller instance
- `metadata`: Wallet metadata
- `signConfig`: Sign protocol configuration

**Methods:**
- Session management: `approveSession()`, `rejectSession()`, `updateSession()`, `extendSession()`, `disconnectSession()`
- Request handling: `respondSessionRequest()`
- Event emission: `emitSessionEvent()`
- Query methods: `getActiveSessions()`, `getPendingSessionProposals()`, `getPendingSessionRequests()`
- Authentication: `approveSessionAuthenticate()`, `rejectSessionAuthenticate()`, `formatAuthMessage()`
- Push notifications: `registerDeviceToken()`
- Pairing: `pair()`
- Event handlers: `on()`, `once()`, `off()`, `removeListener()`

### 2. Engine Controller (`src/controllers/engine.ts`)

Wraps the WalletConnect SignClient and provides the core business logic.

**Key Features:**
- Extends `IWalletKitEngine` abstract class
- Manages SignClient lifecycle
- Bridges SignClient events to WalletKit events
- Handles all protocol interactions

**Properties:**
- `signClient`: ISignClient instance (from `@walletconnect/sign-client`)

**Initialization:**
- Creates SignClient with Core, metadata, and signConfig
- Initializes event client

**Event Bridging:**
- Maps SignClient events to WalletKit events:
  - `session_request` → `session_request`
  - `session_proposal` → `session_proposal`
  - `session_delete` → `session_delete`
  - `proposal_expire` → `proposal_expire`
  - `session_request_expire` → `session_request_expire`
  - `session_authenticate` → `session_authenticate`

### 3. Type Definitions (`src/types/`)

**Client Types (`client.ts`):**
- `WalletKitTypes.Event`: Event type union
- `WalletKitTypes.EventArguments`: Event argument types
- `WalletKitTypes.Options`: Initialization options
- `WalletKitTypes.Metadata`: Wallet metadata
- `WalletKitTypes.INotifications`: Notification utilities interface
- `IWalletKit`: Abstract base class for WalletKit
- `IWalletKitEvents`: Abstract base class for events

**Engine Types (`engine.ts`):**
- `IWalletKitEngine`: Abstract base class for Engine
- Method signatures for all engine operations

### 4. Constants (`src/constants/`)

- Client context constants
- Request constants
- Configuration defaults

### 5. Utilities (`src/utils/notifications.ts`)

Static notification utilities:
- `decryptMessage()`: Decrypts encrypted messages using Core crypto
- `getMetadata()`: Retrieves session metadata using SessionStore

## Reference Implementation Analysis

### WalletConnect Core (`tmp/@walletconnect-core/`)

**Purpose:** Core WalletConnect protocol implementation that walletkit depends on.

**Key Components:**

1. **Core Class** (`src/core.ts`)
   - Main orchestrator for all WalletConnect functionality
   - Manages all controllers
   - Provides event system via EventEmitter
   - Handles initialization of all subsystems

2. **Controllers:**
   - **Crypto** (`controllers/crypto.ts`): Cryptographic operations, key management
   - **Relayer** (`controllers/relayer.ts`): WebSocket-based message relaying
   - **Pairing** (`controllers/pairing.ts`): Pairing management
   - **History** (`controllers/history.ts`): JSON-RPC request/response history
   - **Expirer** (`controllers/expirer.ts`): Expiration management for sessions/pairings
   - **Verify** (`controllers/verify.ts`): Verification utilities
   - **Echo** (`controllers/echo.ts`): Push notification client
   - **Events** (`controllers/events.ts`): Event client for telemetry
   - **Store** (`controllers/store.ts`): Generic storage interface
   - **Subscriber** (`controllers/subscriber.ts`): Topic subscription management
   - **Publisher** (`controllers/publisher.ts`): Message publishing
   - **Messages** (`controllers/messages.ts`): Message handling
   - **Keychain** (`controllers/keychain.ts`): Keychain management

3. **Storage Abstraction:**
   - Uses `@walletconnect/keyvaluestorage` for persistence
   - Supports custom storage backends
   - Handles storage options and prefixes

4. **Event System:**
   - EventEmitter-based
   - Hierarchical event propagation
   - Event history tracking

### WalletConnect Utils (`tmp/@walletconnect-utils/`)

**Purpose:** Utility functions used across WalletConnect packages.

**Key Modules:**
- **CAIP** (`src/caip.ts`): Chain Agnostic Improvement Proposals utilities
- **CACAO** (`src/cacao.ts`): Chain Agnostic CApability Object handling
- **Crypto** (`src/crypto.ts`): Cryptographic utilities
- **URI** (`src/uri.ts`): WalletConnect URI parsing/formatting
- **Validators** (`src/validators.ts`): Validation utilities
- **Namespaces** (`src/namespaces.ts`): Namespace handling
- **Signatures** (`src/signatures.ts`): Signature utilities
- **Relay** (`src/relay.ts`): Relay protocol utilities
- **Network** (`src/network.ts`): Network utilities
- **Polkadot** (`src/polkadot.ts`): Polkadot-specific utilities
- **Logger** (`src/logger.ts`): Logging utilities
- **Memory Store** (`src/memoryStore.ts`): In-memory storage implementation
- **Misc** (`src/misc.ts`): Miscellaneous utilities
- **Errors** (`src/errors.ts`): Error definitions

## Dependency Analysis

### Direct Dependencies (from `package.json`)

1. **`@walletconnect/core` (v2.23.0)**
   - Core protocol implementation
   - Used for: Core instance, pairing, crypto, relayer, storage
   - Reference: `tmp/@walletconnect-core/`

2. **`@walletconnect/sign-client` (v2.23.0)**
   - Sign protocol client
   - Used for: Session management, signing operations
   - Wrapped by Engine controller

3. **`@walletconnect/types` (v2.23.0)**
   - TypeScript type definitions
   - Used for: Type imports (ICore, SignClientTypes, etc.)

4. **`@walletconnect/jsonrpc-provider` (v1.0.14)**
   - JSON-RPC provider
   - Used by: Core (transitive)

5. **`@walletconnect/jsonrpc-utils` (v1.0.8)**
   - JSON-RPC utilities
   - Used for: JsonRpcPayload, ErrorResponse, JsonRpcResponse types

6. **`@walletconnect/logger` (v3.0.0)**
   - Logging utilities
   - Used for: Logger interface

### Transitive Dependencies (from Core)

- `@walletconnect/keyvaluestorage`: Storage abstraction
- `@walletconnect/relay-api`: Relay API client
- `@walletconnect/relay-auth`: Relay authentication
- `@walletconnect/heartbeat`: Heartbeat mechanism
- `@walletconnect/jsonrpc-ws-connection`: WebSocket connection
- `events`: EventEmitter (Node.js)
- `uint8arrays`: Byte array utilities

### Transitive Dependencies (from Utils)

- `@noble/ciphers`, `@noble/curves`, `@noble/hashes`: Cryptographic libraries
- `@msgpack/msgpack`: MessagePack serialization
- `@scure/base`: Base encoding utilities
- `blakejs`: Blake hash implementation
- `bs58`: Base58 encoding
- `ox`: Ethereum utilities

## Design Patterns

### 1. Abstract Base Classes

Both `IWalletKit` and `IWalletKitEngine` use abstract base classes to define interfaces:
- TypeScript abstract classes with abstract methods
- Python equivalent: ABC (Abstract Base Classes) from `abc` module

### 2. Event-Driven Architecture

- EventEmitter pattern throughout
- Event delegation from Engine to Client
- Event bridging from SignClient to WalletKit events

### 3. Controller Pattern

- Engine acts as controller for SignClient
- Core uses multiple controllers for different concerns
- Separation of concerns

### 4. Dependency Injection

- Core instance injected into WalletKit
- Logger, storage, and other dependencies injected
- Allows for testing and customization

### 5. Factory Pattern

- Static `init()` methods for async initialization
- Returns configured instances

## Event System

### Event Flow

```
SignClient Event → Engine Handler → WalletKit Event → User Listener
```

### Event Types

1. **`session_proposal`**: New session proposal received
2. **`session_request`**: Session request received
3. **`session_delete`**: Session deleted
4. **`proposal_expire`**: Proposal expired
5. **`session_request_expire`**: Session request expired
6. **`session_authenticate`**: Authentication request

### Event Handling

- Events are typed with TypeScript generics
- Event arguments are strongly typed
- Listeners receive typed event arguments

## TODO

- [ ] Analyze test structure and patterns
- [ ] Document error handling patterns
- [ ] Analyze async/await usage patterns
- [ ] Document storage patterns in detail
- [ ] Analyze WebSocket connection lifecycle
- [ ] Document crypto operations in detail
- [ ] Analyze pairing flow in detail

