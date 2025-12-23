# WalletKit Python

Python port of the WalletKit SDK for WalletConnect Protocol.

## Status

🚧 **In Development** - Phase 0 Complete

### Completed

- ✅ Virtual environment setup
- ✅ Project structure
- ✅ Testing suite configuration
- ✅ EventEmitter implementation (async support)
- ✅ Storage abstraction (FileStorage, MemoryStorage)
- ✅ JSON-RPC utilities
- ✅ Unit tests (14 tests passing)

### In Progress

- 🔄 Type definitions porting

### Next Steps

- Core controllers (Crypto, Relayer, Pairing)
- Sign Client wrapper
- Engine controller
- WalletKit client

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
│       ├── utils/          # Utilities (events, storage, jsonrpc)
│       ├── controllers/    # Controllers (to be implemented)
│       ├── types/          # Type definitions (to be implemented)
│       └── constants/      # Constants (to be implemented)
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   └── integration/        # Integration tests
├── docs/                   # Documentation
├── js/                     # Original JavaScript source
└── tmp/                    # Reference implementations
```

## Documentation

See `docs/` folder for comprehensive documentation:
- [Project Plan](docs/project-plan.md) - Complete project plan
- [Research Findings](docs/research-findings.md) - Research and analysis
- [Architecture Analysis](docs/architecture-analysis.md) - Codebase structure

## License

Apache 2.0

