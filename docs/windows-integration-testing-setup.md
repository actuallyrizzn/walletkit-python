# Windows Integration Testing Setup for Venice.ai Web3 Login

This guide covers what you need to install on Windows to perform live integration tests connecting your WalletConnect library to venice.ai's web3 login.

## Overview

Venice.ai uses WalletConnect for web3 authentication. The flow involves:
1. Venice.ai displays a WalletConnect QR code/URI
2. User connects their wallet via WalletConnect
3. Venice.ai provides a token to sign
4. User signs the token with their wallet
5. Venice.ai generates an API key

For automated testing, you'll need tools to:
- Automate browser interactions with venice.ai
- Extract WalletConnect URIs from the page
- Handle QR codes (optional, if you can extract URIs directly)
- Make API calls to Venice.ai's endpoints
- Programmatically handle wallet operations

## Required Installations

### 1. Python Dependencies

Install these additional packages for browser automation and QR code handling:

```powershell
# Activate your virtual environment first
.\venv\Scripts\Activate.ps1

# Install browser automation and QR code libraries
pip install playwright>=1.40.0
pip install qrcode[pil]>=7.4.2
pip install pillow>=10.0.0
pip install pyzbar>=0.1.9  # Optional: for reading QR codes from images
```

**Note:** After installing Playwright, you need to install browser binaries:

```powershell
playwright install chromium
```

### 2. System Dependencies

#### Playwright Browser Binaries
Playwright will download Chromium automatically when you run `playwright install`, but you may need:

- **Windows Visual C++ Redistributables** (usually already installed on Windows 11)
- **Internet connection** for first-time browser download

#### QR Code Reading (Optional)
If you want to read QR codes from screenshots:

- **ZBar** (for pyzbar): Download from https://github.com/mchehab/zbar/releases
  - Extract and add to PATH, or
  - Use the Windows installer version

**Alternative:** You can extract WalletConnect URIs directly from the page DOM/JavaScript, which is more reliable than QR code reading.

### 3. Optional: Wallet Simulator/Test Wallet

For automated testing, you have a few options:

#### Option A: Use Your WalletKit Library as the Wallet
Your library can act as the wallet side - you already have this capability in your examples.

#### Option B: Use a Test Wallet
- **MetaMask Test Wallet**: Set up a test account
- **WalletConnect Test Wallet**: Use WalletConnect's test wallet

#### Option C: Mock Wallet Operations
For testing, you can mock wallet signing operations if you just need to test the connection flow.

## Installation Commands Summary

Run these commands in PowerShell (as Administrator if needed):

```powershell
# 1. Ensure you're in your project directory
cd C:\projects\walletkit-python

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. Install Python packages
pip install playwright>=1.40.0
pip install qrcode[pil]>=7.4.2
pip install pillow>=10.0.0

# 4. Install Playwright browsers
playwright install chromium

# 5. Verify installation
python -c "import playwright; print('Playwright installed successfully')"
python -c "import qrcode; print('QRCode installed successfully')"
```

## Testing Setup

### Environment Variables

Make sure you have:

```powershell
# Set WalletConnect Project ID
$env:WALLETCONNECT_PROJECT_ID = "your-project-id-here"

# Optional: Venice.ai API endpoint (if different from default)
$env:VENICE_API_URL = "https://api.venice.ai"
```

### Basic Test Structure

Here's a basic structure for a venice.ai integration test:

```python
import asyncio
import pytest
from playwright.async_api import async_playwright
from walletkit import WalletKit, Core
from walletkit.utils.storage import MemoryStorage

@pytest.mark.integration
@pytest.mark.asyncio
async def test_venice_ai_web3_login():
    """Test connecting to venice.ai's web3 login."""
    # 1. Initialize your wallet
    storage = MemoryStorage()
    core = Core(
        project_id=os.getenv("WALLETCONNECT_PROJECT_ID"),
        storage=storage,
    )
    await core.start()
    
    wallet = await WalletKit.init({
        "core": core,
        "metadata": {
            "name": "Test Wallet",
            "description": "Test wallet for venice.ai",
            "url": "https://test.wallet",
            "icons": [],
        },
    })
    
    # 2. Launch browser and navigate to venice.ai
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Set to True for CI
        page = await browser.new_page()
        
        # Navigate to venice.ai login
        await page.goto("https://venice.ai")
        
        # 3. Click login button
        await page.click("text=Login / Sign Up")
        
        # 4. Wait for WalletConnect modal/QR code
        # Extract URI from page (check DOM or JavaScript)
        # This will vary based on how venice.ai implements it
        
        # 5. Pair wallet with extracted URI
        # uri = await extract_walletconnect_uri(page)
        # await wallet.pair(uri)
        
        # 6. Handle session proposal
        # ... (your existing session handling code)
        
        # 7. Handle signing requests from venice.ai
        # ... (sign the token venice.ai provides)
        
        await browser.close()
```

## Venice.ai API Integration

Based on research, venice.ai's web3 login flow:

1. **Get validation token:**
   ```python
   import aiohttp
   
   async with aiohttp.ClientSession() as session:
       async with session.get("https://api.venice.ai/api/v1/api_keys/generate_web3_key") as resp:
           data = await resp.json()
           token = data["token"]  # Token to sign
   ```

2. **Sign token with wallet** (using your WalletKit)

3. **Generate API key:**
   ```python
   async with session.post(
       "https://api.venice.ai/api/v1/api_keys/generate_web3_key",
       json={
           "description": "Web3 API Key",
           "apiKeyType": "INFERENCE",
           "signature": signed_token,
           "token": token,
           "address": wallet_address,
           "consumptionLimit": {"diem": 1}
       }
   ) as resp:
       api_key_data = await resp.json()
   ```

## Troubleshooting

### Playwright Issues

**Problem:** `playwright install` fails
**Solution:** 
- Check internet connection
- Run PowerShell as Administrator
- Try: `python -m playwright install chromium`

**Problem:** Browser won't launch
**Solution:**
- Ensure Chromium is installed: `playwright install chromium`
- Check Windows Defender isn't blocking it

### QR Code Issues

**Problem:** Can't read QR codes
**Solution:**
- Extract URI directly from page DOM/JavaScript instead
- Check venice.ai's page source for WalletConnect URI
- Use browser DevTools to monitor network requests for WalletConnect URIs

### WalletConnect Connection Issues

**Problem:** Can't connect to WalletConnect relay
**Solution:**
- Verify `WALLETCONNECT_PROJECT_ID` is set correctly
- Check firewall isn't blocking WebSocket connections
- Test with a simple pairing first (use your existing examples)

## Next Steps

1. **Create integration test file:**
   - `tests/integration/test_venice_ai_login.py`

2. **Update requirements-dev.txt:**
   ```txt
   playwright>=1.40.0
   qrcode[pil]>=7.4.2
   pillow>=10.0.0
   ```

3. **Test the setup:**
   - Run a simple Playwright test to verify browser automation works
   - Test WalletConnect pairing with your existing examples
   - Then combine both for venice.ai testing

## Additional Resources

- [Playwright Python Documentation](https://playwright.dev/python/)
- [Venice.ai API Documentation](https://docs.venice.ai)
- [WalletConnect Protocol Documentation](https://docs.walletconnect.com/)

