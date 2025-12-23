"""Ethereum message signing utilities for WalletConnect.

This module provides functions to sign Ethereum messages (personal_sign, eth_sign)
using private keys. This is separate from WalletConnect's protocol encryption.
"""
from typing import Optional
from eth_account import Account
from eth_account.messages import encode_defunct


def sign_personal_message(private_key: str, message: str) -> str:
    """Sign a message using Ethereum personal_sign format.
    
    This is what venice.ai and other dApps use for authentication.
    
    Args:
        private_key: Ethereum private key (hex string, with or without 0x prefix)
        message: Message to sign (string)
        
    Returns:
        Signature as hex string (0x-prefixed)
        
    Example:
        >>> private_key = "0x" + "0" * 64  # Test key
        >>> signature = sign_personal_message(private_key, "Hello Venice.ai")
        >>> assert signature.startswith("0x")
    """
    # Remove 0x prefix if present
    if private_key.startswith("0x"):
        private_key = private_key[2:]
    
    # Create account from private key
    account = Account.from_key(private_key)
    
    # Encode message in Ethereum format (adds prefix)
    message_encoded = encode_defunct(text=message)
    
    # Sign the message
    signed_message = account.sign_message(message_encoded)
    
    # Return signature as hex string
    return signed_message.signature.hex()


def get_address_from_private_key(private_key: str) -> str:
    """Get Ethereum address from private key.
    
    Args:
        private_key: Ethereum private key (hex string, with or without 0x prefix)
        
    Returns:
        Ethereum address (0x-prefixed)
    """
    # Remove 0x prefix if present
    if private_key.startswith("0x"):
        private_key = private_key[2:]
    
    # Create account from private key
    account = Account.from_key(private_key)
    
    # Return checksummed address
    return account.address


def generate_test_account() -> dict:
    """Generate a test Ethereum account for testing.
    
    WARNING: This is for testing only. Never use in production.
    
    Returns:
        Dict with 'private_key' and 'address'
    """
    account = Account.create()
    return {
        "private_key": account.key.hex(),
        "address": account.address,
    }

