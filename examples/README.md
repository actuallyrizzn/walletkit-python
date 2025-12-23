# WalletKit Python Examples

This directory contains runnable examples demonstrating how to use the WalletKit Python SDK.

## Examples

### 1. Basic Wallet (`basic_wallet.py`)

A minimal wallet implementation that:
- Initializes WalletKit
- Handles pairing requests
- Approves/rejects session proposals
- Responds to signing requests

**Usage:**
```bash
python examples/basic_wallet.py
```

### 2. DApp Simulator (`dapp_simulator.py`)

A simple dApp that:
- Creates a pairing URI
- Initiates session proposals
- Sends signing requests
- Handles responses

**Usage:**
```bash
python examples/dapp_simulator.py
```

### 3. Full Flow (`full_flow.py`)

A complete example showing:
- Wallet initialization
- DApp connection
- Session approval
- Transaction signing
- Session management

**Usage:**
```bash
python examples/full_flow.py
```

## Prerequisites

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

2. Get a WalletConnect Project ID:
   - Sign up at https://cloud.walletconnect.com
   - Create a project
   - Copy your Project ID

3. Set environment variable (optional):
```bash
export WALLETCONNECT_PROJECT_ID="your-project-id"
```

Or pass it directly in the examples.

## Running Examples

All examples can be run directly:

```bash
# Basic wallet
python examples/basic_wallet.py

# DApp simulator
python examples/dapp_simulator.py

# Full flow (requires two terminals)
# Terminal 1: Wallet
python examples/full_flow.py wallet

# Terminal 2: DApp
python examples/full_flow.py dapp
```

