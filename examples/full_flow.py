#!/usr/bin/env python3
"""
Full Flow Example

Demonstrates a complete WalletConnect flow:
- Wallet initialization
- DApp pairing URI creation
- Session proposal and approval
- Request/response handling
"""
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from walletkit import WalletKit, Core
from walletkit.types.client import Metadata
from walletkit.utils.storage import MemoryStorage


async def wallet_mode(project_id: str):
    """Run in wallet mode."""
    print("=" * 60)
    print("WALLET MODE")
    print("=" * 60)
    
    metadata: Metadata = {
        "name": "Python Wallet Example",
        "description": "A wallet using WalletKit Python",
        "url": "https://example.com/wallet",
        "icons": ["https://example.com/wallet-icon.png"],
    }
    
    # Initialize
    storage = MemoryStorage()
    core = Core(project_id=project_id, storage=storage)
    await core.start()
    
    wallet = await WalletKit.init({
        "core": core,
        "metadata": metadata,
    })
    
    # Event handlers
    @wallet.on("session_proposal")
    async def on_proposal(event: dict) -> None:
        proposal_id = event.get("id")
        params = event.get("params", {})
        proposer = params.get("proposer", {})
        proposer_metadata = proposer.get("metadata", {})
        
        print(f"\n📱 Session Proposal from: {proposer_metadata.get('name', 'Unknown')}")
        print(f"   Proposal ID: {proposal_id}")
        
        # Auto-approve
        required_namespaces = params.get("requiredNamespaces", {})
        namespaces = {}
        for ns_name, ns_req in required_namespaces.items():
            namespaces[ns_name] = {
                "chains": ns_req.get("chains", []),
                "methods": ns_req.get("methods", []),
                "events": ns_req.get("events", []),
            }
        
        result = await wallet.approve_session(id=proposal_id, namespaces=namespaces)
        print(f"   ✅ Approved! Topic: {result.get('topic')}")
    
    @wallet.on("session_request")
    async def on_request(event: dict) -> None:
        topic = event.get("topic")
        request_id = event.get("id")
        params = event.get("params", {})
        request = params.get("request", {})
        method = request.get("method")
        
        print(f"\n📝 Request: {method}")
        print(f"   Topic: {topic}")
        
        # Auto-reject for demo
        await wallet.respond_session_request(
            topic=topic,
            response={
                "id": request_id,
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": "Demo mode - request not processed"},
            },
        )
    
    print("\n✅ Wallet ready! Waiting for connections...")
    print("   Share a pairing URI from a dApp to connect\n")
    
    await asyncio.Event().wait()


async def dapp_mode(project_id: str):
    """Run in dApp mode."""
    print("=" * 60)
    print("DAPP MODE")
    print("=" * 60)
    
    metadata: Metadata = {
        "name": "Python DApp Example",
        "description": "A dApp using WalletKit Python",
        "url": "https://example.com/dapp",
        "icons": ["https://example.com/dapp-icon.png"],
    }
    
    # Initialize
    storage = MemoryStorage()
    core = Core(project_id=project_id, storage=storage)
    await core.start()
    
    dapp = await WalletKit.init({
        "core": core,
        "metadata": metadata,
    })
    
    # Create pairing URI
    print("\n🔗 Creating pairing URI...")
    pairing = await dapp.core.pairing.create({
        "methods": ["wc_sessionPropose"],
    })
    
    uri = pairing.get("uri")
    print(f"\n✅ Pairing URI created:")
    print(f"   {uri}")
    print(f"\n📱 Share this URI with a wallet to connect")
    print(f"   (In a real scenario, you would display this as a QR code)")
    
    await asyncio.Event().wait()


async def main():
    """Main entry point."""
    project_id = os.getenv("WALLETCONNECT_PROJECT_ID", "your-project-id-here")
    
    if project_id == "your-project-id-here":
        print("⚠️  Warning: Using placeholder Project ID")
        print("   Set WALLETCONNECT_PROJECT_ID environment variable")
        print("   Get your Project ID at: https://cloud.walletconnect.com\n")
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "wallet"
    
    if mode == "wallet":
        await wallet_mode(project_id)
    elif mode == "dapp":
        await dapp_mode(project_id)
    else:
        print(f"Unknown mode: {mode}")
        print("Usage: python examples/full_flow.py [wallet|dapp]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

