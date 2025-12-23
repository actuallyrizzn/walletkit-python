# Full Project Plan: WalletKit Python Port

## Purpose

This document provides a complete, actionable project plan for porting the WalletKit SDK from TypeScript/JavaScript to Python, including project setup, virtual environment configuration, testing suite, and phased implementation.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Project Setup](#project-setup)
4. [Virtual Environment Setup](#virtual-environment-setup)
5. [Project Structure](#project-structure)
6. [Testing Suite Setup](#testing-suite-setup)
7. [Implementation Phases](#implementation-phases)
8. [Dependencies Management](#dependencies-management)
9. [Development Workflow](#development-workflow)
10. [Build and Distribution](#build-and-distribution)

## Project Overview

### Goals

- Port `@reown/walletkit` from TypeScript/JavaScript to Python
- Maintain API compatibility where possible (adapted to Python conventions)
- Ensure WalletConnect protocol compatibility
- Provide comprehensive test coverage
- Create production-ready Python package

### Success Criteria

- All WalletKit functionality ported and working
- Test coverage >80%
- Protocol compatibility verified
- Documentation complete
- Package published to PyPI (optional)

## Prerequisites

### System Requirements

- **Python:** 3.8 or higher (3.10+ recommended)
- **Operating System:** Windows, Linux, or macOS
- **Git:** For version control
- **Node.js/npm:** For reference implementation access (optional)

### Required Knowledge

- Python async/await
- Python type hints
- pytest testing framework
- Python packaging (setuptools/poetry)

## Project Setup

### Step 1: Initialize Project

```bash
# Navigate to project root
cd walletkit-python

# Initialize git (if not already done)
git init

# Create .gitignore
```

**`.gitignore` content:**
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/
.venv

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
tmp/
*.log
```

### Step 2: Create Project Structure

```bash
# Create directory structure
mkdir -p src/walletkit/{controllers,types,constants,utils}
mkdir -p tests/{unit,integration,shared}
mkdir -p docs
```

## Virtual Environment Setup

### Step 1: Create Virtual Environment

**Windows:**
```powershell
# Create venv
python -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**
```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate
```

### Step 2: Upgrade pip and Tools

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install build tools
pip install --upgrade setuptools wheel
```

### Step 3: Install Development Dependencies

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

**`requirements-dev.txt` (initial):**
```
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# Code Quality
black>=23.7.0
flake8>=6.1.0
mypy>=1.5.0
isort>=5.12.0

# Type Stubs
types-requests>=2.31.0

# Documentation
sphinx>=7.1.0
sphinx-rtd-theme>=1.3.0
```

### Step 4: Verify Setup

```bash
# Verify Python version
python --version

# Verify pip
pip --version

# Verify venv is active (should show venv path)
which python  # Linux/macOS
where python  # Windows
```

## Project Structure

### Final Directory Structure

```
walletkit-python/
├── .github/
│   └── workflows/
│       └── ci.yml                 # CI/CD pipeline
├── docs/                           # Documentation (already created)
│   ├── README.md
│   ├── architecture-analysis.md
│   ├── research-findings.md
│   └── ...
├── src/
│   └── walletkit/                 # Main package
│       ├── __init__.py
│       ├── client.py              # WalletKit client
│       ├── controllers/
│       │   ├── __init__.py
│       │   └── engine.py          # Engine controller
│       ├── types/
│       │   ├── __init__.py
│       │   ├── client.py          # Client types
│       │   └── engine.py          # Engine types
│       ├── constants/
│       │   ├── __init__.py
│       │   ├── client.py
│       │   └── request.py
│       └── utils/
│           ├── __init__.py
│           └── notifications.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest configuration
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_client.py
│   │   ├── test_engine.py
│   │   └── test_events.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_integration.py
│   └── shared/
│       ├── __init__.py
│       ├── helpers.py             # Test helpers
│       └── values.py              # Test data
├── venv/                          # Virtual environment (gitignored)
├── .gitignore
├── .flake8                        # Flake8 configuration
├── .mypy.ini                       # MyPy configuration
├── pyproject.toml                  # Project configuration (Poetry)
├── pytest.ini                     # Pytest configuration
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
├── README.md
└── LICENSE
```

## Testing Suite Setup

### Step 1: Create pytest Configuration

**`pytest.ini`:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function

# Coverage
addopts = 
    --cov=walletkit
    --cov-report=html
    --cov-report=term-missing
    --cov-report=xml
    --cov-fail-under=80
    -v

# Markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    protocol: Protocol compatibility tests

# Logging
log_cli = true
log_cli_level = INFO
log_cli_format = %(asctime)s [%(levelname)8s] %(name)s: %(message)s
log_cli_date_format = %Y-%m-%d %H:%M:%S
```

### Step 2: Create conftest.py

**`tests/conftest.py`:**
```python
"""Pytest configuration and shared fixtures."""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest

# Test configuration
TEST_PROJECT_ID = os.getenv("TEST_PROJECT_ID", "test_project_id")
TEST_METADATA = {
    "name": "Test Wallet",
    "description": "Test Wallet for WalletKit Python",
    "url": "https://test.wallet.com",
    "icons": [],
}


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def core():
    """Create and initialize a Core instance for testing."""
    from walletkit.core import Core
    
    core = Core(project_id=TEST_PROJECT_ID)
    await core.start()
    yield core
    # Cleanup
    if core.relayer.connected:
        await core.relayer.transport_close()
    await core.relayer.transport_disconnect()


@pytest.fixture
async def walletkit(core):
    """Create and initialize a WalletKit instance for testing."""
    from walletkit import WalletKit
    
    walletkit = await WalletKit.init(
        core=core,
        metadata=TEST_METADATA
    )
    yield walletkit
    # Cleanup handled by core fixture


@pytest.fixture
def test_namespaces():
    """Test namespaces for session proposals."""
    return {
        "eip155": {
            "chains": ["eip155:1"],
            "methods": ["eth_sendTransaction", "eth_signTransaction"],
            "events": ["accountsChanged", "chainChanged"],
        }
    }


@pytest.fixture
def test_required_namespaces():
    """Test required namespaces."""
    return {
        "eip155": {
            "chains": ["eip155:1"],
            "methods": ["eth_sendTransaction"],
            "events": ["accountsChanged"],
        }
    }
```

### Step 3: Create Test Helpers

**`tests/shared/helpers.py`:**
```python
"""Test helper functions."""
import asyncio
from typing import Optional

from walletkit.core import Core


async def disconnect(core: Core) -> None:
    """Disconnect core relayer."""
    if core.relayer.connected:
        await core.relayer.transport_close()
    await core.relayer.transport_disconnect()


async def create_walletkit(
    project_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> "WalletKit":
    """Create and initialize a WalletKit instance for testing."""
    from walletkit import WalletKit
    from tests.shared.values import TEST_METADATA, TEST_PROJECT_ID
    
    if project_id is None:
        project_id = TEST_PROJECT_ID
    if metadata is None:
        metadata = TEST_METADATA
    
    core = Core(project_id=project_id)
    await core.start()
    
    walletkit = await WalletKit.init(
        core=core,
        metadata=metadata
    )
    
    return walletkit
```

**`tests/shared/values.py`:**
```python
"""Test data and constants."""
import os

TEST_PROJECT_ID = os.getenv("TEST_PROJECT_ID", "test_project_id")

TEST_METADATA = {
    "name": "Test Wallet",
    "description": "Test Wallet for WalletKit Python",
    "url": "https://test.wallet.com",
    "icons": [],
}

TEST_ETHEREUM_CHAIN = "eip155:1"

TEST_NAMESPACES = {
    "eip155": {
        "chains": ["eip155:1"],
        "methods": ["eth_sendTransaction", "eth_signTransaction"],
        "events": ["accountsChanged", "chainChanged"],
    }
}

TEST_REQUIRED_NAMESPACES = {
    "eip155": {
        "chains": ["eip155:1"],
        "methods": ["eth_sendTransaction"],
        "events": ["accountsChanged"],
    }
}

TEST_UPDATED_NAMESPACES = {
    "eip155": {
        "chains": ["eip155:1", "eip155:137"],
        "methods": ["eth_sendTransaction", "eth_signTransaction"],
        "events": ["accountsChanged", "chainChanged"],
    }
}
```

### Step 4: Create Sample Test Files

**`tests/unit/test_client.py`:**
```python
"""Unit tests for WalletKit client."""
import pytest

from walletkit import WalletKit
from walletkit.core import Core
from tests.shared.values import TEST_METADATA, TEST_PROJECT_ID


@pytest.mark.asyncio
async def test_walletkit_init():
    """Test WalletKit initialization."""
    core = Core(project_id=TEST_PROJECT_ID)
    await core.start()
    
    walletkit = await WalletKit.init(
        core=core,
        metadata=TEST_METADATA
    )
    
    assert walletkit is not None
    assert walletkit.core == core
    assert walletkit.metadata == TEST_METADATA
    assert walletkit.engine is not None


@pytest.mark.asyncio
async def test_walletkit_get_active_sessions(walletkit):
    """Test getting active sessions."""
    sessions = walletkit.get_active_sessions()
    assert isinstance(sessions, dict)
    assert len(sessions) == 0  # Initially empty
```

**`tests/integration/test_integration.py`:**
```python
"""Integration tests for WalletKit."""
import pytest

from tests.shared.values import TEST_METADATA, TEST_PROJECT_ID


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_session_flow(walletkit):
    """Test complete session flow."""
    # This will be implemented as we build out the functionality
    pass
```

### Step 5: Run Initial Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=walletkit --cov-report=html

# Run specific test file
pytest tests/unit/test_client.py

# Run with markers
pytest -m unit
pytest -m integration
```

## Implementation Phases

### Phase 0: Foundation (Week 1)

#### Day 1-2: Project Setup
- [x] Create project structure
- [x] Set up virtual environment
- [x] Configure testing suite
- [ ] Set up CI/CD pipeline
- [ ] Create initial package structure

#### Day 3-4: Core Dependencies
- [ ] Implement EventEmitter class
- [ ] Implement storage abstraction
- [ ] Implement JSON-RPC utilities
- [ ] Write tests for dependencies

#### Day 5: Type System
- [ ] Port type definitions
- [ ] Create Protocol classes
- [ ] Create dataclasses
- [ ] Add type hints

**Deliverables:**
- Working virtual environment
- Test suite running
- Core dependency implementations
- Type system in place

### Phase 1: Core Controllers (Week 2-3)

#### Week 2: Crypto and Storage
- [ ] Implement KeyChain class
- [ ] Implement Crypto controller
- [ ] Implement encryption/decryption
- [ ] Write comprehensive tests

#### Week 3: Relayer and Pairing
- [ ] Implement Relayer controller
- [ ] Implement WebSocket connection
- [ ] Implement Pairing controller
- [ ] Write comprehensive tests

**Deliverables:**
- Crypto controller working
- Relayer controller working
- Pairing controller working
- Tests passing

### Phase 2: Sign Client (Week 4-5)

**Status:** ⚠️ Stub implementation complete, full implementation needed

#### Week 4: SignClient Core Implementation
- [x] Create SignClient stub (placeholder)
- [ ] Implement Store for sessions (SessionStore)
- [ ] Implement Store for proposals (ProposalStore)
- [ ] Implement Store for pending requests (RequestStore)
- [ ] Implement session state management
- [ ] Implement proposal handling
- [ ] Implement request/response queue
- [ ] Write comprehensive tests

#### Week 5: SignClient Protocol Implementation
- [ ] Implement session proposal handling
- [ ] Implement session approval flow
- [ ] Implement session rejection flow
- [ ] Implement session update/extend
- [ ] Implement request/response handling
- [ ] Implement session disconnect
- [ ] Implement event emission
- [ ] Implement message encryption/decryption integration
- [ ] Write comprehensive tests

**Deliverables:**
- Full SignClient implementation (not stub)
- Session management working
- Request/response handling working
- All protocol operations functional
- Tests passing (>80% coverage)

### Phase 3: Engine and Client (Week 6)

**Status:** ✅ Complete

- [x] Port Engine controller
- [x] Port WalletKit client
- [x] Implement event bridging
- [x] Write comprehensive tests

**Deliverables:**
- ✅ Engine controller working
- ✅ WalletKit client working
- ✅ Event system functional
- ✅ Tests passing (40+ tests)

### Phase 4: Store Implementation (Week 7)

**Status:** ⚠️ Missing - Critical for SignClient

#### Tasks
- [ ] Implement Store base class (generic key-value store with persistence)
- [ ] Implement SessionStore (manages active sessions)
- [ ] Implement ProposalStore (manages pending proposals)
- [ ] Implement RequestStore (manages pending requests)
- [ ] Integrate stores with SignClient
- [ ] Add storage persistence (file-based)
- [ ] Write comprehensive tests

**Deliverables:**
- Store abstraction working
- All stores implemented
- Persistence working
- Tests passing

### Phase 5: Additional Controllers and Utilities (Week 8)

**Status:** ⚠️ Partially complete

#### Tasks
- [x] Implement Expirer controller (basic structure)
- [ ] Complete Expirer implementation (expiry management)
- [ ] Implement EventClient (analytics/telemetry)
- [ ] Implement EchoClient (push notifications)
- [ ] Implement Notifications utility (decryptMessage, getMetadata)
- [ ] Port remaining utilities
- [ ] Complete constants
- [ ] Write comprehensive tests

**Deliverables:**
- All controllers implemented
- Utilities complete
- Constants ported
- Tests passing

### Phase 6: Integration and Polish (Week 9)

- [ ] Write integration tests
- [ ] Protocol compatibility testing
- [ ] End-to-end flow testing
- [ ] Performance testing
- [ ] Error handling improvements
- [ ] Complete public API documentation

**Deliverables:**
- Integration tests passing
- Protocol compatibility verified
- Performance benchmarks
- Complete API surface

### Phase 7: Testing and Documentation (Week 10)

**Status:** 🔄 In Progress

- [x] Unit tests for core components (40+ tests)
- [ ] Port all tests from JavaScript
- [ ] Achieve >80% coverage (currently 64%)
- [ ] Write comprehensive documentation
- [ ] Create usage examples
- [ ] Create API reference
- [ ] Performance testing and optimization

**Deliverables:**
- Comprehensive test suite
- >80% test coverage
- Complete documentation
- Example code and tutorials
- API reference

## Dependencies Management

### Production Dependencies

**`requirements.txt`:**
```
# Core dependencies
websockets>=11.0.0          # WebSocket support
cryptography>=41.0.0         # Crypto operations
aiohttp>=3.9.0               # HTTP client
msgpack>=1.0.0               # MessagePack serialization
base58>=2.1.0                # Base58 encoding

# Optional but recommended
aiosqlite>=0.19.0            # SQLite storage backend
```

### Development Dependencies

**`requirements-dev.txt`:**
```
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0

# Code Quality
black>=23.7.0
flake8>=6.1.0
mypy>=1.5.0
isort>=5.12.0

# Documentation
sphinx>=7.1.0
sphinx-rtd-theme>=1.3.0
```

### Using Poetry (Recommended)

**`pyproject.toml`:**
```toml
[tool.poetry]
name = "walletkit"
version = "0.1.0"
description = "WalletKit SDK for Python"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
packages = [{include = "walletkit", from = "src"}]

[tool.poetry.dependencies]
python = "^3.8"
websockets = "^11.0"
cryptography = "^41.0"
aiohttp = "^3.9"
msgpack = "^1.0"
base58 = "^2.1"
aiosqlite = {version = "^0.19", optional = true}

[tool.poetry.group.dev.dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.21"
pytest-cov = "^4.1"
pytest-mock = "^3.11"
black = "^23.7"
flake8 = "^6.1"
mypy = "^1.5"
isort = "^5.12"
sphinx = "^7.1"
sphinx-rtd-theme = "^1.3"

[tool.poetry.extras]
sqlite = ["aiosqlite"]

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 100
target-version = ['py38', 'py39', 'py310', 'py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
```

**Install with Poetry:**
```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Install with SQLite extra
poetry install --extras sqlite

# Activate virtual environment
poetry shell
```

## Development Workflow

### Daily Workflow

1. **Activate Virtual Environment**
   ```bash
   # Windows
   .\venv\Scripts\Activate.ps1
   
   # Linux/macOS
   source venv/bin/activate
   ```

2. **Run Tests Before Starting**
   ```bash
   pytest
   ```

3. **Make Changes**
   - Write code
   - Write tests
   - Run tests frequently

4. **Code Quality Checks**
   ```bash
   # Format code
   black src/ tests/
   
   # Sort imports
   isort src/ tests/
   
   # Lint
   flake8 src/ tests/
   
   # Type check
   mypy src/
   ```

5. **Run Tests**
   ```bash
   # All tests
   pytest
   
   # With coverage
   pytest --cov=walletkit
   
   # Specific test
   pytest tests/unit/test_client.py::test_walletkit_init
   ```

6. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: implement feature X"
   ```

### Testing Workflow

1. **Write Test First (TDD)**
   - Write failing test
   - Implement feature
   - Make test pass
   - Refactor

2. **Run Tests Frequently**
   - After each change
   - Before committing
   - In CI/CD

3. **Coverage Goals**
   - Unit tests: >80% coverage
   - Integration tests: All major flows
   - Protocol tests: All protocol operations

### Code Review Checklist

- [ ] Tests pass
- [ ] Code formatted (black)
- [ ] Imports sorted (isort)
- [ ] No linting errors (flake8)
- [ ] Type hints added (mypy)
- [ ] Documentation updated
- [ ] Test coverage maintained

## Build and Distribution

### Building Package

**Using setuptools:**
```bash
# Build
python setup.py sdist bdist_wheel

# Check
twine check dist/*
```

**Using Poetry:**
```bash
# Build
poetry build

# Check
poetry check
```

### Publishing (Optional)

```bash
# Test PyPI
twine upload --repository testpypi dist/*

# Production PyPI
twine upload dist/*
```

## CI/CD Pipeline

### GitHub Actions

**`.github/workflows/ci.yml`:**
```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.8", "3.9", "3.10", "3.11"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
        pip install -r requirements.txt
    
    - name: Lint with flake8
      run: |
        flake8 src/ tests/
    
    - name: Type check with mypy
      run: |
        mypy src/
    
    - name: Test with pytest
      run: |
        pytest --cov=walletkit --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Timeline Summary

| Phase | Duration | Status | Key Deliverables |
|-------|----------|--------|------------------|
| Phase 0: Foundation | Week 1 | ✅ Complete | Project setup, venv, test suite, core dependencies |
| Phase 1: Core Controllers | Week 2-3 | ✅ Complete | Crypto, Relayer, Pairing controllers |
| Phase 2: Sign Client | Week 4-5 | ⚠️ Stub Only | **Full SignClient + Store implementation needed** |
| Phase 3: Engine and Client | Week 6 | ✅ Complete | Engine, WalletKit client, events |
| Phase 4: Store Implementation | Week 7 | ❌ Not Started | Store abstraction, SessionStore, ProposalStore, RequestStore |
| Phase 5: Additional Controllers | Week 8 | 🔄 Partial | Expirer, EventClient, EchoClient, Notifications |
| Phase 6: Integration and Polish | Week 9 | ❌ Not Started | Integration tests, protocol compatibility |
| Phase 7: Testing and Docs | Week 10 | 🔄 In Progress | >80% coverage, documentation, examples |

**Total Estimated Time:** 10 weeks
**Current Status:** ~60% complete (Phases 0, 1, 3 done; Phase 2 needs full implementation)

## Current Status and Next Steps

### ✅ Completed (Phases 0, 1, 3)
- Project setup and virtual environment
- Core dependencies (EventEmitter, Storage, JSON-RPC, Crypto)
- Core controllers (Crypto, Relayer, Pairing)
- Engine controller
- WalletKit client
- 40+ unit tests passing
- 64% code coverage

### ⚠️ Critical Missing Components

1. **Full SignClient Implementation** (Phase 2 - Week 4-5)
   - Currently using stub placeholder
   - Needs full session/proposal/request management
   - Requires Store implementation first

2. **Store Implementation** (Phase 4 - Week 7)
   - SessionStore for active sessions
   - ProposalStore for pending proposals
   - RequestStore for pending requests
   - Base Store abstraction with persistence

3. **Additional Controllers** (Phase 5 - Week 8)
   - Expirer (expiry management)
   - EventClient (analytics)
   - EchoClient (push notifications)
   - Notifications utility

### 🎯 Immediate Next Steps (Priority Order)

1. **Week 4-5: Full SignClient Implementation**
   - Implement Store base class
   - Implement SessionStore, ProposalStore, RequestStore
   - Complete SignClient protocol implementation
   - Replace stub with full implementation

2. **Week 7: Store Implementation**
   - Critical dependency for SignClient
   - Should be done before or alongside SignClient

3. **Week 8: Additional Controllers**
   - Complete Expirer, EventClient, EchoClient
   - Implement Notifications utility

4. **Week 9: Integration Testing**
   - End-to-end tests with real WalletConnect relay
   - Protocol compatibility verification

5. **Week 10: Documentation and Examples**
   - Complete API documentation
   - Create usage examples
   - Performance optimization

## TODO - Remaining Work

### Critical (Blocking)
- [ ] **Implement Store base class** (required for SignClient)
- [ ] **Implement SessionStore** (required for SignClient)
- [ ] **Implement ProposalStore** (required for SignClient)
- [ ] **Implement RequestStore** (required for SignClient)
- [ ] **Complete SignClient implementation** (replace stub)
- [ ] **Integration tests** (validate protocol compatibility)

### High Priority
- [ ] Complete Expirer controller
- [ ] Implement EventClient
- [ ] Implement EchoClient
- [ ] Implement Notifications utility
- [ ] Increase test coverage to >80%

### Medium Priority
- [ ] Set up CI/CD pipeline
- [ ] Create usage examples
- [ ] Complete API documentation
- [ ] Performance optimization
- [ ] Package distribution (PyPI)

### Low Priority
- [ ] Additional utilities
- [ ] Advanced features
- [ ] Migration guides

