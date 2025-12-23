# Testing and Validation Plan

## Purpose

This document outlines the testing strategy for the Python port of WalletKit, including test porting, framework selection, integration testing, and validation approaches.

## Table of Contents

1. [Test Porting Strategy](#test-porting-strategy)
2. [Python Testing Framework](#python-testing-framework)
3. [Integration Testing](#integration-testing)
4. [Compatibility Testing](#compatibility-testing)
5. [Test Coverage Goals](#test-coverage-goals)
6. [Protocol Compliance Testing](#protocol-compliance-testing)

## Test Porting Strategy

### Source Tests

Tests to port from `packages/walletkit/test/`:

1. **`test/sign.spec.ts`**
   - Sign protocol tests
   - Session management tests
   - Request/response tests

2. **`test/multitenancy.spec.ts`**
   - Multi-tenancy tests
   - Multiple instance tests

3. **`test/shared/helpers.ts`**
   - Test helpers
   - Utility functions

4. **`test/shared/values.ts`**
   - Test data
   - Constants

### Porting Process

#### Step 1: Analyze Test Structure

- Understand test organization
- Identify test patterns
- Map test utilities

#### Step 2: Port Test Framework

**JavaScript (Vitest):**
```typescript
import { describe, it, expect, beforeEach } from "vitest";

describe("WalletKit", () => {
  beforeEach(() => {
    // Setup
  });

  it("should approve session", async () => {
    // Test
    expect(result).toBeDefined();
  });
});
```

**Python (pytest):**
```python
import pytest

class TestWalletKit:
    @pytest.fixture
    def setup(self):
        # Setup
        yield
        # Teardown
    
    async def test_approve_session(self, setup):
        # Test
        assert result is not None
```

#### Step 3: Port Test Helpers

**JavaScript:**
```typescript
export async function createWalletKit() {
  const core = new Core({ projectId: TEST_PROJECT_ID });
  return await WalletKit.init({ core, metadata });
}
```

**Python:**
```python
async def create_walletkit():
    core = Core(project_id=TEST_PROJECT_ID)
    return await WalletKit.init(core=core, metadata=metadata)
```

#### Step 4: Port Test Data

**JavaScript:**
```typescript
export const TEST_METADATA = {
  name: "Test Wallet",
  description: "Test",
  url: "https://test.com",
  icons: [],
};
```

**Python:**
```python
TEST_METADATA = {
    "name": "Test Wallet",
    "description": "Test",
    "url": "https://test.com",
    "icons": [],
}
```

#### Step 5: Adapt Test Syntax

- Convert Jest/Vitest syntax to pytest
- Convert async/await patterns
- Convert assertions
- Convert mocks

### Reference Implementation Tests

#### Core Tests (`tmp/@walletconnect-core/test/`)

Tests that may be useful for reference:
- `core.spec.ts` - Core initialization tests
- `crypto.spec.ts` - Crypto operation tests
- `relayer.spec.ts` - Relayer tests
- `pairing.spec.ts` - Pairing tests

**Usage:** Reference for understanding expected behavior, not necessarily port all tests.

#### Utils Tests (`tmp/@walletconnect-utils/test/`)

Tests that may be useful for reference:
- `crypto.spec.ts` - Crypto utility tests
- `uri.spec.ts` - URI parsing tests
- `validators.spec.ts` - Validation tests

**Usage:** Reference for utility function behavior.

## Python Testing Framework

### Framework Selection: pytest

**Rationale:**
- Standard in Python ecosystem
- Excellent async support
- Great fixtures
- Good plugin ecosystem
- Easy to use

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest configuration and fixtures
├── test_sign.py            # Sign protocol tests
├── test_multitenancy.py     # Multi-tenancy tests
├── test_client.py           # Client tests
├── test_engine.py           # Engine tests
├── test_events.py            # Event tests
├── shared/
│   ├── __init__.py
│   ├── helpers.py           # Test helpers
│   └── values.py             # Test data
└── integration/
    ├── __init__.py
    └── test_integration.py   # Integration tests
```

### Pytest Configuration

**`pytest.ini` or `pyproject.toml`:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

### Fixtures

**`tests/conftest.py`:**
```python
import pytest
from walletkit import WalletKit
from walletconnect.core import Core

@pytest.fixture
async def core():
    core = Core(project_id=TEST_PROJECT_ID)
    await core.start()
    yield core
    # Cleanup

@pytest.fixture
async def walletkit(core):
    walletkit = await WalletKit.init(
        core=core,
        metadata=TEST_METADATA
    )
    yield walletkit
    # Cleanup
```

### Async Testing

**pytest-asyncio:**
```python
import pytest

@pytest.mark.asyncio
async def test_async_operation(walletkit):
    result = await walletkit.approve_session(...)
    assert result is not None
```

### Mocking

**unittest.mock:**
```python
from unittest.mock import AsyncMock, patch

async def test_with_mock(walletkit):
    with patch('walletkit.engine.sign_client') as mock:
        mock.approve = AsyncMock(return_value=session)
        result = await walletkit.approve_session(...)
        mock.approve.assert_called_once()
```

## Integration Testing

### End-to-End Tests

Test complete flows:

1. **Pairing Flow:**
   - Create pairing URI
   - Pair with URI
   - Verify pairing

2. **Session Flow:**
   - Receive proposal
   - Approve session
   - Handle requests
   - Disconnect session

3. **Request/Response Flow:**
   - Receive request
   - Process request
   - Send response
   - Verify response

### Test with Real WalletConnect Protocol

**Approach:**
- Use test WalletConnect relay
- Test with real dApps (if possible)
- Test protocol compatibility

**Tools:**
- Test relay server
- Test dApps
- Protocol validators

### Multi-Instance Testing

Test multiple WalletKit instances:
- Multiple wallets
- Multiple dApps
- Concurrent operations

## Compatibility Testing

### Protocol Compatibility

**Test Areas:**
1. **Message Formats:**
   - JSON-RPC messages
   - Session proposals
   - Session requests
   - Event messages

2. **Crypto Operations:**
   - Encryption/decryption
   - Key generation
   - Signatures

3. **WebSocket Communication:**
   - Connection establishment
   - Message sending
   - Message receiving
   - Reconnection

### JavaScript Compatibility

**Test Areas:**
1. **API Compatibility:**
   - Same functionality
   - Same behavior
   - Same error handling

2. **Protocol Compatibility:**
   - Can communicate with JavaScript implementation
   - Same message formats
   - Same crypto operations

### Cross-Platform Testing

**Test Areas:**
1. **Platform Compatibility:**
   - Windows
   - Linux
   - macOS

2. **Python Version Compatibility:**
   - Python 3.8+
   - Different Python versions

## Test Coverage Goals

### Coverage Targets

- **Unit Tests:** >80% code coverage
- **Integration Tests:** All major flows
- **Protocol Tests:** All protocol operations

### Coverage Tools

**pytest-cov:**
```bash
pytest --cov=walletkit --cov-report=html
```

### Coverage Areas

1. **Core Functionality:**
   - All public methods
   - All event handlers
   - All error paths

2. **Edge Cases:**
   - Error conditions
   - Boundary conditions
   - Concurrent operations

3. **Protocol Operations:**
   - All protocol messages
   - All crypto operations
   - All WebSocket operations

## Protocol Compliance Testing

### WalletConnect Protocol Compliance

**Test Areas:**
1. **Message Format Compliance:**
   - JSON-RPC 2.0 compliance
   - WalletConnect message format
   - Session proposal format
   - Session request format

2. **Crypto Compliance:**
   - Encryption algorithm compliance
   - Key format compliance
   - Signature format compliance

3. **WebSocket Compliance:**
   - Connection protocol
   - Message framing
   - Reconnection protocol

### Compliance Tools

1. **Protocol Validators:**
   - Message format validators
   - Crypto validators
   - Protocol validators

2. **Test Suites:**
   - Official WalletConnect test suite (if available)
   - Custom compliance tests

### Interoperability Testing

**Test with:**
1. **JavaScript Implementation:**
   - Test Python ↔ JavaScript communication
   - Verify compatibility

2. **Other Implementations:**
   - Test with other WalletConnect implementations
   - Verify protocol compliance

## Test Data Management

### Test Fixtures

- Reusable test data
- Test configurations
- Mock data

### Test Isolation

- Each test should be independent
- Clean up after tests
- Use fixtures for setup/teardown

### Test Environment

- Isolated test environment
- Test relay server
- Test project IDs
- Test credentials

## Continuous Integration

### CI Pipeline

1. **Linting:**
   - `black` for formatting
   - `flake8` or `ruff` for linting
   - `mypy` for type checking

2. **Testing:**
   - Run all tests
   - Generate coverage report
   - Check coverage thresholds

3. **Integration:**
   - Run integration tests
   - Test protocol compatibility

### CI Configuration

**GitHub Actions example:**
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -e ".[dev]"
      - run: pytest --cov=walletkit
      - run: mypy walletkit
```

## TODO

- [ ] Set up pytest configuration
- [ ] Port first test file
- [ ] Create test fixtures
- [ ] Set up CI pipeline
- [ ] Create integration test framework
- [ ] Set up protocol compliance testing
- [ ] Document test patterns
- [ ] Create test data management
- [ ] Set up coverage reporting

