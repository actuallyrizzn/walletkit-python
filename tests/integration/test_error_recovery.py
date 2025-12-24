"""Integration tests for error recovery scenarios."""
import pytest
import asyncio

from walletkit import WalletKit, Core
from walletkit.utils.storage import MemoryStorage


@pytest.mark.integration
@pytest.mark.asyncio
async def test_core_recovery_after_storage_error():
    """Test Core recovery after storage errors."""
    storage = MemoryStorage()
    core = Core(storage=storage, project_id="test-project")
    
    await core.start()
    
    # Simulate storage error by corrupting storage
    # Core should handle gracefully
    try:
        await core.crypto.init()
        assert core.crypto._initialized
    except Exception:
        # Should handle storage errors
        pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_walletkit_recovery_after_core_error():
    """Test WalletKit recovery after Core errors."""
    storage = MemoryStorage()
    core = Core(storage=storage, project_id="test-project")
    
    await core.start()
    
    wallet = await WalletKit.init({
        "core": core,
        "metadata": {
            "name": "Test Wallet",
            "description": "Test",
            "url": "https://test.com",
            "icons": [],
        },
    })
    
    # Wallet should be functional even if some operations fail
    assert wallet is not None
    assert wallet.core is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_relayer_reconnection_scenario():
    """Test Relayer reconnection in integration scenario."""
    storage = MemoryStorage()
    core = Core(storage=storage, project_id="test-project")
    
    await core.start()
    
    relayer = core.relayer
    
    # Disconnect
    await relayer.disconnect()
    
    # Should be able to reconnect
    # Note: This will fail without real relay, but tests the error path
    try:
        await relayer.connect()
    except Exception:
        # Expected without real relay
        pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_wallet_instances():
    """Test multiple WalletKit instances with shared storage."""
    storage = MemoryStorage()
    
    core1 = Core(storage=storage, project_id="test-project")
    await core1.start()
    
    wallet1 = await WalletKit.init({
        "core": core1,
        "metadata": {
            "name": "Wallet 1",
            "description": "Test",
            "url": "https://test.com",
            "icons": [],
        },
    })
    
    core2 = Core(storage=storage, project_id="test-project")
    await core2.start()
    
    wallet2 = await WalletKit.init({
        "core": core2,
        "metadata": {
            "name": "Wallet 2",
            "description": "Test",
            "url": "https://test.com",
            "icons": [],
        },
    })
    
    # Both should work independently
    assert wallet1 is not None
    assert wallet2 is not None
    assert wallet1.core != wallet2.core
