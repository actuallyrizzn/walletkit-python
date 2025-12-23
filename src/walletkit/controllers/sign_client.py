"""SignClient implementation for WalletConnect Sign Protocol."""
import json
from typing import Any, Callable, Dict, Optional

from walletkit.controllers.expirer import EXPIRER_EVENTS, parse_expirer_target
from walletkit.controllers.proposal_store import ProposalStore
from walletkit.controllers.request_store import RequestStore
from walletkit.controllers.session_store import SessionStore
from walletkit.utils.events import EventEmitter
from walletkit.utils.jsonrpc import format_jsonrpc_error, format_jsonrpc_result


class SignClient:
    """SignClient for managing WalletConnect Sign Protocol sessions."""

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
        self.sign_config = sign_config or {}
        self.events = EventEmitter()
        
        # Initialize stores
        storage = core.storage
        logger = core.logger
        storage_prefix = getattr(core, "storage_prefix", "wc@2:core:")
        
        self.session = SessionStore(storage, logger, storage_prefix)
        self.proposal = ProposalStore(storage, logger, storage_prefix)
        self.request_store = RequestStore(storage, logger, storage_prefix)
        
        self._initialized = False
        self._pending_acknowledgments: Dict[str, Callable[[], Any]] = {}
        self._pending_auth_requests: Dict[int, Dict[str, Any]] = {}

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
            # Initialize stores
            await self.session.init()
            await self.proposal.init()
            await self.request_store.init()
            
            # Subscribe to relayer messages
            self._setup_relayer_listeners()
            
            # Register expirer events
            self._register_expirer_events()
            
            # Initialize event client if available
            if hasattr(self.core, "event_client") and self.core.event_client:
                try:
                    await self.core.event_client.init()
                except Exception as e:
                    if hasattr(self.core, "logger"):
                        self.core.logger.warn(str(e))
            
            self._initialized = True

    def _setup_relayer_listeners(self) -> None:
        """Set up relayer message listeners."""
        async def on_message(event: Dict[str, Any]) -> None:
            """Handle incoming relayer message."""
            topic = event.get("topic")
            message = event.get("message")
            
            if not topic or not message:
                return
            
            try:
                # Decode message
                payload = await self.core.crypto.decode(topic, message)
                
                # Handle based on method
                method = payload.get("method")
                if method:
                    await self._handle_protocol_message(topic, payload)
            except Exception as e:
                self.core.logger.error(f"Error handling relayer message: {e}")
        
        self.core.relayer.on("message", on_message)

    async def _handle_protocol_message(self, topic: str, payload: Dict[str, Any]) -> None:
        """Handle protocol message.
        
        Args:
            topic: Message topic
            payload: Decoded JSON-RPC payload
        """
        method = payload.get("method")
        params = payload.get("params", {})
        request_id = payload.get("id")
        
        if method == "wc_sessionPropose":
            await self._handle_session_propose(topic, params, request_id)
        elif method == "wc_sessionSettle":
            await self._handle_session_settle(topic, params, request_id)
        elif method == "wc_sessionRequest":
            await self._handle_session_request(topic, params, request_id)
        elif method == "wc_sessionUpdate":
            await self._handle_session_update(topic, params, request_id)
        elif method == "wc_sessionExtend":
            await self._handle_session_extend(topic, params, request_id)
        elif method == "wc_sessionDelete":
            await self._handle_session_delete(topic, params, request_id)
        elif method == "wc_sessionEvent":
            await self._handle_session_event(topic, params, request_id)
        elif method == "wc_sessionAuthenticate":
            await self._handle_session_authenticate(topic, params, request_id)

    async def _handle_session_propose(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session proposal.
        
        Args:
            topic: Proposal topic
            params: Proposal parameters
            request_id: Request ID
        """
        proposal_id = params.get("id") or request_id
        if not proposal_id:
            return
        
        proposal = {
            "id": proposal_id,
            "topic": topic,
            "params": params,
        }
        
        await self.proposal.set(proposal_id, proposal)
        
        # Register expiry with expirer (proposals expire in 5 minutes)
        import time
        proposal_expiry = int(time.time() * 1000) + (5 * 60 * 1000)
        self.core.expirer.set(proposal_id, proposal_expiry)
        
        # Emit event
        await self.events.emit("session_proposal", {
            "id": proposal_id,
            "topic": topic,
            "params": params,
        })

    async def _handle_session_settle(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session settlement (approval).
        
        Args:
            topic: Session topic
            params: Session parameters
            request_id: Request ID
        """
        session = params.get("session")
        if not session:
            return
        
        session["topic"] = topic
        await self.session.set(topic, session)
        
        # Register expiry with expirer
        expiry = session.get("expiry")
        if expiry:
            self.core.expirer.set(topic, expiry)
        
        # Acknowledge if pending
        if topic in self._pending_acknowledgments:
            ack = self._pending_acknowledgments.pop(topic)
            if ack:
                await ack()

    async def _handle_session_request(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session request.
        
        Args:
            topic: Session topic
            params: Request parameters
            request_id: Request ID
        """
        request = params.get("request")
        if not request:
            return
        
        # Store pending request
        await self.request_store.add({
            "topic": topic,
            "request": request,
        })
        
        # Emit event
        await self.events.emit("session_request", {
            "id": request.get("id", request_id or 0),
            "topic": topic,
            "params": {
                "request": request,
                "chainId": params.get("chainId"),
            },
        })

    async def _handle_session_update(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session update.
        
        Args:
            topic: Session topic
            params: Update parameters
            request_id: Request ID
        """
        namespaces = params.get("namespaces")
        if not namespaces:
            return
        
        # Update session
        await self.session.update(topic, {"namespaces": namespaces})
        
        # Acknowledge
        if topic in self._pending_acknowledgments:
            ack = self._pending_acknowledgments.pop(topic)
            if ack:
                await ack()

    async def _handle_session_extend(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session extend.
        
        Args:
            topic: Session topic
            params: Extend parameters
            request_id: Request ID
        """
        expiry = params.get("expiry")
        if expiry:
            await self.session.update(topic, {"expiry": expiry})
            # Update expiry in expirer
            if self.core.expirer.has(topic):
                self.core.expirer.set(topic, expiry)
        
        # Acknowledge
        if topic in self._pending_acknowledgments:
            ack = self._pending_acknowledgments.pop(topic)
            if ack:
                await ack()

    async def _handle_session_delete(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session delete.
        
        Args:
            topic: Session topic
            params: Delete parameters
            request_id: Request ID
        """
        await self.session.delete(topic)
        
        # Emit event
        await self.events.emit("session_delete", {
            "id": request_id or 0,
            "topic": topic,
        })

    async def _handle_session_event(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session event.
        
        Args:
            topic: Session topic
            params: Event parameters
            request_id: Request ID
        """
        # Events are emitted by the dapp, wallet just receives them
        # Could emit a custom event here if needed
        pass

    async def _handle_session_authenticate(
        self, topic: str, params: Dict[str, Any], request_id: Optional[int]
    ) -> None:
        """Handle session authenticate.
        
        Args:
            topic: Session topic
            params: Auth parameters
            request_id: Request ID
        """
        # Store pending auth request
        auth_id = request_id or 0
        self._pending_auth_requests[auth_id] = {
            "id": auth_id,
            "topic": topic,
            "params": params,
        }
        
        # Emit event
        await self.events.emit("session_authenticate", {
            "id": auth_id,
            "topic": topic,
            "params": params,
        })

    async def approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Approve session proposal.
        
        Args:
            params: Approval parameters with:
                - id: Proposal ID
                - namespaces: Session namespaces
                - sessionProperties: Optional session properties
                - scopedProperties: Optional scoped properties
                - sessionConfig: Optional session config
                - relayProtocol: Optional relay protocol
                
        Returns:
            Dict with 'topic' and 'acknowledged' callback
        """
        proposal_id = params.get("id")
        if not proposal_id:
            raise ValueError("Proposal ID required")
        
        # Get proposal
        try:
            proposal = self.proposal.get(proposal_id)
        except KeyError:
            raise ValueError("Proposal topic not found")
        
        topic = proposal.get("topic")
        
        if not topic:
            raise ValueError("Proposal topic not found")
        
        # Create session
        namespaces = params.get("namespaces", {})
        session_properties = params.get("sessionProperties")
        scoped_properties = params.get("scopedProperties")
        session_config = params.get("sessionConfig")
        
        # Calculate expiry (7 days default)
        import time
        expiry = int(time.time() * 1000) + (7 * 24 * 60 * 60 * 1000)
        
        session = {
            "topic": topic,
            "expiry": expiry,
            "namespaces": namespaces,
            "sessionProperties": session_properties,
            "scopedProperties": scoped_properties,
            "sessionConfig": session_config,
            "peer": proposal.get("params", {}).get("proposer", {}),
            "requiredNamespaces": proposal.get("params", {}).get("requiredNamespaces", {}),
            "optionalNamespaces": proposal.get("params", {}).get("optionalNamespaces", {}),
        }
        
        # Send approval message
        await self._send_session_approval(topic, session, proposal_id)
        
        # Store acknowledgment callback
        ack_called = False
        
        async def acknowledged() -> None:
            """Acknowledgment callback."""
            nonlocal ack_called
            if not ack_called:
                # Wait for session_settle message
                # For now, just mark as called
                ack_called = True
                # Store session immediately (in real impl, wait for settlement)
                await self.session.set(topic, session)
                # Delete proposal
                await self.proposal.delete(proposal_id)
        
        self._pending_acknowledgments[topic] = acknowledged
        
        return {"topic": topic, "acknowledged": acknowledged}

    async def _send_session_approval(
        self, topic: str, session: Dict[str, Any], proposal_id: int
    ) -> None:
        """Send session approval message.
        
        Args:
            topic: Session topic
            session: Session data
            proposal_id: Proposal ID
        """
        # Create approval payload
        payload = {
            "jsonrpc": "2.0",
            "id": proposal_id,
            "method": "wc_sessionApprove",
            "params": {
                "id": proposal_id,
                "relay": {"protocol": "irn"},
                "responderPublicKey": "",  # Will be set by crypto
                "namespaces": session["namespaces"],
            },
        }
        
        # Encode and publish
        encoded = await self.core.crypto.encode(topic, payload)
        await self.core.relayer.publish(topic, encoded)

    async def reject(self, params: Dict[str, Any]) -> None:
        """Reject session proposal.
        
        Args:
            params: Rejection parameters with 'id' and 'reason'
        """
        proposal_id = params.get("id")
        reason = params.get("reason", {"code": 5000, "message": "User rejected"})
        
        if not proposal_id:
            raise ValueError("Proposal ID required")
        
        # Get proposal
        try:
            proposal = self.proposal.get(proposal_id)
        except KeyError:
            raise ValueError("Proposal topic not found")
        
        topic = proposal.get("topic")
        
        if not topic:
            raise ValueError("Proposal topic not found")
        
        # Send rejection
        payload = {
            "jsonrpc": "2.0",
            "id": proposal_id,
            "method": "wc_sessionReject",
            "params": {
                "id": proposal_id,
                "reason": reason,
            },
        }
        
        encoded = await self.core.crypto.encode(topic, payload)
        await self.core.relayer.publish(topic, encoded)
        
        # Delete proposal
        await self.proposal.delete(proposal_id)
        # Remove from expirer
        if self.core.expirer.has(proposal_id):
            self.core.expirer.delete(proposal_id)

    async def update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update session.
        
        Args:
            params: Update parameters with 'topic' and 'namespaces'
            
        Returns:
            Dict with 'acknowledged' callback
        """
        topic = params.get("topic")
        namespaces = params.get("namespaces")
        
        if not topic or not namespaces:
            raise ValueError("Topic and namespaces required")
        
        # Send update
        payload = {
            "jsonrpc": "2.0",
            "method": "wc_sessionUpdate",
            "params": {
                "topic": topic,
                "namespaces": namespaces,
            },
        }
        
        encoded = await self.core.crypto.encode(topic, payload)
        await self.core.relayer.publish(topic, encoded)
        
        # Store acknowledgment
        ack_called = False
        
        async def acknowledged() -> None:
            """Acknowledgment callback."""
            nonlocal ack_called
            if not ack_called:
                ack_called = True
                # Update will be confirmed by session_update message
        
        self._pending_acknowledgments[topic] = acknowledged
        
        return {"acknowledged": acknowledged}

    async def extend(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extend session.
        
        Args:
            params: Extend parameters with 'topic'
            
        Returns:
            Dict with 'acknowledged' callback
        """
        topic = params.get("topic")
        if not topic:
            raise ValueError("Topic required")
        
        # Get current session to verify it exists
        session = self.session.get(topic)
        
        # Calculate new expiry (7 days from now)
        import time
        expiry = int(time.time() * 1000) + (7 * 24 * 60 * 60 * 1000)
        
        # Update session expiry immediately
        await self.session.update(topic, {"expiry": expiry})
        # Update expiry in expirer
        if self.core.expirer.has(topic):
            self.core.expirer.set(topic, expiry)
        
        # Send extend
        payload = {
            "jsonrpc": "2.0",
            "method": "wc_sessionExtend",
            "params": {
                "topic": topic,
                "expiry": expiry,
            },
        }
        
        encoded = await self.core.crypto.encode(topic, payload)
        await self.core.relayer.publish(topic, encoded)
        
        # Store acknowledgment
        ack_called = False
        
        async def acknowledged() -> None:
            """Acknowledgment callback."""
            nonlocal ack_called
            if not ack_called:
                ack_called = True
        
        self._pending_acknowledgments[topic] = acknowledged
        
        return {"acknowledged": acknowledged}

    async def respond(self, params: Dict[str, Any]) -> None:
        """Respond to session request.
        
        Args:
            params: Response parameters with 'topic' and 'response'
        """
        topic = params.get("topic")
        response = params.get("response")
        
        if not topic or not response:
            raise ValueError("Topic and response required")
        
        # Encode and publish response
        encoded = await self.core.crypto.encode(topic, response)
        await self.core.relayer.publish(topic, encoded)
        
        # Remove from pending requests
        request_id = response.get("id")
        if request_id:
            await self.request_store.delete(request_id)

    async def disconnect(self, params: Dict[str, Any]) -> None:
        """Disconnect session.
        
        Args:
            params: Disconnect parameters with 'topic' and 'reason'
        """
        topic = params.get("topic")
        reason = params.get("reason", {"code": 6000, "message": "User disconnected"})
        
        if not topic:
            raise ValueError("Topic required")
        
        # Send disconnect
        payload = {
            "jsonrpc": "2.0",
            "method": "wc_sessionDelete",
            "params": {
                "topic": topic,
                "reason": reason,
            },
        }
        
        encoded = await self.core.crypto.encode(topic, payload)
        await self.core.relayer.publish(topic, encoded)
        
        # Delete session
        await self.session.delete(topic)
        # Remove from expirer
        if self.core.expirer.has(topic):
            self.core.expirer.delete(topic)
        # Delete pending requests for this topic
        await self.request_store.delete_by_topic(topic)

    async def emit(self, params: Dict[str, Any]) -> None:
        """Emit session event.
        
        Args:
            params: Emit parameters with 'topic', 'event', and 'chainId'
        """
        topic = params.get("topic")
        event = params.get("event")
        chain_id = params.get("chainId")
        
        if not topic or not event or not chain_id:
            raise ValueError("Topic, event, and chainId required")
        
        # Send event
        payload = {
            "jsonrpc": "2.0",
            "method": "wc_sessionEvent",
            "params": {
                "topic": topic,
                "chainId": chain_id,
                "event": event,
            },
        }
        
        encoded = await self.core.crypto.encode(topic, payload)
        await self.core.relayer.publish(topic, encoded)

    def get_pending_session_requests(self) -> list[Dict[str, Any]]:
        """Get pending session requests.
        
        Returns:
            List of pending requests
        """
        return self.request_store.get_all()

    async def approve_session_authenticate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Approve session authentication.
        
        Args:
            params: Approval parameters with:
                - id: Auth request ID
                - auths: List of auth objects (CACAO)
                
        Returns:
            Dict with session
        """
        auth_id = params.get("id")
        auths = params.get("auths", [])
        
        if not auth_id:
            raise ValueError("Auth request ID required")
        
        if not auths:
            raise ValueError("Auths required")
        
        # Get pending auth request
        auth_request = self._pending_auth_requests.get(auth_id)
        if not auth_request:
            raise ValueError(f"Auth request not found: {auth_id}")
        
        topic = auth_request.get("topic")
        if not topic:
            raise ValueError("Auth request topic not found")
        
        # Send approval message
        payload = {
            "jsonrpc": "2.0",
            "id": auth_id,
            "method": "wc_sessionAuthenticateApprove",
            "params": {
                "id": auth_id,
                "auths": auths,
            },
        }
        
        encoded = await self.core.crypto.encode(topic, payload)
        await self.core.relayer.publish(topic, encoded)
        
        # Wait for session settlement (similar to approve flow)
        # For now, we'll create a session from the auth request
        # In a real implementation, we'd wait for wc_sessionSettle
        import time
        expiry = int(time.time() * 1000) + (7 * 24 * 60 * 60 * 1000)
        
        # Extract namespaces from auths (if available)
        # This is a simplified version - real impl would parse CACAO
        namespaces = {}
        for auth in auths:
            if isinstance(auth, dict) and "p" in auth:
                payload_auth = auth["p"]
                iss = payload_auth.get("iss", "")
                # Extract chain from iss (e.g., "did:pkh:eip155:1:0x...")
                if ":" in iss:
                    parts = iss.split(":")
                    if len(parts) >= 4:
                        chain_namespace = parts[2]  # eip155
                        chain_id = parts[3]  # 1
                        chain_key = f"{chain_namespace}:{chain_id}"
                        if chain_key not in namespaces:
                            namespaces[chain_key] = {
                                "chains": [chain_key],
                                "methods": ["personal_sign", "eth_sign", "eth_signTypedData"],
                                "events": ["chainChanged", "accountsChanged"],
                            }
        
        session = {
            "topic": topic,
            "expiry": expiry,
            "namespaces": namespaces,
            "peer": auth_request.get("params", {}).get("requester", {}),
        }
        
        # Store session
        await self.session.set(topic, session)
        
        # Register expiry
        self.core.expirer.set(topic, expiry)
        
        # Remove pending auth request
        del self._pending_auth_requests[auth_id]
        
        return {"session": session}

    async def reject_session_authenticate(self, params: Dict[str, Any]) -> None:
        """Reject session authentication.
        
        Args:
            params: Rejection parameters with:
                - id: Auth request ID
                - reason: Rejection reason
        """
        auth_id = params.get("id")
        reason = params.get("reason", {"code": 5000, "message": "User rejected"})
        
        if not auth_id:
            raise ValueError("Auth request ID required")
        
        # Get pending auth request
        auth_request = self._pending_auth_requests.get(auth_id)
        if not auth_request:
            raise ValueError(f"Auth request not found: {auth_id}")
        
        topic = auth_request.get("topic")
        if not topic:
            raise ValueError("Auth request topic not found")
        
        # Send rejection message
        payload = {
            "jsonrpc": "2.0",
            "id": auth_id,
            "method": "wc_sessionAuthenticateReject",
            "params": {
                "id": auth_id,
                "reason": reason,
            },
        }
        
        encoded = await self.core.crypto.encode(topic, payload)
        await self.core.relayer.publish(topic, encoded)
        
        # Remove pending auth request
        del self._pending_auth_requests[auth_id]

    def format_auth_message(self, params: Dict[str, Any]) -> str:
        """Format auth message (CACAO format).
        
        Args:
            params: Format parameters with 'request' and 'iss'
                - request: Auth request payload (CACAO payload params)
                - iss: Issuer (e.g., "did:pkh:eip155:1:0x...")
            
        Returns:
            Formatted message string
        """
        request = params.get("request", {})
        iss = params.get("iss", "")
        
        if not iss:
            raise ValueError("Issuer (iss) required")
        
        # Extract namespace from iss
        # Format: "did:pkh:eip155:1:0x..." or "eip155:1:0x..."
        did_prefix = "did:pkh:"
        if iss.startswith(did_prefix):
            parts = iss[len(did_prefix):].split(":")
        else:
            parts = iss.split(":")
        
        if len(parts) < 2:
            raise ValueError(f"Invalid issuer format: {iss}")
        
        namespace = parts[0]  # eip155
        chain_id = parts[1] if len(parts) > 1 else ""
        address = parts[2] if len(parts) > 2 else ""
        
        # Get namespace display name
        namespace_names = {
            "eip155": "Ethereum",
            "solana": "Solana",
            "bip122": "Bitcoin",
        }
        namespace_name = namespace_names.get(namespace, namespace)
        
        # Build message components
        domain = request.get("domain", "")
        if not domain:
            raise ValueError("Domain required in request")
        
        header = f"{domain} wants you to sign in with your {namespace_name} account:"
        wallet_address = address
        
        # Statement (can be None/empty)
        statement = request.get("statement") or None
        
        # URI
        aud = request.get("aud")
        uri_param = request.get("uri")
        if not aud and not uri_param:
            raise ValueError("Either 'aud' or 'uri' is required")
        uri = f"URI: {aud or uri_param}"
        
        # Version
        version = request.get("version", "1")
        version_line = f"Version: {version}"
        
        # Chain ID
        chain_id_line = f"Chain ID: {chain_id}"
        
        # Nonce
        nonce = request.get("nonce", "")
        nonce_line = f"Nonce: {nonce}"
        
        # Issued At
        iat = request.get("iat", "")
        issued_at_line = f"Issued At: {iat}"
        
        # Optional fields
        expiration_time = request.get("exp")
        expiration_line = f"Expiration Time: {expiration_time}" if expiration_time else None
        
        not_before = request.get("nbf")
        not_before_line = f"Not Before: {not_before}" if not_before else None
        
        request_id = request.get("requestId")
        request_id_line = f"Request ID: {request_id}" if request_id else None
        
        # Resources
        resources = request.get("resources", [])
        resources_line = None
        if resources:
            resources_lines = "\n".join([f"- {r}" for r in resources])
            resources_line = f"Resources:\n{resources_lines}"
        
        # Build message
        message_parts = [
            header,
            wallet_address,
            "",
            statement,
            "",
            uri,
            version_line,
            chain_id_line,
            nonce_line,
            issued_at_line,
            expiration_line,
            not_before_line,
            request_id_line,
            resources_line,
        ]
        
        # Filter out None/empty values
        message = "\n".join([part for part in message_parts if part])
        
        return message
    
    def _register_expirer_events(self) -> None:
        """Register expirer event listeners."""
        async def on_expired(event: Dict[str, Any]) -> None:
            """Handle expiry events."""
            target = event.get("target", "")
            try:
                parsed = parse_expirer_target(target)
                target_type = parsed.get("type")
                value = parsed.get("value")
                
                if target_type == "topic":
                    # Session expired
                    topic = value
                    if topic and self.session.has(topic):
                        await self.session.delete(topic)
                        await self.request_store.delete_by_topic(topic)
                        await self.events.emit("session_delete", {
                            "id": 0,
                            "topic": topic,
                        })
                elif target_type == "id":
                    # Proposal expired
                    proposal_id = value
                    if proposal_id and self.proposal.has(proposal_id):
                        await self.proposal.delete(proposal_id)
                        await self.events.emit("proposal_expire", {
                            "id": proposal_id,
                        })
            except Exception as e:
                self.core.logger.error(f"Error handling expiry: {e}")
        
        self.core.expirer.on(EXPIRER_EVENTS["expired"], on_expired)
    
    def on(self, event: str, listener: Any) -> EventEmitter:
        """Register event listener."""
        return self.events.on(event, listener)
    
    def once(self, event: str, listener: Any) -> EventEmitter:
        """Register one-time event listener."""
        return self.events.once(event, listener)
    
    def off(self, event: str, listener: Any) -> EventEmitter:
        """Remove event listener."""
        return self.events.off(event, listener)

