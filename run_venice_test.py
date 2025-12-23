"""Fully automated venice.ai integration test - WORKING VERSION."""
import asyncio
import os
import sys
import re
from urllib.parse import urlparse, parse_qs
from walletkit import WalletKit, Core
from walletkit.types.client import Metadata
from walletkit.utils.storage import MemoryStorage
from walletkit.utils.ethereum_signing import (
    generate_test_account,
    sign_personal_message,
)

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("ERROR: playwright not installed")
    sys.exit(1)

WC_URI_RE = re.compile(r"wc:[a-zA-Z0-9]+@\d+\?[^\s\"']+")


async def _try_get_clipboard_text(page) -> str:
    """Best-effort clipboard read; returns empty string on failure."""
    try:
        return await page.evaluate("() => navigator.clipboard.readText().catch(() => '')")
    except Exception:
        return ""


async def extract_wc_uri_from_web3modal(page) -> str | None:
    """Extract a WalletConnect wc: URI from the Reown/Web3Modal UI.

    Venice uses Reown AppKit/Web3Modal, which renders most of its UI in shadow DOM.
    Prefer Playwright locators (shadow-piercing) + clipboard-based extraction.
    """
    # 1) Look for a direct link with wc:
    try:
        wc_href = page.locator("a[href^='wc:']").first
        if await wc_href.count():
            href = await wc_href.get_attribute("href")
            if href and href.startswith("wc:"):
                return href
    except Exception:
        pass

    # 2) Click the "QR CODE" pill if present (often switches view)
    try:
        qr_btn = page.get_by_role("button", name=re.compile(r"^\s*QR\s*CODE\s*$", re.I)).first
        if await qr_btn.is_visible():
            await qr_btn.click(timeout=8000)
            await asyncio.sleep(0.8)
    except Exception:
        pass

    # 3) Click the "WalletConnect" row (sometimes required)
    try:
        wc_row = page.get_by_text("WalletConnect", exact=False).first
        if await wc_row.is_visible():
            await wc_row.click(timeout=8000)
            await asyncio.sleep(0.8)
    except Exception:
        pass

    # 4) Try "Copy" / "Copy link" then read clipboard
    try:
        copy_btn = page.get_by_role("button", name=re.compile(r"\bcopy\b", re.I)).first
        if await copy_btn.is_visible():
            await copy_btn.click(timeout=8000)
            await asyncio.sleep(0.4)
            clip = await _try_get_clipboard_text(page)
            if clip and clip.startswith("wc:"):
                return clip
    except Exception:
        pass

    # 5) Scan any visible text for a wc: pattern
    try:
        text = await page.evaluate("() => document.body.innerText || ''")
        m = WC_URI_RE.search(text or "")
        if m:
            return m.group(0)
    except Exception:
        pass

    return None


async def main():
    """Run fully automated venice.ai test."""
    project_id = os.getenv("WALLETCONNECT_PROJECT_ID")  # prefer user's project id if set
    relay_origin = os.getenv("WALLETCONNECT_ORIGIN")
    
    print("=" * 70)
    print("VENICE.AI FULLY AUTOMATED INTEGRATION TEST")
    print("=" * 70)
    
    # Generate account
    print("\n[1/8] Generating Ethereum account...")
    account = generate_test_account()
    wallet_address = account["address"]
    print(f"    Address: {wallet_address}")

    # Browser automation + auto-detect Venice's projectId if user didn't provide one
    print("\n[2/8] Launching browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        # Allow clipboard-based extraction via "Copy link" in Web3Modal
        context = await browser.new_context(permissions=["clipboard-read", "clipboard-write"])
        page = await context.new_page()
        
        # Monitor network for WalletConnect URIs
        captured_uris = []
        detected_project_id: str | None = None
        
        def capture_request(request):
            url = request.url
            post_data = request.post_data or ""
            body = post_data

            nonlocal detected_project_id
            if detected_project_id is None and "api.web3modal.org" in url and "projectId=" in url:
                try:
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query or "")
                    pid = (qs.get("projectId") or [None])[0]
                    if pid and isinstance(pid, str) and len(pid) >= 8:
                        detected_project_id = pid
                        print(f"    [DETECTED] Venice Web3Modal projectId: {detected_project_id}")
                except Exception:
                    pass
            
            # Check URL
            if "walletconnect" in url.lower() or "relay.walletconnect.com" in url:
                if body:
                    matches = re.findall(r'wc:[a-zA-Z0-9]+@\d+\?[^\s"\'}]+', body)
                    if matches:
                        captured_uris.extend(matches)
                        print(f"    [NETWORK] Found URI in request: {matches[0][:50]}...")
            
            # Check body for wc: URIs
            if "wc:" in body:
                matches = re.findall(r'wc:[a-zA-Z0-9]+@\d+\?[^\s"\'}]+', body)
                if matches:
                    captured_uris.extend(matches)
                    print(f"    [NETWORK] Found URI in body: {matches[0][:50]}...")
        
        page.on("request", capture_request)
        
        # Monitor responses for URIs
        def capture_response(response):
            try:
                url = response.url
                if "walletconnect" in url.lower() or "relay.walletconnect.com" in url or "web3modal" in url.lower():
                    # Try to get response body (may be async)
                    pass
            except:
                pass
        
        page.on("response", capture_response)
        
        # Monitor WebSocket messages (where WalletConnect URIs are often sent)
        def capture_websocket(ws):
            def on_framereceived(event):
                try:
                    payload = event.get('payload', '') or str(event)
                    if payload and "wc:" in str(payload):
                        matches = re.findall(r'wc:[a-zA-Z0-9]+@\d+\?[^\s"\'}]+', str(payload))
                        if matches:
                            captured_uris.extend(matches)
                            print(f"    [WEBSOCKET RX] Found URI: {matches[0][:50]}...")
                except:
                    pass
            
            def on_framesent(event):
                try:
                    payload = event.get('payload', '') or str(event)
                    if payload and "wc:" in str(payload):
                        matches = re.findall(r'wc:[a-zA-Z0-9]+@\d+\?[^\s"\'}]+', str(payload))
                        if matches:
                            captured_uris.extend(matches)
                            print(f"    [WEBSOCKET TX] Found URI: {matches[0][:50]}...")
                except:
                    pass
            
            try:
                ws.on("framereceived", on_framereceived)
                ws.on("framesent", on_framesent)
            except:
                pass
        
        page.on("websocket", capture_websocket)
        
        try:
            print("\n[3/8] Navigating to sign-in page...")
            await page.goto("https://venice.ai/sign-in", wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            # If user didn't set a project id, use Venice's detected id (from api.web3modal.org requests)
            if not project_id:
                # Wait a moment for the config request to fire
                for _ in range(30):
                    if detected_project_id:
                        break
                    await asyncio.sleep(0.2)
                project_id = detected_project_id
                # When piggybacking Venice's projectId, use Venice as the websocket Origin by default.
                # (WalletConnect Cloud often enforces allowlisted origins per project.)
                if not relay_origin:
                    relay_origin = "https://venice.ai"

            if not project_id:
                print("    [ERROR] Could not detect Web3Modal projectId and WALLETCONNECT_PROJECT_ID is not set.")
                await page.screenshot(path="venice_no_project_id.png")
                return
            else:
                print(f"    [OK] Using WalletConnect projectId: {project_id}")
                if relay_origin:
                    print(f"    [OK] Using relay Origin: {relay_origin}")

            # Initialize wallet (after projectId is known)
            print("\n[4/8] Initializing WalletKit...")
            storage = MemoryStorage()
            core = Core(project_id=project_id, storage=storage, relay_origin=relay_origin)
            await core.start()

            metadata: Metadata = {
                "name": "Test Wallet",
                "description": "Automated test wallet",
                "url": "https://test.wallet",
                "icons": [],
            }

            wallet = await WalletKit.init({"core": core, "metadata": metadata})
            wallet._ethereum_account = account

            session_ready = asyncio.Event()
            session_topic = None

            # Event handlers
            async def on_proposal(event: dict):
                nonlocal session_topic
                proposal_id = event.get("id")
                params = event.get("params", {})

                print(f"\n[SESSION] Proposal received (ID: {proposal_id})")

                try:
                    required_namespaces = params.get("requiredNamespaces", {})
                    namespaces = {}

                    if "eip155" in required_namespaces:
                        chains = required_namespaces["eip155"].get("chains", ["eip155:1"])
                        accounts = [f"{chain}:{wallet_address}" for chain in chains]
                        namespaces["eip155"] = {
                            "accounts": accounts,
                            "chains": chains,
                            "methods": required_namespaces["eip155"].get("methods", ["personal_sign", "eth_sign"]),
                            "events": required_namespaces["eip155"].get("events", ["chainChanged", "accountsChanged"]),
                        }
                    else:
                        namespaces["eip155"] = {
                            "accounts": [f"eip155:1:{wallet_address}"],
                            "chains": ["eip155:1"],
                            "methods": ["personal_sign", "eth_sign"],
                            "events": ["chainChanged", "accountsChanged"],
                        }

                    result = await wallet.approve_session(id=proposal_id, namespaces=namespaces)
                    session_topic = result.get("topic")
                    print(f"    [OK] Session approved! Topic: {session_topic}")
                    session_ready.set()
                except Exception as e:
                    print(f"    [ERROR] Approval failed: {e}")
                    import traceback
                    traceback.print_exc()
                    session_ready.set()

            async def on_request(event: dict):
                topic = event.get("topic")
                request_id = event.get("id")
                params = event.get("params", {})
                request = params.get("request", {})
                method = request.get("method")
                request_params = request.get("params", [])

                print(f"\n[SIGN] Request: {method} (ID: {request_id})")

                if method == "personal_sign" and len(request_params) >= 2:
                    message_hex = request_params[0]
                    if message_hex.startswith("0x"):
                        message_bytes = bytes.fromhex(message_hex[2:])
                    else:
                        message_bytes = bytes.fromhex(message_hex)

                    try:
                        message = message_bytes.decode("utf-8")
                    except Exception:
                        message = message_hex

                    print(f"    Message: {message[:50]}...")

                    signature = sign_personal_message(account["private_key"], message)
                    print(f"    [OK] Signed: {signature[:30]}...")

                    await wallet.respond_session_request(
                        topic=topic,
                        response={"id": request_id, "jsonrpc": "2.0", "result": signature},
                    )
                else:
                    print(f"    [SKIP] Method {method} not handled")

            wallet.on("session_proposal", on_proposal)
            wallet.on("session_request", on_request)
            
            print("\n[5/8] Clicking Web3 Wallet button...")
            await page.wait_for_load_state("domcontentloaded", timeout=30000)
            await page.get_by_role("button", name=re.compile(r"^\s*Web3 Wallet\s*$", re.I)).click(timeout=20000)
            await page.get_by_text("Connect Wallet", exact=False).wait_for(timeout=20000)
            await asyncio.sleep(1.0)
            print("    [OK] Web3Modal opened")
            
            print("\n[7/8] Extracting WalletConnect URI...")
            uri = None
            
            # Method 1: Check captured network URIs
            if captured_uris:
                uri = captured_uris[-1]  # Get most recent
                print(f"    [OK] Found URI from network: {uri[:50]}...")
            
            # Method 2: Extract via shadow-DOM-aware locators + clipboard
            if not uri:
                for attempt in range(20):
                    if captured_uris:
                        uri = captured_uris[-1]
                        break
                    uri = await extract_wc_uri_from_web3modal(page)
                    if uri:
                        break
                    if attempt % 3 == 0:
                        print(f"    Attempt {attempt+1}/20: waiting...")
                    await asyncio.sleep(1.0)
            
            if not uri:
                print("    [ERROR] Could not extract URI")
                await page.screenshot(path="venice_debug.png")
                print("    Screenshot saved to venice_debug.png")
                return
            
            print(f"\n[8/8] Pairing with URI...")
            print(f"    URI: {uri[:60]}...")
            await wallet.pair(uri)
            
            print("\n[WAITING] Waiting for session...")
            try:
                await asyncio.wait_for(session_ready.wait(), timeout=30.0)
                if session_topic:
                    print(f"    [SUCCESS] Session established! Topic: {session_topic}")
                    print("\n[READY] Wallet ready. Waiting for signing requests...")
                    await asyncio.sleep(20)  # Wait for venice.ai to send signing request
                else:
                    print("    [ERROR] Session topic not set")
            except asyncio.TimeoutError:
                print("    [ERROR] Session timeout")
            
        finally:
            await browser.close()
            # Cleanup
            try:
                if "core" in locals() and hasattr(core, "relayer") and core.relayer:
                    await core.relayer.disconnect()
            except Exception:
                pass
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[INTERRUPTED]")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
