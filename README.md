# WalletKit Python

Python port of the WalletKit SDK for WalletConnect Protocol.

## Status

🚧 **In Development** - Phase 1 Complete, Phase 2 In Progress

### Completed (Phase 0 & 1)

- ✅ Virtual environment setup
- ✅ Project structure
- ✅ Testing suite configuration
- ✅ EventEmitter implementation (async support)
- ✅ Storage abstraction (FileStorage, MemoryStorage)
- ✅ JSON-RPC utilities
- ✅ Type definitions (IWalletKit, IWalletKitEngine)
- ✅ Crypto utilities (X25519, ChaCha20-Poly1305, HKDF)
- ✅ KeyChain implementation
- ✅ Crypto controller (encryption/decryption, key management)
- ✅ URI parsing and formatting utilities
- ✅ Relayer controller (WebSocket communication)
- ✅ Pairing controller (URI handling, pairing management)
- ✅ Core class (orchestrates all controllers)
- ✅ Unit tests (23+ tests passing)

### In Progress (Phase 2)

- 🔄 Engine controller (SignClient wrapper)
- 🔄 WalletKit client (main API)

### Next Steps

- Complete Engine controller implementation
- Implement WalletKit client with full API surface
- Integration tests
- Documentation and examples

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
23+ tests passing
Coverage: ~36% (expected - many components not yet fully tested)
```

## Architecture

The port follows the same architecture as the JavaScript implementation:

1. **Core**: Orchestrates all controllers (Crypto, Relayer, Pairing)
2. **Crypto**: Handles encryption/decryption, key management
3. **Relayer**: Manages WebSocket communication with relay server
4. **Pairing**: Handles pairing creation and management
5. **Engine**: (In progress) Wraps SignClient for protocol interactions
6. **Client**: (In progress) Main API for wallet integration

## Documentation

See `docs/` folder for comprehensive documentation:
- [Project Plan](docs/project-plan.md) - Complete project plan
- [Research Findings](docs/research-findings.md) - Research and analysis
- [Architecture Analysis](docs/architecture-analysis.md) - Codebase structure

## License

Apache 2.0
