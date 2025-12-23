#!/usr/bin/env python3
"""
DApp Simulator Example

A simple dApp demonstrating:
- Creating pairing URIs
- Initiating session proposals
- Sending signing requests
- Handling responses
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
    """Main dApp example."""
    # Get Project ID from environment or use placeholder
    project_id = os.getenv("WALLETCONNECT_PROJECT_ID", "your-project-id-here")
    
    if project_id == "your-project-id-here":
        print("⚠️  Warning: Using placeholder Project ID")
        print("   Set WALLETCONNECT_PROJECT_ID environment variable or update the code")
        print("   Get your Project ID at: https://cloud.walletconnect.com\n")
    
    # Define dApp metadata
    metadata: Metadata = {
        "name": "Python DApp Example",
        "description": "A simple dApp using WalletKit Python",
        "url": "https://example.com/dapp",
        "icons": ["https://example.com/dapp-icon.png"],
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
    print("🚀 Initializing WalletKit (DApp mode)...")
    dapp = await WalletKit.init({
        "core": core,
        "metadata": metadata,
    })
    
    # Register event handlers
    @dapp.on("session_proposal")
    async def on_session_proposal(event: dict) -> None:
        """Handle session proposal (as responder)."""
        print(f"\n📱 Session Proposal Response:")
        print(f"   Proposal ID: {event.get('id')}")
    
    @dapp.on("session_approve")
    async def on_session_approve(event: dict) -> None:
        """Handle session approval."""
        print(f"\n✅ Session Approved:")
        print(f"   Topic: {event.get('topic')}")
        print(f"   Session established!")
    
    @dapp.on("session_reject")
    async def on_session_reject(event: dict) -> None:
        """Handle session rejection."""
        print(f"\n❌ Session Rejected:")
        print(f"   Proposal ID: {event.get('id')}")
    
    @dapp.on("session_request")
    async def on_session_request(event: dict) -> None:
        """Handle session request response."""
        print(f"\n📝 Request Response:")
        print(f"   Topic: {event.get('topic')}")
        print(f"   Request ID: {event.get('id')}")
        
        response = event.get("params", {}).get("response", {})
        if "result" in response:
            print(f"   ✅ Result: {response.get('result')}")
        elif "error" in response:
            error = response.get("error", {})
            print(f"   ❌ Error: {error.get('message', 'Unknown error')}")
    
    @dapp.on("session_delete")
    async def on_session_delete(event: dict) -> None:
        """Handle session deletion."""
        print(f"\n🗑️  Session Deleted:")
        print(f"   Topic: {event.get('topic')}")
    
    # Start the dApp
    print("✅ WalletKit initialized!")
    print("\n📱 DApp is ready!")
    print("\nTo connect a wallet:")
    print("1. Call dapp.connect() to get a pairing URI")
    print("2. Share the URI with the wallet (QR code, deep link, etc.)")
    print("3. Wait for session approval")
    print("4. Send signing requests")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        # Example: Create a pairing URI
        print("🔗 Creating pairing URI...")
        pairing = await dapp.core.pairing.create({
            "methods": ["wc_sessionPropose"],
        })
        
        uri = pairing.get("uri")
        topic = pairing.get("topic")
        
        print(f"\n✅ Pairing created!")
        print(f"   Topic: {topic}")
        print(f"   URI: {uri}")
        print(f"\n📱 Share this URI with your wallet:")
        print(f"   {uri}")
        print(f"\n⏳ Waiting for wallet to pair and send session proposal...")
        print("   (In a real scenario, the wallet would pair and send a session proposal)")
        print("   (This example demonstrates the pairing creation only)")
        
        # Keep running to listen for events
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down dApp...")
        print("✅ DApp stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

