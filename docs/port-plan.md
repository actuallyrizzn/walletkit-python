# Port Plan

## Purpose

This document outlines the phased implementation plan for porting the WalletKit SDK from TypeScript/JavaScript to Python. It provides a step-by-step approach with detailed tasks for each phase.

**Note:** For a complete project plan including virtual environment setup, testing suite configuration, and detailed workflow, see [Project Plan](project-plan.md).

## Table of Contents

1. [Overview](#overview)
2. [Phases](#phases)
3. [File-by-File Mapping](#file-by-file-mapping)
4. [Testing Strategy](#testing-strategy)
5. [Build and Distribution](#build-and-distribution)

## Overview

The port will be executed in phases, starting with foundational components and building up to the full WalletKit implementation. Each phase builds on the previous one.

## Phases

### Phase 0: Foundation

**Goal:** Set up Python project structure and identify/port core dependencies.

#### Tasks

1. **Project Setup**
   - [ ] Create Python package structure
   - [ ] Set up `pyproject.toml` or `setup.py`
   - [ ] Configure development dependencies (pytest, black, mypy, etc.)
   - [ ] Set up CI/CD pipeline
   - [ ] Create `.gitignore` for Python

2. **Dependency Analysis**
   - [ ] Research existing Python WalletConnect libraries
   - [ ] Identify Python equivalents for all dependencies
   - [ ] Document dependency decisions
   - [ ] Create requirements files

3. **Core Dependencies - Event System**
   - [ ] Implement EventEmitter class in Python
   - [ ] Support async event handling
   - [ ] Match TypeScript EventEmitter API
   - [ ] Write tests

4. **Core Dependencies - Storage**
   - [ ] Create storage abstraction interface
   - [ ] Implement file-based storage backend
   - [ ] Implement in-memory storage backend
   - [ ] Write tests

5. **Core Dependencies - JSON-RPC**
   - [ ] Implement JSON-RPC message types
   - [ ] Implement JSON-RPC utilities
   - [ ] Write tests

6. **Core Dependencies - Crypto (Minimal)**
   - [ ] Identify required crypto operations
   - [ ] Implement encryption/decryption (ChaCha20-Poly1305)
   - [ ] Implement key generation (X25519)
   - [ ] Write tests

**Deliverables:**
- Python project structure
- EventEmitter implementation
- Storage abstraction with backends
- JSON-RPC utilities
- Minimal crypto implementation

### Phase 1: Core Types and Interfaces

**Goal:** Port all type definitions and create Python equivalents.

#### Tasks

1. **Type Definitions**
   - [ ] Port `@walletconnect/types` interfaces to Python
   - [ ] Create Protocol classes for interfaces
   - [ ] Create dataclasses for data structures
   - [ ] Add type hints throughout

2. **WalletKit Types**
   - [ ] Port `src/types/client.ts` to Python
   - [ ] Port `src/types/engine.ts` to Python
   - [ ] Create abstract base classes (ABC)
   - [ ] Add type hints

3. **Constants**
   - [ ] Port `src/constants/` to Python
   - [ ] Convert to Python constants or enums

**Deliverables:**
- Complete type definitions in Python
- Abstract base classes
- Constants and enums

### Phase 2: Event System and Base Classes

**Goal:** Implement event system and base classes for controllers.

#### Tasks

1. **Event System Enhancement**
   - [ ] Enhance EventEmitter for typed events
   - [ ] Support event filtering
   - [ ] Support event history (if needed)

2. **Base Classes**
   - [ ] Implement `IWalletKit` abstract class
   - [ ] Implement `IWalletKitEngine` abstract class
   - [ ] Implement `IWalletKitEvents` abstract class

3. **Controller Base**
   - [ ] Create base controller class
   - [ ] Add common controller functionality

**Deliverables:**
- Enhanced event system
- Abstract base classes
- Controller base class

### Phase 3: Core Controllers (Minimal Implementation)

**Goal:** Implement minimal Core controllers needed by walletkit.

#### Tasks

1. **Crypto Controller**
   - [ ] Port crypto operations from Core
   - [ ] Implement key management
   - [ ] Implement encryption/decryption
   - [ ] Write tests

2. **Relayer Controller**
   - [ ] Implement WebSocket connection
   - [ ] Implement message publishing
   - [ ] Implement message subscription
   - [ ] Implement reconnection logic
   - [ ] Write tests

3. **Pairing Controller**
   - [ ] Implement pairing creation
   - [ ] Implement pairing storage
   - [ ] Implement pairing activation
   - [ ] Write tests

4. **Core Class (Minimal)**
   - [ ] Implement minimal Core class
   - [ ] Integrate controllers
   - [ ] Implement initialization
   - [ ] Write tests

**Deliverables:**
- Crypto controller
- Relayer controller
- Pairing controller
- Minimal Core class

### Phase 4: Sign Client (Minimal Implementation)

**Goal:** Implement minimal Sign Client wrapper needed by Engine.

#### Tasks

1. **Sign Client Wrapper**
   - [ ] Analyze Sign Client API used by Engine
   - [ ] Implement minimal Sign Client interface
   - [ ] Integrate with Core
   - [ ] Implement session management
   - [ ] Write tests

2. **Session Operations**
   - [ ] Implement session approval
   - [ ] Implement session rejection
   - [ ] Implement session update
   - [ ] Implement session extension
   - [ ] Implement session disconnect
   - [ ] Write tests

3. **Request/Response Handling**
   - [ ] Implement request handling
   - [ ] Implement response handling
   - [ ] Implement event emission
   - [ ] Write tests

**Deliverables:**
- Sign Client wrapper
- Session management
- Request/response handling

### Phase 5: Engine Controller

**Goal:** Port Engine controller from walletkit.

#### Tasks

1. **Engine Implementation**
   - [ ] Port `src/controllers/engine.ts` to Python
   - [ ] Integrate with Sign Client
   - [ ] Implement event bridging
   - [ ] Write tests

2. **Event Bridging**
   - [ ] Map Sign Client events to WalletKit events
   - [ ] Implement event handlers
   - [ ] Write tests

3. **Method Implementations**
   - [ ] Implement all Engine methods
   - [ ] Add error handling
   - [ ] Write tests

**Deliverables:**
- Engine controller
- Event bridging
- All Engine methods

### Phase 6: WalletKit Client

**Goal:** Port WalletKit client class.

#### Tasks

1. **Client Implementation**
   - [ ] Port `src/client.ts` to Python
   - [ ] Integrate with Engine
   - [ ] Implement initialization
   - [ ] Write tests

2. **Public API**
   - [ ] Implement all public methods
   - [ ] Add error handling
   - [ ] Add logging
   - [ ] Write tests

3. **Event Handling**
   - [ ] Implement event delegation
   - [ ] Write tests

**Deliverables:**
- WalletKit client class
- Complete public API
- Event handling

### Phase 7: Utilities and Constants

**Goal:** Port utilities and constants.

#### Tasks

1. **Utilities**
   - [ ] Port `src/utils/notifications.ts` to Python
   - [ ] Port other utilities as needed
   - [ ] Write tests

2. **Constants**
   - [ ] Port all constants
   - [ ] Convert to Python format

3. **Public API**
   - [ ] Port `src/index.ts` exports
   - [ ] Create `__init__.py` with exports

**Deliverables:**
- Utilities
- Constants
- Public API exports

### Phase 8: Testing

**Goal:** Port and create comprehensive tests.

#### Tasks

1. **Test Porting**
   - [ ] Port tests from `test/sign.spec.ts`
   - [ ] Port tests from `test/multitenancy.spec.ts`
   - [ ] Adapt to pytest
   - [ ] Fix any issues

2. **Integration Tests**
   - [ ] Create integration tests
   - [ ] Test with real WalletConnect protocol
   - [ ] Test compatibility

3. **Test Coverage**
   - [ ] Achieve high test coverage
   - [ ] Add missing test cases
   - [ ] Document test strategy

**Deliverables:**
- Ported tests
- Integration tests
- High test coverage

## File-by-File Mapping

### Source Files

| TypeScript | Python | Status |
|-----------|--------|--------|
| `src/index.ts` | `src/__init__.py` | TODO |
| `src/client.ts` | `src/client.py` | TODO |
| `src/controllers/engine.ts` | `src/controllers/engine.py` | TODO |
| `src/types/client.ts` | `src/types/client.py` | TODO |
| `src/types/engine.ts` | `src/types/engine.py` | TODO |
| `src/constants/client.ts` | `src/constants/client.py` | TODO |
| `src/constants/request.ts` | `src/constants/request.py` | TODO |
| `src/utils/notifications.ts` | `src/utils/notifications.py` | TODO |

### Test Files

| TypeScript | Python | Status |
|-----------|--------|--------|
| `test/sign.spec.ts` | `tests/test_sign.py` | TODO |
| `test/multitenancy.spec.ts` | `tests/test_multitenancy.py` | TODO |
| `test/shared/helpers.ts` | `tests/shared/helpers.py` | TODO |
| `test/shared/values.ts` | `tests/shared/values.py` | TODO |

## Testing Strategy

### Unit Tests

- Use `pytest` for testing framework
- Test each component in isolation
- Mock dependencies where appropriate
- Aim for >80% code coverage

### Integration Tests

- Test with real WalletConnect protocol
- Test compatibility with JavaScript implementation
- Test end-to-end flows

### Test Porting

1. Port test structure
2. Adapt test syntax (Jest → pytest)
3. Port test helpers
4. Port test values
5. Fix any compatibility issues

## Build and Distribution

### Package Structure

```
walletkit-python/
├── src/
│   └── walletkit/
│       ├── __init__.py
│       ├── client.py
│       ├── controllers/
│       ├── types/
│       ├── constants/
│       └── utils/
├── tests/
├── docs/
├── pyproject.toml
├── README.md
└── LICENSE
```

### Build Tool

**Options:**
- `setuptools` (traditional)
- `poetry` (modern, recommended)
- `hatchling` (PEP 517)

**Recommendation:** `poetry` for dependency management and building.

### Distribution

- Publish to PyPI
- Version following semantic versioning
- Include type stubs for type checking
- Include documentation

### Development Setup

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linter
poetry run black .
poetry run mypy src/

# Build package
poetry build
```

## TODO

- [ ] Create detailed task breakdown for each phase
- [ ] Estimate effort for each phase
- [ ] Set up project structure
- [ ] Create initial proof-of-concept
- [ ] Document any deviations from plan

