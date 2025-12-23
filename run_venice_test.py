"""Standalone script to test venice.ai integration."""
import asyncio
import os
import sys
from walletkit import WalletKit, Core
from walletkit.types.client import Metadata
from walletkit.utils.storage import MemoryStorage
from walletkit.utils.ethereum_signing import (
    generate_test_account,
    sign_personal_message,
    get_address_from_private_key,
)

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright")
    sys.exit(1)


async def extract_walletconnect_uri(page, timeout=30.0):
    """Extract WalletConnect URI from page."""
    # Try JavaScript extraction
    try:
        uri = await page.evaluate("""
            () => {
                if (window.walletConnectURI) return window.walletConnectURI;
                if (window.WalletConnect && window.WalletConnect.uri) {
                    return window.WalletConnect.uri;
                }
                const uriElements = document.querySelectorAll('[data-uri], [data-wc-uri]');
                for (const el of uriElements) {
                    const uri = el.getAttribute('data-uri') || el.getAttribute('data-wc-uri');
                    if (uri && uri.startsWith('wc:')) return uri;
                }
                return null;
            }
        """)
        if uri and uri.startswith("wc:"):
            return uri
    except Exception as e:
        print(f"JavaScript extraction failed: {e}")
    
    return None


async def main():
    """Run venice.ai integration test."""
    # Get project ID
    project_id = os.getenv("WALLETCONNECT_PROJECT_ID", "a01e2f3b4c5d6e7f8a9b0c1d2e3f4a5b")
    
    print("=" * 60)
    print("VENICE.AI INTEGRATION TEST")
    print("=" * 60)
    
    # Generate test Ethereum account
    print("\n[1/6] Generating test Ethereum account...")
    ethereum_account = generate_test_account()
    wallet_address = ethereum_account["address"]
    print(f"    Address: {wallet_address}")
    print(f"    Private Key: {ethereum_account['private_key'][:20]}... (hidden)")
    
    # Initialize wallet
    print("\n[2/6] Initializing WalletKit...")
    storage = MemoryStorage()
    core = Core(project_id=project_id, storage=storage)
    await core.start()
    
    metadata: Metadata = {
        "name": "Test Wallet for Venice.ai",
        "description": "Test wallet for Venice.ai integration",
        "url": "https://test.wallet",
        "icons": [],
    }
    
    wallet = await WalletKit.init({
        "core": core,
        "metadata": metadata,
    })
    wallet._ethereum_account = ethereum_account
    
    session_established = asyncio.Event()
    session_topic = None
    
    # Set up event handlers
    async def on_session_proposal(event: dict) -> None:
        nonlocal session_topic
        proposal_id = event.get("id")
        params = event.get("params", {})
        
        print(f"\n[SESSION] Proposal received:")
        print(f"    Proposal ID: {proposal_id}")
        
        proposer = params.get("proposer", {})
        proposer_metadata = proposer.get("metadata", {})
        print(f"    DApp: {proposer_metadata.get('name', 'Unknown')}")
        
        try:
            required_namespaces = params.get("requiredNamespaces", {})
            namespaces = {}
            
            if "eip155" in required_namespaces:
                required_chains = required_namespaces["eip155"].get("chains", ["eip155:1"])
                accounts = [f"{chain}:{wallet_address}" for chain in required_chains]
                
                namespaces["eip155"] = {
                    "accounts": accounts,
                    "chains": required_chains,
                    "methods": required_namespaces["eip155"].get("methods", [
                        "eth_sendTransaction",
                        "eth_sign",
                        "personal_sign",
                    ]),
                    "events": required_namespaces["eip155"].get("events", [
                        "chainChanged",
                        "accountsChanged",
                    ]),
                }
            else:
                namespaces["eip155"] = {
                    "accounts": [f"eip155:1:{wallet_address}"],
                    "chains": ["eip155:1"],
                    "methods": ["eth_sendTransaction", "eth_sign", "personal_sign"],
                    "events": ["chainChanged", "accountsChanged"],
                }
            
            print(f"    Approving with address: {wallet_address}")
            result = await wallet.approve_session(
                id=proposal_id,
                namespaces=namespaces,
            )
            session_topic = result.get("topic")
            print(f"    [OK] Session approved! Topic: {session_topic}")
            session_established.set()
        except Exception as e:
            print(f"    [ERROR] Failed to approve: {e}")
            import traceback
            traceback.print_exc()
            session_established.set()
    
    wallet.on("session_proposal", on_session_proposal)
    
    async def on_session_request(event: dict) -> None:
        topic = event.get("topic")
        request_id = event.get("id")
        params = event.get("params", {})
        request = params.get("request", {})
        method = request.get("method", "unknown")
        request_params = request.get("params", [])
        
        print(f"\n[SIGN] Request received:")
        print(f"    Method: {method}")
        print(f"    Request ID: {request_id}")
        
        private_key = ethereum_account["private_key"]
        
        try:
            if method == "personal_sign":
                if len(request_params) < 2:
                    raise ValueError("personal_sign requires [message, address]")
                
                message_hex = request_params[0]
                requested_address = request_params[1]
                
                if message_hex.startswith("0x"):
                    message_bytes = bytes.fromhex(message_hex[2:])
                else:
                    message_bytes = bytes.fromhex(message_hex)
                
                try:
                    message = message_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    message = message_hex
                
                print(f"    Message: {message[:50]}...")
                print(f"    Requested address: {requested_address}")
                
                signature = sign_personal_message(private_key, message)
                print(f"    [OK] Signature created: {signature[:30]}...")
                
                await wallet.respond_session_request(
                    topic=topic,
                    response={
                        "id": request_id,
                        "jsonrpc": "2.0",
                        "result": signature,
                    },
                )
            else:
                print(f"    [SKIP] Method {method} not handled")
        except Exception as e:
            print(f"    [ERROR] Failed to handle request: {e}")
            import traceback
            traceback.print_exc()
    
    wallet.on("session_request", on_session_request)
    
    # Launch browser
    print("\n[3/6] Launching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        
        try:
            context = await browser.new_context()
            page = await context.new_page()
            
            print("\n[4/6] Navigating to venice.ai...")
            try:
                await page.goto("https://venice.ai", wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                print(f"    [WARNING] Navigation issue: {e}")
                print("    Continuing anyway...")
                await asyncio.sleep(2)
            
            print("\n[5/6] Looking for login button...")
            try:
                # Try multiple ways to find login
                login_clicked = False
                try:
                    await page.click("text=Login / Sign Up", timeout=3000)
                    login_clicked = True
                    print("    Clicked 'Login / Sign Up'")
                except:
                    try:
                        await page.click("a:has-text('Login')", timeout=3000)
                        login_clicked = True
                        print("    Clicked login link")
                    except:
                        try:
                            await page.click("button:has-text('Login')", timeout=3000)
                            login_clicked = True
                            print("    Clicked login button")
                        except:
                            print("    Could not find login button - page might already be on login")
                            login_clicked = True  # Assume we're there
                
                if login_clicked:
                    await asyncio.sleep(2)  # Wait for page to load
                    
                    # Take screenshot for debugging
                    await page.screenshot(path="venice_page.png")
                    print("    Screenshot saved to venice_page.png")
                    
                    # Try to find WalletConnect elements with longer timeout
                    print("    Looking for WalletConnect UI...")
                    try:
                        await page.wait_for_selector(
                            "canvas, img[alt*='QR'], [data-wc], .walletconnect-modal, [class*='wallet'], [class*='connect']",
                            timeout=15000,
                            state="attached"
                        )
                        print("    Found WalletConnect element!")
                    except:
                        print("    WalletConnect UI not found with standard selectors")
                        print("    Checking page content...")
                        page_text = await page.inner_text("body")
                        if "wallet" in page_text.lower() or "connect" in page_text.lower():
                            print("    Page contains wallet/connect text - might be loading")
                        else:
                            print("    Page might not have WalletConnect yet")
            except Exception as e:
                print(f"    [WARNING] Login flow issue: {e}")
                await page.screenshot(path="venice_error.png")
                print("    Error screenshot saved to venice_error.png")
            
            print("\n[6/6] Extracting WalletConnect URI...")
            print("    Trying multiple extraction methods...")
            
            # Try extraction immediately
            uri = await extract_walletconnect_uri(page, timeout=5.0)
            
            if not uri:
                print("    Waiting 5 seconds and trying again...")
                await asyncio.sleep(5)
                uri = await extract_walletconnect_uri(page, timeout=10.0)
            
            if not uri:
                print("    Waiting 10 more seconds (WalletConnect might be loading)...")
                await asyncio.sleep(10)
                uri = await extract_walletconnect_uri(page, timeout=10.0)
            
            if not uri:
                print("    [INFO] Could not automatically extract URI")
                print("    This is normal - venice.ai might:")
                print("    1. Require manual interaction")
                print("    2. Use a different WalletConnect implementation")
                print("    3. Load WalletConnect asynchronously")
                print("\n    Browser window is open - you can:")
                print("    1. Manually click through the login flow")
                print("    2. Look for a QR code or WalletConnect URI")
                print("    3. Copy any 'wc:' URI you see and we'll use it")
                print("\n    Waiting 60 seconds for manual interaction...")
                print("    (Or press Ctrl+C to stop)")
                await asyncio.sleep(60)
                
                # Try one more time after waiting
                uri = await extract_walletconnect_uri(page, timeout=5.0)
            
            if not uri:
                print("\n    [SKIP] URI extraction failed")
                print("    The test setup is working, but venice.ai's WalletConnect")
                print("    implementation may require manual interaction or different handling")
                return
            
            print(f"    [OK] Found URI: {uri[:50]}...")
            
            print("\n[PAIRING] Pairing wallet with URI...")
            await wallet.pair(uri)
            
            print("\n[WAITING] Waiting for session establishment...")
            try:
                await asyncio.wait_for(session_established.wait(), timeout=30.0)
            except asyncio.TimeoutError:
                print("    [ERROR] Session establishment timeout")
                return
            
            if session_topic:
                print(f"    [OK] Session established! Topic: {session_topic}")
                print("\n[READY] Wallet is ready. Waiting for signing requests...")
                await asyncio.sleep(10)  # Wait for any requests
            else:
                print("    [ERROR] Session topic not set")
            
        finally:
            print("\n[CLEANUP] Closing browser...")
            await browser.close()
    
    # Cleanup
    if hasattr(core, "relayer") and core.relayer:
        try:
            await core.relayer.disconnect()
        except Exception:
            pass
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Test stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

