# WalletKit Python

Python port of the WalletKit SDK for WalletConnect Protocol.

## Status

✅ **Phase 0, 1 & 2 Complete** - Core Implementation Done

### Completed

**Phase 0: Foundation**
- ✅ Virtual environment setup
- ✅ Project structure
- ✅ Testing suite configuration
- ✅ EventEmitter implementation (async support)
- ✅ Storage abstraction (FileStorage, MemoryStorage)
- ✅ JSON-RPC utilities

**Phase 1: Core Controllers**
- ✅ Type definitions (IWalletKit, IWalletKitEngine)
- ✅ Crypto utilities (X25519, ChaCha20-Poly1305, HKDF)
- ✅ KeyChain implementation
- ✅ Crypto controller (encryption/decryption, key management)
- ✅ URI parsing and formatting utilities
- ✅ Relayer controller (WebSocket communication)
- ✅ Pairing controller (URI handling, pairing management)
- ✅ Core class (orchestrates all controllers)

**Phase 2: Client API**
- ✅ SignClient stub (placeholder for full implementation)
- ✅ Engine controller (SignClient wrapper)
- ✅ WalletKit client (main API with full method surface)
- ✅ Event forwarding and handling
- ✅ Unit tests (40+ tests passing)

### Next Steps

- Full SignClient implementation (currently using stub)
- Integration tests with real WalletConnect relay
- Documentation and usage examples
- Performance optimization

## Quick Start

### Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=walletkit

# Run specific test file
pytest tests/unit/test_events.py
```

## Project Structure

```
walletkit-python/
├── src/
│   └── walletkit/          # Main package
│       ├── utils/          # ✅ Utilities (events, storage, jsonrpc, crypto, uri)
│       ├── controllers/    # ✅ Controllers (crypto, keychain, relayer, pairing)
│       ├── types/          # ✅ Type definitions
│       ├── constants/      # ✅ Constants
│       └── core.py         # ✅ Core implementation
├── tests/                  # ✅ Test suite
│   ├── unit/              # Unit tests
│   └── integration/        # Integration tests (to be implemented)
├── docs/                   # ✅ Documentation
├── js/                     # Original JavaScript source
└── tmp/                    # Reference implementations
```

## Test Results

```
40 tests passing ✅
Coverage: 64% (expected - many components have placeholder implementations)
```

## Architecture

The port follows the same architecture as the JavaScript implementation:

1. **Core**: Orchestrates all controllers (Crypto, Relayer, Pairing)
2. **Crypto**: Handles encryption/decryption, key management
3. **Relayer**: Manages WebSocket communication with relay server
4. **Pairing**: Handles pairing creation and management
5. **SignClient**: Stub implementation (placeholder for full port)
6. **Engine**: Wraps SignClient for protocol interactions
7. **WalletKit Client**: Main API for wallet integration

## Usage Example

```python
from walletkit import WalletKit, Core
from walletkit.utils.storage import MemoryStorage

# Initialize Core
storage = MemoryStorage()
core = Core(storage=storage)
await core.start()

# Initialize WalletKit
client = await WalletKit.init({
    "core": core,
    "metadata": {
        "name": "My Wallet",
        "description": "My Wallet Description",
        "url": "https://mywallet.com",
        "icons": ["https://mywallet.com/icon.png"],
    },
})

# Pair with a URI
await client.pair("wc:...")

# Listen for session proposals
@client.on("session_proposal")
async def on_proposal(event):
    # Handle proposal
    pass

# Approve session
session = await client.approve_session(
    id=event["id"],
    namespaces={...},
)
```

## Documentation

See `docs/` folder for comprehensive documentation:
- [Project Plan](docs/project-plan.md) - Complete project plan
- [Research Findings](docs/research-findings.md) - Research and analysis
- [Architecture Analysis](docs/architecture-analysis.md) - Codebase structure

## License

Apache 2.0
