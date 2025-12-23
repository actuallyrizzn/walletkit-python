#!/usr/bin/env python3
"""
Basic Wallet Example

A minimal wallet implementation demonstrating:
- WalletKit initialization
- Pairing request handling
- Session proposal approval/rejection
- Signing request handling
"""
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from walletkit import WalletKit, Core
from walletkit.types.client import Metadata, Options
from walletkit.utils.storage import MemoryStorage


async def main():
    """Main wallet example."""
    # Get Project ID from environment or use placeholder
    project_id = os.getenv("WALLETCONNECT_PROJECT_ID", "your-project-id-here")
    
    if project_id == "your-project-id-here":
        print("⚠️  Warning: Using placeholder Project ID")
        print("   Set WALLETCONNECT_PROJECT_ID environment variable or update the code")
        print("   Get your Project ID at: https://cloud.walletconnect.com\n")
    
    # Define wallet metadata
    metadata: Metadata = {
        "name": "Python Wallet Example",
        "description": "A basic wallet implementation using WalletKit Python",
        "url": "https://example.com",
        "icons": ["https://example.com/icon.png"],
    }
    
    # Initialize Core
    print("🚀 Initializing Core...")
    storage = MemoryStorage()
    core = Core(
        project_id=project_id,
        storage=storage,
    )
    await core.start()
    
    # Initialize WalletKit
    print("🚀 Initializing WalletKit...")
    wallet = await WalletKit.init({
        "core": core,
        "metadata": metadata,
    })
    
    # Register event handlers
    @wallet.on("session_proposal")
    async def on_session_proposal(event: dict) -> None:
        """Handle session proposal."""
        print(f"\n📱 Session Proposal Received:")
        proposal_id = event.get("id")
        print(f"   Proposal ID: {proposal_id}")
        
        params = event.get("params", {})
        proposer = params.get("proposer", {})
        proposer_metadata = proposer.get("metadata", {})
        print(f"   DApp: {proposer_metadata.get('name', 'Unknown')}")
        print(f"   URL: {proposer_metadata.get('url', 'Unknown')}")
        
        required_namespaces = params.get("requiredNamespaces", {})
        print(f"   Required Namespaces: {list(required_namespaces.keys())}")
        
        # Auto-approve for demo (in real wallet, show UI to user)
        print("\n✅ Auto-approving session (demo mode)...")
        try:
            # Get required namespaces from proposal or use defaults
            namespaces = {}
            if "eip155" in required_namespaces:
                namespaces["eip155"] = {
                    "chains": required_namespaces["eip155"].get("chains", ["eip155:1"]),
                    "methods": required_namespaces["eip155"].get("methods", ["eth_sendTransaction", "eth_sign", "personal_sign"]),
                    "events": required_namespaces["eip155"].get("events", ["chainChanged", "accountsChanged"]),
                }
            else:
                # Default namespace
                namespaces["eip155"] = {
                    "chains": ["eip155:1"],
                    "methods": ["eth_sendTransaction", "eth_sign", "personal_sign"],
                    "events": ["chainChanged", "accountsChanged"],
                }
            
            result = await wallet.approve_session(
                id=proposal_id,
                namespaces=namespaces,
            )
            print(f"   ✅ Session approved! Topic: {result.get('topic', 'N/A')}")
        except Exception as e:
            print(f"   ❌ Error approving session: {e}")
            import traceback
            traceback.print_exc()
    
    @wallet.on("session_request")
    async def on_session_request(event: dict) -> None:
        """Handle session request."""
        print(f"\n📝 Session Request Received:")
        topic = event.get("topic")
        request_id = event.get("id")
        print(f"   Topic: {topic}")
        print(f"   Request ID: {request_id}")
        
        params = event.get("params", {})
        request = params.get("request", {})
        method = request.get("method", "unknown")
        request_params = request.get("params", [])
        
        print(f"   Method: {method}")
        print(f"   Params: {request_params}")
        
        # Auto-respond for demo (in real wallet, show UI to user)
        print("\n✅ Auto-responding to request (demo mode)...")
        try:
            if method == "eth_sendTransaction":
                # In a real wallet, show transaction details to user
                print("   ⚠️  Transaction signing not implemented in demo")
                await wallet.respond_session_request(
                    topic=topic,
                    response={
                        "id": request_id,
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": "Transaction signing not implemented in demo",
                        },
                    },
                )
            elif method in ["eth_sign", "personal_sign"]:
                # In a real wallet, show message to user
                print("   ⚠️  Message signing not implemented in demo")
                await wallet.respond_session_request(
                    topic=topic,
                    response={
                        "id": request_id,
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32000,
                            "message": "Message signing not implemented in demo",
                        },
                    },
                )
            else:
                await wallet.respond_session_request(
                    topic=topic,
                    response={
                        "id": request_id,
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": f"Method not supported: {method}",
                        },
                    },
                )
        except Exception as e:
            print(f"   ❌ Error responding to request: {e}")
            import traceback
            traceback.print_exc()
    
    @wallet.on("session_delete")
    async def on_session_delete(event: dict) -> None:
        """Handle session deletion."""
        print(f"\n🗑️  Session Deleted:")
        print(f"   Topic: {event.get('topic')}")
    
    @wallet.on("session_event")
    async def on_session_event(event: dict) -> None:
        """Handle session events."""
        print(f"\n📢 Session Event:")
        print(f"   Topic: {event.get('topic')}")
        print(f"   Event: {event.get('params', {}).get('event', {})}")
    
    # Start the wallet
    print("✅ WalletKit initialized!")
    print("\n📱 Wallet is ready to receive connections...")
    print("   Share a WalletConnect URI to connect a dApp")
    print("   Press Ctrl+C to stop\n")
    
    try:
        # Keep running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down wallet...")
        # Cleanup would go here
        print("✅ Wallet stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

