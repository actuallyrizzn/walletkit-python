"""SignClient stub implementation.

Note: This is a minimal implementation that will be replaced with a full
SignClient port from @walletconnect/sign-client in the future.
"""
from typing import Any, Dict, Optional

from walletkit.utils.events import EventEmitter


class SignClient:
    """SignClient stub - minimal implementation for Engine wrapper."""

    def __init__(
        self,
        core: Any,  # ICore
        metadata: Dict[str, Any],
        sign_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize SignClient.
        
        Args:
            core: Core instance
            metadata: Wallet metadata
            sign_config: Optional sign configuration
        """
        self.core = core
        self.metadata = metadata
        self.sign_config = sign_config
        self.events = EventEmitter()
        
        # Placeholder stores
        self.session: Dict[str, Any] = {}  # Will be replaced with proper Store
        self.proposal: Dict[int, Any] = {}  # Will be replaced with proper Store
        
        self._initialized = False

    @classmethod
    async def init(
        cls,
        core: Any,
        metadata: Dict[str, Any],
        sign_config: Optional[Dict[str, Any]] = None,
    ) -> "SignClient":
        """Initialize SignClient.
        
        Args:
            core: Core instance
            metadata: Wallet metadata
            sign_config: Optional sign configuration
            
        Returns:
            Initialized SignClient instance
        """
        client = cls(core, metadata, sign_config)
        await client._init()
        return client

    async def _init(self) -> None:
        """Internal initialization."""
        if not self._initialized:
            # Initialize event client if available
            if hasattr(self.core, "event_client") and self.core.event_client:
                try:
                    await self.core.event_client.init()
                except Exception as e:
                    # Log warning but don't fail
                    if hasattr(self.core, "logger"):
                        self.core.logger.warn(str(e))
            self._initialized = True

    async def approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Approve session proposal.
        
        Args:
            params: Approval parameters
            
        Returns:
            Dict with 'topic' and 'acknowledged' callback
        """
        # Placeholder implementation
        topic = params.get("topic", "placeholder_topic")
        
        async def acknowledged() -> None:
            """Acknowledgment callback."""
            pass
        
        return {"topic": topic, "acknowledged": acknowledged}

    async def reject(self, params: Dict[str, Any]) -> None:
        """Reject session proposal.
        
        Args:
            params: Rejection parameters
        """
        # Placeholder implementation
        pass

    async def update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update session.
        
        Args:
            params: Update parameters
            
        Returns:
            Dict with 'acknowledged' callback
        """
        async def acknowledged() -> None:
            """Acknowledgment callback."""
            pass
        
        return {"acknowledged": acknowledged}

    async def extend(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extend session.
        
        Args:
            params: Extend parameters
            
        Returns:
            Dict with 'acknowledged' callback
        """
        async def acknowledged() -> None:
            """Acknowledgment callback."""
            pass
        
        return {"acknowledged": acknowledged}

    async def respond(self, params: Dict[str, Any]) -> None:
        """Respond to session request.
        
        Args:
            params: Response parameters
        """
        # Placeholder implementation
        pass

    async def disconnect(self, params: Dict[str, Any]) -> None:
        """Disconnect session.
        
        Args:
            params: Disconnect parameters
        """
        # Placeholder implementation
        pass

    async def emit(self, params: Dict[str, Any]) -> None:
        """Emit session event.
        
        Args:
            params: Emit parameters
        """
        # Placeholder implementation
        pass

    def get_pending_session_requests(self) -> list[Dict[str, Any]]:
        """Get pending session requests.
        
        Returns:
            List of pending requests
        """
        # Placeholder implementation
        return []

    async def approve_session_authenticate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Approve session authentication.
        
        Args:
            params: Approval parameters
            
        Returns:
            Dict with session
        """
        # Placeholder implementation
        return {"session": None}

    async def reject_session_authenticate(self, params: Dict[str, Any]) -> None:
        """Reject session authentication.
        
        Args:
            params: Rejection parameters
        """
        # Placeholder implementation
        pass

    def format_auth_message(self, params: Dict[str, Any]) -> str:
        """Format auth message.
        
        Args:
            params: Format parameters
            
        Returns:
            Formatted message
        """
        # Placeholder implementation
        return "placeholder_auth_message"

