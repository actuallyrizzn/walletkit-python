"""Notifications utility for decrypting messages and getting session metadata."""
from typing import Any, Dict, Optional

from walletkit.controllers.session_store import SessionStore
from walletkit.core import Core
from walletkit.utils.storage import IKeyValueStorage


async def decrypt_message(
    topic: str,
    encrypted_message: str,
    storage: Optional[IKeyValueStorage] = None,
    storage_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Decrypt an encrypted message for a topic.
    
    Args:
        topic: Session topic
        encrypted_message: Encrypted message string
        storage: Optional storage backend
        storage_options: Optional storage options
        
    Returns:
        Decrypted JSON-RPC payload
    """
    # Create a temporary Core instance for decryption
    core = Core(
        storage=storage,
        storage_prefix=storage_options.get("prefix", "wc@2:core:") if storage_options else "wc@2:core:",
    )
    
    try:
        # Initialize crypto
        await core.crypto.init()
        
        # Decode the message
        decoded = await core.crypto.decode(topic, encrypted_message)
        
        return decoded
    finally:
        # Cleanup
        core = None


async def get_metadata(
    topic: str,
    storage: Optional[IKeyValueStorage] = None,
    storage_options: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Get session metadata for a topic.
    
    Args:
        topic: Session topic
        storage: Optional storage backend
        storage_options: Optional storage options
        
    Returns:
        Session metadata or None if not found
    """
    # Create a temporary Core instance
    storage_prefix = storage_options.get("prefix", "wc@2:core:") if storage_options else "wc@2:core:"
    core = Core(
        storage=storage,
        storage_prefix=storage_prefix,
    )
    
    try:
        # Initialize session store
        session_store = SessionStore(core.storage, core.logger, storage_prefix)
        await session_store.init()
        
        # Get session
        try:
            session = session_store.get(topic)
            if session and isinstance(session, dict):
                peer = session.get("peer", {})
                if isinstance(peer, dict):
                    return peer.get("metadata")
        except KeyError:
            # Session not found
            return None
        
        return None
    finally:
        # Cleanup
        core = None
        session_store = None


class Notifications:
    """Notifications utility class."""
    
    @staticmethod
    async def decrypt_message(
        topic: str,
        encrypted_message: str,
        storage: Optional[IKeyValueStorage] = None,
        storage_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Decrypt an encrypted message for a topic.
        
        Args:
            topic: Session topic
            encrypted_message: Encrypted message string
            storage: Optional storage backend
            storage_options: Optional storage options
            
        Returns:
            Decrypted JSON-RPC payload
        """
        return await decrypt_message(topic, encrypted_message, storage, storage_options)
    
    @staticmethod
    async def get_metadata(
        topic: str,
        storage: Optional[IKeyValueStorage] = None,
        storage_options: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get session metadata for a topic.
        
        Args:
            topic: Session topic
            storage: Optional storage backend
            storage_options: Optional storage options
            
        Returns:
            Session metadata or None if not found
        """
        return await get_metadata(topic, storage, storage_options)

