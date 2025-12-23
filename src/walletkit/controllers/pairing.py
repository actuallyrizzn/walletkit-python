"""Pairing controller implementation."""
from typing import Any, Dict, Optional

from walletkit.constants.crypto import CRYPTO_CLIENT_SEED
from walletkit.utils.crypto_utils import generate_random_bytes32
from walletkit.utils.uri import format_uri, parse_uri


def calc_expiry(ttl_ms: int) -> int:
    """Calculate expiry timestamp.
    
    Args:
        ttl_ms: Time to live in milliseconds
        
    Returns:
        Expiry timestamp in milliseconds
    """
    import time
    return int(time.time() * 1000) + ttl_ms


class Pairing:
    """Pairing controller for managing pairings."""

    def __init__(
        self,
        core: Any,  # ICore
        logger: Any,  # Logger
    ) -> None:
        """Initialize Pairing controller.
        
        Args:
            core: Core instance
            logger: Logger instance
        """
        self.core = core
        self.logger = logger
        self.name = "pairing"
        self.version = "1.0"
        
        # Store pairings in memory (will be replaced with proper Store later)
        self.pairings: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def init(self) -> None:
        """Initialize pairing controller."""
        if not self._initialized:
            # TODO: Initialize store
            # await self.pairings.init()
            self._initialized = True
            self.logger.info("Pairing initialized")

    async def create(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new pairing.
        
        Args:
            params: Optional parameters (methods, transportType, etc.)
            
        Returns:
            Dict with 'topic' and 'uri'
        """
        self._check_initialized()
        
        if params is None:
            params = {}
        
        # Generate symmetric key and topic
        sym_key = generate_random_bytes32()
        topic = await self.core.crypto.set_sym_key(sym_key)
        
        # Calculate expiry (5 minutes default)
        FIVE_MINUTES = 5 * 60 * 1000
        expiry = calc_expiry(FIVE_MINUTES)
        
        # Create pairing
        relay = {"protocol": "irn"}
        pairing = {
            "topic": topic,
            "expiry": expiry,
            "relay": relay,
            "active": False,
            "methods": params.get("methods"),
        }
        
        # Format URI
        uri = format_uri({
            "protocol": self.core.protocol,
            "version": self.core.version,
            "topic": topic,
            "symKey": sym_key,
            "relay": relay,
            "expiryTimestamp": expiry,
            "methods": params.get("methods"),
        })
        
        # Store pairing
        self.pairings[topic] = pairing
        
        # Subscribe to topic
        await self.core.relayer.subscribe(topic, {
            "transportType": params.get("transportType"),
        })
        
        return {"topic": topic, "uri": uri}

    async def pair(self, params: Dict[str, Any]) -> None:
        """Pair with a URI.
        
        Args:
            params: Pairing parameters with 'uri' key
        """
        self._check_initialized()
        
        uri = params.get("uri")
        if not uri:
            raise ValueError("URI is required")
        
        # Parse URI
        parsed = parse_uri(uri)
        topic = parsed["topic"]
        sym_key = parsed["symKey"]
        relay = parsed["relay"]
        expiry_timestamp = parsed.get("expiryTimestamp")
        
        # Check if pairing already exists
        if topic in self.pairings:
            existing = self.pairings[topic]
            if existing.get("active"):
                raise ValueError(f"Pairing already exists: {topic}")
        
        # Set symmetric key
        await self.core.crypto.set_sym_key(sym_key, override_topic=topic)
        
        # Create pairing
        pairing = {
            "topic": topic,
            "expiry": expiry_timestamp or calc_expiry(5 * 60 * 1000),
            "relay": relay,
            "active": False,
            "methods": parsed.get("methods"),
        }
        
        self.pairings[topic] = pairing
        
        # Subscribe to topic
        await self.core.relayer.subscribe(topic)
        
        self.logger.info(f"Paired with topic: {topic}")

    def get(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get pairing by topic.
        
        Args:
            topic: Pairing topic
            
        Returns:
            Pairing dict or None
        """
        self._check_initialized()
        return self.pairings.get(topic)

    async def activate(self, topic: str) -> None:
        """Activate a pairing.
        
        Args:
            topic: Pairing topic
        """
        self._check_initialized()
        if topic not in self.pairings:
            raise ValueError(f"Pairing not found: {topic}")
        
        self.pairings[topic]["active"] = True

    async def delete(self, topic: str) -> None:
        """Delete a pairing.
        
        Args:
            topic: Pairing topic
        """
        self._check_initialized()
        if topic in self.pairings:
            # Unsubscribe from topic
            await self.core.relayer.unsubscribe(topic)
            del self.pairings[topic]

    def _check_initialized(self) -> None:
        """Check if pairing is initialized."""
        if not self._initialized:
            raise RuntimeError("Pairing not initialized. Call init() first.")

