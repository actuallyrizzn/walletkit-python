# Reference Implementation Catalog

## Purpose

This document catalogs the reference implementations in the `tmp/` folder, which contain the WalletConnect Core and Utils libraries that walletkit depends on. Understanding these implementations is critical for planning the Python port.

## Table of Contents

1. [WalletConnect Core](#walletconnect-core)
2. [WalletConnect Utils](#walletconnect-utils)
3. [Usage Analysis](#usage-analysis)
4. [Porting Priorities](#porting-priorities)

## WalletConnect Core

**Location:** `tmp/@walletconnect-core/`

**Version:** 2.23.1

**Purpose:** Core WalletConnect protocol implementation providing the foundation for all WalletConnect functionality.

### File Structure

```
tmp/@walletconnect-core/
├── src/
│   ├── core.ts                    # Main Core class
│   ├── index.ts                   # Public exports
│   ├── constants/                 # Constants and configuration
│   │   ├── core.ts
│   │   ├── crypto.ts
│   │   ├── echo.ts
│   │   ├── events.ts
│   │   ├── expirer.ts
│   │   ├── history.ts
│   │   ├── keychain.ts
│   │   ├── messages.ts
│   │   ├── pairing.ts
│   │   ├── publisher.ts
│   │   ├── relayer.ts
│   │   ├── store.ts
│   │   ├── subscriber.ts
│   │   └── verify.ts
│   └── controllers/               # Business logic controllers
│       ├── crypto.ts
│       ├── echo.ts
│       ├── events.ts
│       ├── expirer.ts
│       ├── history.ts
│       ├── keychain.ts
│       ├── messages.ts
│       ├── pairing.ts
│       ├── publisher.ts
│       ├── relayer.ts
│       ├── store.ts
│       ├── subscriber.ts
│       ├── topicmap.ts
│       └── verify.ts
└── test/                          # Test files
```

### Core Class Architecture

**File:** `src/core.ts`

**Key Responsibilities:**
- Orchestrates all WalletConnect subsystems
- Manages initialization lifecycle
- Provides unified event system
- Handles global core instance management

**Properties:**
- `protocol`, `version`: Protocol identification
- `name`: Context name
- `relayUrl`, `projectId`: Configuration
- `events`: EventEmitter instance
- `logger`: Logger instance
- `heartbeat`: Heartbeat controller
- `relayer`: Relayer controller
- `crypto`: Crypto controller
- `storage`: Storage abstraction
- `history`: History controller
- `expirer`: Expirer controller
- `pairing`: Pairing controller
- `verify`: Verify controller
- `echoClient`: Echo (push) client
- `eventClient`: Event (telemetry) client

**Initialization Flow:**
1. Initialize crypto
2. Initialize history
3. Initialize expirer
4. Initialize relayer
5. Initialize heartbeat
6. Initialize pairing
7. Load link mode supported apps

### Controllers

#### 1. Crypto Controller (`controllers/crypto.ts`)

**Purpose:** Cryptographic operations and key management

**Key Features:**
- Key generation and storage
- Encryption/decryption
- Client ID generation
- Keychain management

**Dependencies:**
- Uses storage for key persistence
- Integrates with keychain controller

#### 2. Relayer Controller (`controllers/relayer.ts`)

**Purpose:** WebSocket-based message relaying

**Key Features:**
- WebSocket connection management
- Message publishing
- Message subscription
- Topic management
- Connection lifecycle

**Dependencies:**
- `@walletconnect/jsonrpc-ws-connection`
- `@walletconnect/relay-api`
- Publisher and Subscriber controllers

#### 3. Pairing Controller (`controllers/pairing.ts`)

**Purpose:** Pairing management

**Key Features:**
- Pairing creation
- Pairing storage
- Pairing expiration
- Pairing activation

**Dependencies:**
- Relayer for communication
- Expirer for expiration management
- Storage for persistence

#### 4. History Controller (`controllers/history.ts`)

**Purpose:** JSON-RPC request/response history

**Key Features:**
- Request tracking
- Response tracking
- History persistence
- History expiration

#### 5. Expirer Controller (`controllers/expirer.ts`)

**Purpose:** Expiration management

**Key Features:**
- Tracks expiration times
- Automatic expiration
- Expiration events

#### 6. Verify Controller (`controllers/verify.ts`)

**Purpose:** Verification utilities

**Key Features:**
- Domain verification
- Attestation verification
- Verification storage

#### 7. Echo Client (`controllers/echo.ts`)

**Purpose:** Push notification client

**Key Features:**
- Device token registration
- Push notification handling

#### 8. Events Client (`controllers/events.ts`)

**Purpose:** Telemetry and event tracking

**Key Features:**
- Event tracking
- Telemetry collection

#### 9. Store Controller (`controllers/store.ts`)

**Purpose:** Generic storage interface

**Key Features:**
- Key-value storage abstraction
- Storage operations (get, set, delete)

#### 10. Subscriber Controller (`controllers/subscriber.ts`)

**Purpose:** Topic subscription management

**Key Features:**
- Topic subscriptions
- Subscription tracking
- Unsubscription

#### 11. Publisher Controller (`controllers/publisher.ts`)

**Purpose:** Message publishing

**Key Features:**
- Message publishing
- Publishing queue
- Retry logic

#### 12. Messages Controller (`controllers/messages.ts`)

**Purpose:** Message handling

**Key Features:**
- Message encoding/decoding
- Message validation
- Message routing

#### 13. Keychain Controller (`controllers/keychain.ts`)

**Purpose:** Keychain management

**Key Features:**
- Key storage
- Key retrieval
- Key deletion

### Storage Patterns

- Uses `@walletconnect/keyvaluestorage` abstraction
- Supports custom storage backends
- Storage prefix support for multi-instance scenarios
- Async storage operations

### Event Flow

- EventEmitter-based event system
- Hierarchical event propagation
- Event history tracking
- Event filtering

## WalletConnect Utils

**Location:** `tmp/@walletconnect-utils/`

**Version:** 2.23.1

**Purpose:** Utility functions used across WalletConnect packages.

### File Structure

```
tmp/@walletconnect-utils/
├── src/
│   ├── index.ts              # Public exports
│   ├── caip.ts              # CAIP utilities
│   ├── cacao.ts             # CACAO handling
│   ├── crypto.ts            # Cryptographic utilities
│   ├── errors.ts            # Error definitions
│   ├── logger.ts            # Logging utilities
│   ├── memoryStore.ts       # In-memory storage
│   ├── misc.ts              # Miscellaneous utilities
│   ├── namespaces.ts        # Namespace handling
│   ├── network.ts           # Network utilities
│   ├── polkadot.ts          # Polkadot-specific utilities
│   ├── relay.ts             # Relay protocol utilities
│   ├── signatures.ts        # Signature utilities
│   ├── uri.ts               # URI parsing/formatting
│   └── validators.ts        # Validation utilities
└── test/                    # Test files
```

### Utility Categories

#### 1. CAIP (`src/caip.ts`)

**Purpose:** Chain Agnostic Improvement Proposals utilities

**Functions:**
- Chain ID parsing/formatting
- Account ID parsing/formatting
- Namespace handling

#### 2. CACAO (`src/cacao.ts`)

**Purpose:** Chain Agnostic CApability Object handling

**Functions:**
- CACAO creation
- CACAO validation
- CACAO parsing

#### 3. Crypto (`src/crypto.ts`)

**Purpose:** Cryptographic utilities

**Functions:**
- Key generation
- Encryption/decryption
- Hash functions
- Signature operations

**Dependencies:**
- `@noble/ciphers`
- `@noble/curves`
- `@noble/hashes`

#### 4. URI (`src/uri.ts`)

**Purpose:** WalletConnect URI parsing/formatting

**Functions:**
- URI parsing
- URI formatting
- URI validation

#### 5. Validators (`src/validators.ts`)

**Purpose:** Validation utilities

**Functions:**
- Type validation
- Format validation
- Value validation

#### 6. Namespaces (`src/namespaces.ts`)

**Purpose:** Namespace handling

**Functions:**
- Namespace parsing
- Namespace validation
- Namespace manipulation

#### 7. Signatures (`src/signatures.ts`)

**Purpose:** Signature utilities

**Functions:**
- Signature creation
- Signature verification
- Signature formatting

#### 8. Relay (`src/relay.ts`)

**Purpose:** Relay protocol utilities

**Functions:**
- Relay message formatting
- Relay protocol handling

#### 9. Network (`src/network.ts`)

**Purpose:** Network utilities

**Functions:**
- Network detection
- Network configuration

#### 10. Polkadot (`src/polkadot.ts`)

**Purpose:** Polkadot-specific utilities

**Functions:**
- Polkadot account handling
- Polkadot-specific operations

#### 11. Logger (`src/logger.ts`)

**Purpose:** Logging utilities

**Functions:**
- Logger creation
- Log formatting
- Log levels

#### 12. Memory Store (`src/memoryStore.ts`)

**Purpose:** In-memory storage implementation

**Functions:**
- In-memory key-value storage
- Storage operations

#### 13. Misc (`src/misc.ts`)

**Purpose:** Miscellaneous utilities

**Functions:**
- Various helper functions

#### 14. Errors (`src/errors.ts`)

**Purpose:** Error definitions

**Functions:**
- Error creation
- Error formatting
- Error types

## Usage Analysis

### What WalletKit Imports from Core

From analysis of `packages/walletkit/src/`:

1. **Core Class:**
   - `Core` class for initialization
   - Used in: `utils/notifications.ts`

2. **Core Instance (ICore):**
   - Injected into WalletKit constructor
   - Used for: pairing, crypto, echoClient, eventClient

3. **Core Types:**
   - `ICore` interface
   - `CoreTypes.Metadata`
   - `CoreTypes.Options`

### What WalletKit Imports from Sign Client

1. **SignClient Class:**
   - Used in Engine controller
   - Wrapped by Engine

2. **SignClient Types:**
   - `ISignClient` interface
   - `SessionTypes`
   - `SignClientTypes`

### What WalletKit Imports from Utils

1. **JSON-RPC Utils:**
   - `JsonRpcPayload`
   - `JsonRpcResponse`
   - `ErrorResponse`

2. **Types:**
   - Various type definitions

### What WalletKit Imports from Types

1. **Core Types:**
   - `ICore`
   - `CoreTypes`

2. **Sign Client Types:**
   - `SignClientTypes`
   - `SessionTypes`
   - `ProposalTypes`
   - `PendingRequestTypes`
   - `EchoClientTypes`
   - `AuthTypes`
   - `EngineTypes`

3. **Logger:**
   - `Logger` interface

## Porting Priorities

### Critical (Must Port)

1. **Core Functionality:**
   - Core class initialization
   - Crypto controller (for encryption/decryption)
   - Relayer controller (for WebSocket communication)
   - Pairing controller (for pairing management)
   - Storage abstraction

2. **Sign Client:**
   - SignClient wrapper
   - Session management
   - Request/response handling

3. **Utils:**
   - JSON-RPC utilities
   - URI parsing/formatting
   - Crypto utilities (as needed)

### High Priority (Should Port)

1. **Core Controllers:**
   - History controller
   - Expirer controller
   - Verify controller

2. **Utils:**
   - CAIP utilities
   - Namespace handling
   - Validators

### Medium Priority (Nice to Have)

1. **Core Controllers:**
   - Echo client (push notifications)
   - Events client (telemetry)

2. **Utils:**
   - CACAO handling
   - Polkadot utilities
   - Network utilities

### Low Priority (Can Simplify or Omit)

1. **Core Controllers:**
   - Advanced storage features
   - Complex event tracking

2. **Utils:**
   - Some validation utilities
   - Some misc utilities

## TODO

- [ ] Analyze which Core controllers are actually used by walletkit
- [ ] Document exact API surface needed from Core
- [ ] Document exact API surface needed from Sign Client
- [ ] Analyze test coverage of reference implementations
- [ ] Document protocol compliance requirements
- [ ] Analyze performance characteristics
- [ ] Document threading/async requirements

