"""Example integration test for Venice.ai Web3 login.

This is a template/example test file showing how to set up integration tests
for connecting to venice.ai's web3 login using WalletConnect.

NOTE: This is a template - you'll need to adapt it based on:
1. How venice.ai actually implements WalletConnect on their page
2. The exact DOM selectors and flow
3. Your specific testing requirements

To run this test:
1. Install dependencies: pip install -r requirements-dev.txt
2. Install Playwright browsers: playwright install chromium
3. Set WALLETCONNECT_PROJECT_ID environment variable
4. Run: pytest tests/integration/test_venice_ai_example.py -v
"""
import os
import pytest
import asyncio
from typing import Optional
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    pytest.skip("playwright not installed", allow_module_level=True)

from walletkit import WalletKit, Core
from walletkit.types.client import Metadata
from walletkit.utils.storage import MemoryStorage
from walletkit.utils.ethereum_signing import (
    sign_personal_message,
    get_address_from_private_key,
    generate_test_account,
)


# Test configuration
# WalletConnect Cloud project id (must be set in env for live integration tests)
TEST_PROJECT_ID = os.getenv("WALLETCONNECT_PROJECT_ID", "test-project-id")
VENICE_URL = "https://venice.ai"

# Hard time limit for the full browser flow so it can't hang in CI/dev runs.
VENICE_TEST_TIMEOUT_S = float(os.getenv("VENICE_TEST_TIMEOUT_S", "120"))
VENICE_ARTIFACTS_DIR = Path(os.getenv("VENICE_ARTIFACTS_DIR", "test-artifacts/venice"))
VENICE_SIGN_IN_URL = os.getenv("VENICE_SIGN_IN_URL", f"{VENICE_URL}/sign-in")


@pytest.fixture
def ethereum_account():
    """Create a test Ethereum account for signing.
    
    In production, you would load a real private key from secure storage.
    For testing, we generate a new account each time.
    """
    return generate_test_account()


@pytest.fixture
async def wallet(ethereum_account, project_id):
    """Create a WalletKit instance for wallet.
    
    This wallet can:
    - Connect via WalletConnect (handled by WalletKit)
    - Sign Ethereum messages (handled by eth-account)
    """
    # Note: Using test project ID - may need real one for actual connection
    
    storage = MemoryStorage()
    core = Core(
        project_id=project_id,
        storage=storage,
    )
    await core.start()
    
    metadata: Metadata = {
        "name": "Test Wallet for Venice.ai",
        "description": "Test wallet for Venice.ai integration",
        "url": "https://test.wallet",
        "icons": [],
    }
    
    wallet_instance = await WalletKit.init({
        "core": core,
        "metadata": metadata,
    })
    
    # Store the Ethereum account in the wallet instance for use in handlers
    wallet_instance._ethereum_account = ethereum_account
    
    yield wallet_instance
    
    # Cleanup
    if hasattr(core, "relayer") and core.relayer:
        try:
            await core.relayer.disconnect()
        except Exception:
            pass
    # Stop background tasks (prevents "Task was destroyed but it is pending!" warnings)
    if hasattr(core, "expirer") and core.expirer:
        try:
            await core.expirer.cleanup()
        except Exception:
            pass


async def extract_walletconnect_uri(page: Page, timeout: float = 30.0) -> Optional[str]:
    """Extract WalletConnect URI from venice.ai page.
    
    Tries multiple methods to extract the WalletConnect URI:
    1. Check JavaScript variables in page context
    2. Check DOM for URI in data attributes or input fields
    3. Extract from QR code image (if present)
    4. Monitor network requests for WalletConnect bridge calls
    
    Args:
        page: Playwright page object
        timeout: Maximum time to wait for URI
        
    Returns:
        WalletConnect URI string or None
    """
    from PIL import Image
    import io
    try:
        from pyzbar.pyzbar import decode as decode_qr
        HAS_PYZBAR = True
    except ImportError:
        HAS_PYZBAR = False
    
    # Method 1: Execute JavaScript to find URI in page context
    try:
        uri = await page.evaluate("""
            () => {
                // Check window object for WalletConnect URI
                if (window.walletConnectURI) return window.walletConnectURI;
                
                // Check for WalletConnect v2 client
                if (window.WalletConnect && window.WalletConnect.uri) {
                    return window.WalletConnect.uri;
                }
                
                // Check for @walletconnect/modal
                if (window.WalletConnectModal && window.WalletConnectModal.uri) {
                    return window.WalletConnectModal.uri;
                }
                
                // Check for common WalletConnect library instances
                const wcInstances = [
                    window.walletConnect,
                    window.wc,
                    window.WC,
                    window.__WALLETCONNECT__,
                ];
                for (const instance of wcInstances) {
                    if (instance && instance.uri) return instance.uri;
                }
                
                // Search DOM for URI in data attributes
                const uriElements = document.querySelectorAll(
                    '[data-uri], [data-wc-uri], [data-walletconnect-uri], input[value^="wc:"]'
                );
                for (const el of uriElements) {
                    const uri = el.getAttribute('data-uri') || 
                               el.getAttribute('data-wc-uri') || 
                               el.getAttribute('data-walletconnect-uri') ||
                               el.value;
                    if (uri && uri.startsWith('wc:')) return uri;
                }
                
                // Search for URI in text content
                const textContent = document.body.innerText || document.body.textContent || '';
                const wcUriMatch = textContent.match(/wc:[a-zA-Z0-9]+@\\d+\\?[^\\s"']+/);
                if (wcUriMatch) return wcUriMatch[0];
                
                return null;
            }
        """)
        if uri and uri.startswith("wc:"):
            return uri
    except Exception as e:
        print(f"JavaScript extraction failed: {e}")
    
    # Method 2: Check DOM for URI in input fields or data attributes
    try:
        uri_element = await page.wait_for_selector(
            '[data-wc-uri], [data-uri], [data-walletconnect-uri], input[value^="wc:"]',
            timeout=timeout * 1000,
            state="attached"
        )
        if uri_element:
            uri = (await uri_element.get_attribute("value") or 
                   await uri_element.get_attribute("data-uri") or
                   await uri_element.get_attribute("data-wc-uri") or
                   await uri_element.get_attribute("data-walletconnect-uri"))
            if uri and uri.startswith("wc:"):
                return uri
    except Exception:
        pass
    
    # Method 3: Extract from QR code image
    try:
        # Find QR code image
        qr_selectors = [
            'canvas',
            'img[alt*="QR"]',
            'img[alt*="qr"]',
            '[class*="qr"]',
            '[class*="QR"]',
            '[id*="qr"]',
            '[id*="QR"]',
        ]
        
        for selector in qr_selectors:
            try:
                qr_element = await page.wait_for_selector(selector, timeout=2000, state="visible")
                if qr_element:
                    # Take screenshot of QR code
                    screenshot = await qr_element.screenshot()
                    
                    if HAS_PYZBAR:
                        # Try to decode with pyzbar
                        image = Image.open(io.BytesIO(screenshot))
                        decoded = decode_qr(image)
                        if decoded:
                            uri = decoded[0].data.decode('utf-8')
                            if uri.startswith("wc:"):
                                return uri
                    else:
                        # Fallback: try qrcode library (for generating, not reading)
                        # This won't work for reading, but we can try other methods
                        pass
            except Exception:
                continue
    except Exception as e:
        print(f"QR code extraction failed: {e}")
    
    # Method 4: Monitor network requests for WalletConnect bridge calls
    try:
        uris_found = []
        
        def handle_request(request):
            url = request.url
            # Check if it's a WalletConnect bridge URL
            if "walletconnect" in url.lower() or "relay.walletconnect.com" in url:
                # Try to extract URI from request
                post_data = request.post_data
                if post_data and "wc:" in post_data:
                    import re
                    match = re.search(r'wc:[a-zA-Z0-9]+@\d+\?[^\s"\'}]+', post_data)
                    if match:
                        uris_found.append(match.group(0))
        
        page.on("request", handle_request)
        
        # Wait a bit for requests
        await asyncio.sleep(2)
        
        if uris_found:
            return uris_found[0]
    except Exception as e:
        print(f"Network monitoring failed: {e}")
    
    return None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_venice_ai_login_flow(wallet):
    """Test the complete Venice.ai web3 login flow.
    
    This test:
    1. Opens venice.ai in a browser
    2. Clicks login
    3. Extracts WalletConnect URI
    4. Pairs wallet with URI
    5. Handles session proposal
    6. Verifies connection
    """
    session_established = asyncio.Event()
    session_topic: Optional[str] = None

    # Get the Ethereum account for this wallet
    ethereum_account = wallet._ethereum_account
    wallet_address = ethereum_account["address"]

    # Windows consoles commonly default to cp1252, which can't print many emoji characters.
    print(f"\n[WALLET] Wallet Address: {wallet_address}")
    print("   (This is the address that will be used for signing)")

    async def on_session_proposal(event: dict) -> None:
        """Handle session proposal from venice.ai."""
        nonlocal session_topic
        proposal_id = event.get("id")
        params = event.get("params", {})

        print("\n[PROPOSAL] Session Proposal from Venice.ai:")
        print(f"   Proposal ID: {proposal_id}")

        proposer = params.get("proposer", {})
        proposer_metadata = proposer.get("metadata", {})
        print(f"   DApp: {proposer_metadata.get('name', 'Unknown')}")

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

            print(f"   Approving with address: {wallet_address}")
            result = await wallet.approve_session(
                id=proposal_id,
                namespaces=namespaces,
            )
            session_topic = result.get("topic")
            print(f"   [OK] Session approved! Topic: {session_topic}")
            session_established.set()
        except Exception as e:
            print(f"   [ERROR] Error approving session: {e}")
            import traceback
            traceback.print_exc()
            session_established.set()

    async def on_session_request(event: dict) -> None:
        """Handle signing requests from venice.ai."""
        print("\n[REQUEST] Signing Request from Venice.ai:")
        topic = event.get("topic")
        request_id = event.get("id")
        print(f"   Topic: {topic}")
        print(f"   Request ID: {request_id}")

        params = event.get("params", {})
        request = params.get("request", {})
        method = request.get("method", "unknown")
        request_params = request.get("params", [])
        print(f"   Method: {method}")

        # Get the Ethereum account from wallet instance
        ethereum_account = wallet._ethereum_account
        private_key = ethereum_account["private_key"]
        address = ethereum_account["address"]

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

                print(f"   Message to sign: {message[:50]}...")
                print(f"   Requested address: {requested_address}")
                print(f"   Our address: {address}")

                if requested_address.lower() != address.lower():
                    print("   [WARN] Address mismatch, but signing anyway for test")

                signature = sign_personal_message(private_key, message)
                print(f"   [OK] Signature created: {signature[:20]}...")

                await wallet.respond_session_request(
                    topic=topic,
                    response={
                        "id": request_id,
                        "jsonrpc": "2.0",
                        "result": signature,
                    },
                )
            elif method == "eth_sign":
                print("   [WARN] eth_sign not fully implemented - use personal_sign instead")
                await wallet.respond_session_request(
                    topic=topic,
                    response={
                        "id": request_id,
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32601,
                            "message": "eth_sign not supported, use personal_sign",
                        },
                    },
                )
            else:
                print(f"   [WARN] Unknown method: {method}")
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
            print(f"   [ERROR] Error handling request: {e}")
            import traceback
            traceback.print_exc()
            await wallet.respond_session_request(
                topic=topic,
                response={
                    "id": request_id,
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": str(e)},
                },
            )

    # WalletKit `.on()` API expects (event, listener)
    wallet.on("session_proposal", on_session_proposal)
    wallet.on("session_request", on_session_request)

    async def run_browser_flow() -> None:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Set to True for CI/automated runs
                slow_mo=1000,  # Slow down for debugging (remove in production)
            )
            try:
                context = await browser.new_context()
                # Required for reading the WalletConnect URI via "Copy link"
                await context.grant_permissions(["clipboard-read", "clipboard-write"])
                page = await context.new_page()

                print(f"\n[NAV] Navigating to {VENICE_SIGN_IN_URL}...")
                await page.goto(VENICE_SIGN_IN_URL, wait_until="domcontentloaded", timeout=90000)

                # Venice shows Web3 login as an icon button with aria-label="Web3 Wallet"
                print("[SEARCH] Clicking Web3 Wallet...")
                await page.click("button[aria-label='Web3 Wallet']", timeout=15000)

                print("[WAIT] Waiting for Connect Wallet modal...")
                await page.wait_for_selector("text=Connect Wallet", timeout=15000)

                print("[SEARCH] Selecting WalletConnect...")
                await page.click("button:has-text('WalletConnect')", timeout=15000)

                print("[WAIT] Waiting for WalletConnect QR view...")
                try:
                    # Copy link text varies slightly; use a case-insensitive text regex.
                    await page.wait_for_selector("text=/copy link/i", timeout=60000)
                except Exception:
                    # Persist artifacts so we can tune selectors quickly.
                    try:
                        VENICE_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
                        screenshot_path = VENICE_ARTIFACTS_DIR / "venice_wc_qr_view_missing.png"
                        html_path = VENICE_ARTIFACTS_DIR / "venice_wc_qr_view_missing.html"
                        await page.screenshot(path=str(screenshot_path), full_page=True)
                        html_path.write_text(await page.content(), encoding="utf-8", errors="ignore")
                        print(f"[DEBUG] Saved screenshot: {screenshot_path}")
                        print(f"[DEBUG] Saved html: {html_path}")
                        print(f"[DEBUG] URL: {page.url}")
                        try:
                            print(f"[DEBUG] Frames: {[f.url for f in page.frames]}")
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"[DEBUG] Failed to save artifacts: {e}")
                    raise

                print("[EXTRACT] Copying WalletConnect link to clipboard...")
                await page.click("text=/copy link/i", timeout=15000)
                uri = await page.evaluate("() => navigator.clipboard.readText()")
                if not uri:
                    pytest.fail("Could not extract WalletConnect URI from venice.ai page")
                if not isinstance(uri, str) or not uri.startswith("wc:"):
                    pytest.fail(f"Clipboard did not contain a WalletConnect URI. Got: {uri!r}")
                print(f"[OK] Found URI: {uri[:50]}...")

                print("[PAIR] Pairing wallet with URI...")
                await wallet.pair(uri)

                print("[WAIT] Waiting for session establishment...")
                try:
                    await asyncio.wait_for(session_established.wait(), timeout=30.0)
                except asyncio.TimeoutError:
                    pytest.fail("Session establishment timeout")

                assert session_topic is not None, "Session topic should be set"
                print(f"[OK] Session established with topic: {session_topic}")
                await asyncio.sleep(2)
            finally:
                await browser.close()

    # Hard upper bound for the full test (prevents hangs).
    await asyncio.wait_for(run_browser_flow(), timeout=VENICE_TEST_TIMEOUT_S)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_venice_ai_api_key_generation():
    """Test Venice.ai API key generation flow.
    
    This test demonstrates the API flow for generating a web3 API key.
    Note: This requires actual wallet signing, which you'll need to implement.
    """
    import aiohttp
    
    # Step 1: Get validation token
    async with aiohttp.ClientSession() as session:
        print("\n[API] Requesting validation token from Venice.ai...")
        async with session.get(
            "https://api.venice.ai/api/v1/api_keys/generate_web3_key"
        ) as resp:
            if resp.status != 200:
                pytest.skip(f"Venice.ai API returned {resp.status} - may need authentication")
            
            data = await resp.json()
            token = data.get("token")
            
            if not token:
                pytest.skip("No token returned from Venice.ai API")
            
            print(f"[OK] Received token: {token[:20]}...")
            
            # Step 2: Sign token with wallet
            # This requires your wallet implementation
            # signed_token = await wallet.sign_message(token)
            # wallet_address = wallet.get_address()
            
            # Step 3: Generate API key
            # async with session.post(
            #     "https://api.venice.ai/api/v1/api_keys/generate_web3_key",
            #     json={
            #         "description": "Test API Key",
            #         "apiKeyType": "INFERENCE",
            #         "signature": signed_token,
            #         "token": token,
            #         "address": wallet_address,
            #         "consumptionLimit": {"diem": 1}
            #     }
            # ) as resp:
            #     api_key_data = await resp.json()
            #     assert "apiKey" in api_key_data
            
            print("[WARN] Token signing and API key generation not implemented in example")


if __name__ == "__main__":
    # Run with: python -m pytest tests/integration/test_venice_ai_example.py -v -s
    pytest.main([__file__, "-v", "-s"])

