# WalletKit Python Usage Guide

Comprehensive usage guide with examples and best practices.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Wallet Integration](#wallet-integration)
4. [DApp Integration](#dapp-integration)
5. [Session Management](#session-management)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.8 or higher (3.10+ recommended)
- pip

### Install from Source

```bash
# Clone repository
git clone <repository-url>
cd walletkit-python

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Install package
pip install -e .
```

## Quick Start

### Minimal Wallet Example

```python
import asyncio
from walletkit import WalletKit, Core
from walletkit.utils.storage import MemoryStorage

async def main():
    # Initialize Core
    storage = MemoryStorage()
    core = Core(
        project_id="your-project-id",
        storage=storage,
    )
    await core.start()
    
    # Initialize WalletKit
    wallet = await WalletKit.init({
        "core": core,
        "metadata": {
            "name": "My Wallet",
            "description": "My Wallet Description",
            "url": "https://mywallet.com",
            "icons": ["https://mywallet.com/icon.png"],
        },
    })
    
    # Handle session proposals
    @wallet.on("session_proposal")
    async def on_proposal(event):
        proposal_id = event.get("id")
        params = event.get("params", {})
        
        # Show proposal to user
        print(f"New session proposal from: {params.get('proposer', {}).get('metadata', {}).get('name')}")
        
        # Approve with namespaces
        result = await wallet.approve_session(
            id=proposal_id,
            namespaces={
                "eip155": {
                    "chains": ["eip155:1"],
                    "methods": ["eth_sendTransaction", "eth_sign", "personal_sign"],
                    "events": ["chainChanged", "accountsChanged"],
                },
            },
        )
        print(f"Session approved: {result.get('topic')}")
    
    # Handle requests
    @wallet.on("session_request")
    async def on_request(event):
        topic = event.get("topic")
        request_id = event.get("id")
        params = event.get("params", {})
        request = params.get("request", {})
        
        method = request.get("method")
        print(f"Request: {method}")
        
        # Process request based on method
        if method == "eth_sendTransaction":
            # Show transaction to user, get approval
            # Then respond
            await wallet.respond_session_request(
                topic=topic,
                response={
                    "id": request_id,
                    "jsonrpc": "2.0",
                    "result": "0x...",  # Transaction hash
                },
            )
        elif method == "personal_sign":
            # Handle signing
            pass
    
    # Pair with URI from dApp
    uri = input("Enter WalletConnect URI: ")
    await wallet.pair(uri)
    
    # Keep running
    print("Wallet running... Press Ctrl+C to stop")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        await core.relayer.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Wallet Integration

### Complete Wallet Implementation

```python
import asyncio
import logging
from walletkit import WalletKit, Core
from walletkit.utils.storage import FileStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyWallet:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.core = None
        self.wallet = None
        
    async def initialize(self):
        """Initialize wallet."""
        # Use file storage for persistence
        storage = FileStorage(data_dir="./wallet_data")
        
        self.core = Core(
            project_id=self.project_id,
            storage=storage,
        )
        await self.core.start()
        
        self.wallet = await WalletKit.init({
            "core": self.core,
            "metadata": {
                "name": "My Wallet",
                "description": "A WalletConnect-enabled wallet",
                "url": "https://mywallet.com",
                "icons": ["https://mywallet.com/icon.png"],
            },
        })
        
        # Register event handlers
        self._register_handlers()
        
    def _register_handlers(self):
        """Register event handlers."""
        @self.wallet.on("session_proposal")
        async def on_proposal(event):
            await self.handle_proposal(event)
        
        @self.wallet.on("session_request")
        async def on_request(event):
            await self.handle_request(event)
        
        @self.wallet.on("session_delete")
        async def on_delete(event):
            logger.info(f"Session deleted: {event.get('topic')}")
    
    async def handle_proposal(self, event):
        """Handle session proposal."""
        proposal_id = event.get("id")
        params = event.get("params", {})
        proposer = params.get("proposer", {})
        
        logger.info(f"Session proposal from: {proposer.get('metadata', {}).get('name')}")
        
        # Show to user and get approval
        # For demo, auto-approve
        try:
            result = await self.wallet.approve_session(
                id=proposal_id,
                namespaces={
                    "eip155": {
                        "chains": ["eip155:1"],
                        "methods": ["eth_sendTransaction", "eth_sign", "personal_sign"],
                        "events": ["chainChanged", "accountsChanged"],
                    },
                },
            )
            logger.info(f"Session approved: {result.get('topic')}")
        except Exception as e:
            logger.error(f"Failed to approve session: {e}")
    
    async def handle_request(self, event):
        """Handle session request."""
        topic = event.get("topic")
        request_id = event.get("id")
        params = event.get("params", {})
        request = params.get("request", {})
        
        method = request.get("method")
        logger.info(f"Request: {method} from {topic}")
        
        try:
            if method == "eth_sendTransaction":
                # Process transaction
                result = await self.process_transaction(request)
                await self.wallet.respond_session_request(
                    topic=topic,
                    response={
                        "id": request_id,
                        "jsonrpc": "2.0",
                        "result": result,
                    },
                )
            elif method == "personal_sign":
                # Process signing
                result = await self.process_signature(request)
                await self.wallet.respond_session_request(
                    topic=topic,
                    response={
                        "id": request_id,
                        "jsonrpc": "2.0",
                        "result": result,
                    },
                )
        except Exception as e:
            logger.error(f"Failed to handle request: {e}")
            await self.wallet.respond_session_request(
                topic=topic,
                response={
                    "id": request_id,
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": str(e),
                    },
                },
            )
    
    async def process_transaction(self, request):
        """Process transaction request."""
        # Implement transaction processing
        # Return transaction hash
        return "0x..."
    
    async def process_signature(self, request):
        """Process signature request."""
        # Implement signature processing
        # Return signature
        return "0x..."
    
    async def pair(self, uri: str):
        """Pair with dApp URI."""
        try:
            await self.wallet.pair(uri)
            logger.info("Paired successfully")
        except Exception as e:
            logger.error(f"Pairing failed: {e}")
    
    async def shutdown(self):
        """Shutdown wallet."""
        if self.core and self.core.relayer:
            await self.core.relayer.disconnect()
        logger.info("Wallet shut down")

# Usage
async def main():
    wallet = MyWallet(project_id="your-project-id")
    await wallet.initialize()
    
    # Get URI from user
    uri = input("Enter WalletConnect URI: ")
    await wallet.pair(uri)
    
    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        await wallet.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## DApp Integration

### Complete DApp Implementation

```python
import asyncio
import logging
from walletkit import WalletKit, Core
from walletkit.utils.storage import MemoryStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MyDApp:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.core = None
        self.dapp = None
        self.session_topic = None
        
    async def initialize(self):
        """Initialize dApp."""
        storage = MemoryStorage()
        
        self.core = Core(
            project_id=self.project_id,
            storage=storage,
        )
        await self.core.start()
        
        self.dapp = await WalletKit.init({
            "core": self.core,
            "metadata": {
                "name": "My DApp",
                "description": "A WalletConnect-enabled dApp",
                "url": "https://mydapp.com",
                "icons": ["https://mydapp.com/icon.png"],
            },
        })
        
        # Register event handlers
        self._register_handlers()
        
    def _register_handlers(self):
        """Register event handlers."""
        @self.dapp.on("session_approve")
        async def on_approve(event):
            session = event.get("session")
            self.session_topic = session.get("topic")
            logger.info(f"Session approved: {self.session_topic}")
        
        @self.dapp.on("session_reject")
        async def on_reject(event):
            logger.warning("Session rejected")
        
        @self.dapp.on("session_delete")
        async def on_delete(event):
            logger.info("Session deleted")
            self.session_topic = None
    
    async def create_pairing(self):
        """Create pairing URI."""
        pairing = await self.dapp.core.pairing.create({
            "methods": ["wc_sessionPropose"],
        })
        uri = pairing.get("uri")
        logger.info(f"Pairing URI: {uri}")
        return uri
    
    async def send_transaction(self, to: str, value: str):
        """Send transaction request."""
        if not self.session_topic:
            raise RuntimeError("No active session")
        
        try:
            result = await self.dapp.engine.request({
                "topic": self.session_topic,
                "chainId": "eip155:1",
                "request": {
                    "method": "eth_sendTransaction",
                    "params": {
                        "from": "0x...",  # User's address
                        "to": to,
                        "value": value,
                        "gas": "0x5208",
                    },
                },
            })
            logger.info(f"Transaction result: {result}")
            return result
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            raise
    
    async def sign_message(self, message: str):
        """Sign message request."""
        if not self.session_topic:
            raise RuntimeError("No active session")
        
        try:
            result = await self.dapp.engine.request({
                "topic": self.session_topic,
                "chainId": "eip155:1",
                "request": {
                    "method": "personal_sign",
                    "params": [message, "0x..."],  # Message and address
                },
            })
            logger.info(f"Signature result: {result}")
            return result
        except Exception as e:
            logger.error(f"Signing failed: {e}")
            raise

# Usage
async def main():
    dapp = MyDApp(project_id="your-project-id")
    await dapp.initialize()
    
    # Create pairing URI
    uri = await dapp.create_pairing()
    print(f"\nShare this URI with wallet:\n{uri}\n")
    
    # Wait for session approval
    print("Waiting for wallet to connect...")
    while not dapp.session_topic:
        await asyncio.sleep(1)
    
    # Send transaction
    try:
        result = await dapp.send_transaction(
            to="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            value="0x2386f26fc10000",  # 0.01 ETH
        )
        print(f"Transaction sent: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Session Management

### Getting Active Sessions

```python
sessions = wallet.get_active_sessions()
for topic, session in sessions.items():
    print(f"Topic: {topic}")
    print(f"Expiry: {session.get('expiry')}")
    print(f"Peer: {session.get('peer', {}).get('metadata', {}).get('name')}")
```

### Updating Sessions

```python
await wallet.update_session(
    topic="session_topic",
    namespaces={
        "eip155": {
            "chains": ["eip155:1", "eip155:137"],  # Added Polygon
            "methods": ["eth_sendTransaction", "eth_sign"],
            "events": ["chainChanged", "accountsChanged"],
        },
    },
)
```

### Extending Sessions

```python
await wallet.extend_session(topic="session_topic")
```

### Disconnecting Sessions

```python
await wallet.disconnect_session(
    topic="session_topic",
    reason={
        "code": 6000,
        "message": "User disconnected",
    },
)
```

## Error Handling

### Common Patterns

```python
# Pairing with retry
async def pair_with_retry(wallet, uri, max_retries=3):
    for attempt in range(max_retries):
        try:
            await wallet.pair(uri)
            return
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Pairing attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(1)

# Request with timeout
async def request_with_timeout(dapp, request, timeout=30):
    try:
        result = await asyncio.wait_for(
            dapp.engine.request(request),
            timeout=timeout,
        )
        return result
    except asyncio.TimeoutError:
        raise TimeoutError("Request timed out")
```

## Best Practices

1. **Always use persistent storage for wallets:**
   ```python
   storage = FileStorage(data_dir="./wallet_data")
   ```

2. **Handle all events:**
   ```python
   @wallet.on("session_proposal")
   @wallet.on("session_request")
   @wallet.on("session_delete")
   # ... handle all events
   ```

3. **Validate user input:**
   ```python
   if not uri.startswith("wc:"):
       raise ValueError("Invalid WalletConnect URI")
   ```

4. **Log important events:**
   ```python
   logger.info(f"Session approved: {topic}")
   logger.error(f"Request failed: {error}")
   ```

5. **Clean up on shutdown:**
   ```python
   await core.relayer.disconnect()
   ```

## Troubleshooting

### Connection Issues

- Check project ID is correct
- Verify network connectivity
- Check relay URL is accessible

### Session Issues

- Verify session hasn't expired
- Check namespaces are compatible
- Ensure topic is valid

### Request Issues

- Verify session is active
- Check method is supported
- Validate request parameters

## License

This documentation is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License (CC-BY-SA-4.0). See [LICENSE-DOCS](../LICENSE-DOCS) for details.
