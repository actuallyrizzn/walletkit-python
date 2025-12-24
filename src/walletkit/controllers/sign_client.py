"""SignClient implementation for WalletConnect Sign Protocol."""
import base64
import json
import os
import time
from typing import Any, Callable, Dict, Optional

from walletkit.controllers.expirer import EXPIRER_EVENTS, parse_expirer_target
from walletkit.controllers.proposal_store import ProposalStore
from walletkit.controllers.request_store import RequestStore
from walletkit.controllers.session_store import SessionStore
from walletkit.controllers.sign_message_handler import SignMessageHandler
from walletkit.utils.crypto_utils import hash_key
from walletkit.utils.events import EventEmitter
from walletkit.utils.jsonrpc import (
    format_jsonrpc_error,
    format_jsonrpc_result,
    get_big_int_rpc_id,
    is_jsonrpc_response,
)


class SignClient:
    """SignClient for managing WalletConnect Sign Protocol sessions."""

    def __init__(
        self,
        core: Any,  # ICore
        metadata: Dict[str, Any],
        sign_config: Optional[Dict[str, Any]] = None,
        crypto: Optional[Any] = None,  # ICrypto (dependency injection)
        relayer: Optional[Any] = None,  # IRelayer (dependency injection)
    ) -> None:
        """Initialize SignClient.
        
        Args:
            core: Core instance
            metadata: Wallet metadata
            sign_config: Optional sign configuration
            crypto: Optional crypto controller (defaults to core.crypto)
            relayer: Optional relayer controller (defaults to core.relayer)
        """
        self.core = core
        self.metadata = metadata
        self.sign_config = sign_config or {}
        self.events = EventEmitter()
        
        # Dependency injection: use provided dependencies or fall back to core
        self._crypto = crypto if crypto is not None else core.crypto
        self._relayer = relayer if relayer is not None else core.relayer
        
        # Initialize stores
        storage = core.storage
        logger = core.logger
        storage_prefix = getattr(core, "storage_prefix", "wc@2:core:")
        
        self.session = SessionStore(storage, logger, storage_prefix)
        self.proposal = ProposalStore(storage, logger, storage_prefix)
        self.request_store = RequestStore(storage, logger, storage_prefix)
        
        # Message handler for protocol messages
        self._message_handler = SignMessageHandler(self)
        
        self._initialized = False
        self._pending_acknowledgments: Dict[str, Callable[[], Any]] = {}
        self._pending_auth_requests: Dict[int, Dict[str, Any]] = {}
        # Idempotency caches (Venice retries proposals/auth if it doesn't see acceptance fast enough)
        self._approved_proposals: Dict[int, Dict[str, Any]] = {}
        self._approved_auth: Dict[int, Dict[str, Any]] = {}

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
                if os.getenv("WALLETKIT_WC_DEBUG") == "1":
                    try:
                        pt = self._crypto.get_payload_type(message)
                        self.core.logger.debug(f"[WC_DEBUG] envelope type={pt} topic={topic}")
                    except Exception:
                        pass
                # Decode message
                payload = await self._crypto.decode(topic, message)
                
                if os.getenv("WALLETKIT_WC_DEBUG") == "1":
                    method = payload.get("method")
                    pid = payload.get("id")
                    self.core.logger.debug(f"[WC_DEBUG] inbound topic={topic} method={method} id={pid}")
                    # Helpful when we receive JSON-RPC responses (no method)
                    if not method:
                        self.core.logger.debug(f"[WC_DEBUG] inbound payload keys={list(payload.keys())}")
                        if is_jsonrpc_response(payload):
                            if "error" in payload:
                                self.core.logger.debug(f"[WC_DEBUG] inbound response error={payload.get('error')}")
                            else:
                                self.core.logger.debug("[WC_DEBUG] inbound response result present")

                # Handle based on method
                method = payload.get("method")
                if method:
                    await self._message_handler.handle_protocol_message(topic, payload)
            except Exception as e:
                if os.getenv("WALLETKIT_WC_DEBUG") == "1":
                    self.core.logger.error(f"[WC_DEBUG] decode failed topic={topic} err={e}")
                    self.core.logger.error(f"[WC_DEBUG] raw message prefix={str(message)[:80]}")
                self.core.logger.error(f"Error handling relayer message: {e}")
        
        self._relayer.on("message", on_message)

    async def _handle_protocol_message(self, topic: str, payload: Dict[str, Any]) -> None:
        """Handle protocol message (delegates to message handler).
        
        Args:
            topic: Message topic
            payload: Decoded JSON-RPC payload
        """
        await self._message_handler.handle_protocol_message(topic, payload)

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
        proposal_expiry = int(time.time()) + (5 * 60)
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

        if os.getenv("WALLETKIT_WC_DEBUG") == "1":
            try:
                keys = list(params.keys()) if isinstance(params, dict) else []
                self.core.logger.debug(f"[WC_DEBUG] authenticate params keys={keys}")
                ap = params.get("authPayload") if isinstance(params, dict) else None
                if isinstance(ap, dict):
                    self.core.logger.debug(f"[WC_DEBUG] authPayload keys={list(ap.keys())}")
                requester = params.get("requester") if isinstance(params, dict) else None
                if isinstance(requester, dict):
                    rpk = str(requester.get("publicKey") or "")
                    self.core.logger.debug(
                        f"[WC_DEBUG] requester.publicKey len={len(rpk)} prefix={rpk[:10]}"
                    )
            except Exception:
                pass
        
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
        
        pairing_topic = proposal.get("topic")
        if not pairing_topic:
            raise ValueError("Proposal topic not found")

        proposer = (proposal.get("params") or {}).get("proposer") or {}
        proposer_public_key = proposer.get("publicKey")
        if not proposer_public_key:
            raise ValueError("Proposal proposer publicKey not found")
        if os.getenv("WALLETKIT_WC_DEBUG") == "1":
            try:
                pk = str(proposer_public_key)
                self.core.logger.debug(f"[WC_DEBUG] proposer.publicKey len={len(pk)} prefix={pk[:10]}")
            except Exception:
                pass

        # Idempotency: if we already approved this proposal_id, reuse the same responder key + session topic.
        cached = self._approved_proposals.get(proposal_id)
        if cached:
            responder_public_key = cached["responder_public_key"]
            session_topic = cached["session_topic"]
        else:
            # Generate responder key pair + derive new session topic
            responder_public_key = await self._crypto.generate_key_pair()
            session_topic = await self._crypto.generate_shared_key(responder_public_key, proposer_public_key)
            self._approved_proposals[proposal_id] = {
                "responder_public_key": responder_public_key,
                "session_topic": session_topic,
                "pairing_topic": pairing_topic,
                "proposer_public_key": proposer_public_key,
            }

        # Subscribe to the new session topic so we can receive wc_sessionSettle and later requests
        await self._relayer.subscribe(session_topic)
        
        # Create session
        namespaces = params.get("namespaces", {})
        session_properties = params.get("sessionProperties")
        scoped_properties = params.get("scopedProperties")
        session_config = params.get("sessionConfig")
        
        # WalletConnect uses seconds-based expiries (see @walletconnect/utils calcExpiry)
        import time
        expiry = int(time.time()) + (7 * 24 * 60 * 60)
        
        session = {
            "topic": session_topic,
            "expiry": expiry,
            "namespaces": namespaces,
            "sessionProperties": session_properties,
            "scopedProperties": scoped_properties,
            "sessionConfig": session_config,
            "peer": proposal.get("params", {}).get("proposer", {}),
            "requiredNamespaces": proposal.get("params", {}).get("requiredNamespaces", {}),
            "optionalNamespaces": proposal.get("params", {}).get("optionalNamespaces", {}),
        }
        
        # Send approval flow:
        # - JSON-RPC result on pairing topic (wc_sessionPropose response)
        # - wc_sessionSettle request on derived session topic
        await self._send_session_approval(
            pairing_topic=pairing_topic,
            session_topic=session_topic,
            responder_public_key=responder_public_key,
            namespaces=namespaces,
            proposal_id=proposal_id,
            expiry=expiry,
            session_properties=session_properties,
            scoped_properties=scoped_properties,
            session_config=session_config,
        )
        
        # Store acknowledgment callback
        ack_called = False
        
        async def acknowledged() -> None:
            """Acknowledgment callback."""
            nonlocal ack_called
            if not ack_called:
                # In a full implementation, this should only resolve after wc_sessionSettle
                # is received on the derived session topic.
                ack_called = True
                # Delete proposal after ack
                await self.proposal.delete(proposal_id)
        
        self._pending_acknowledgments[session_topic] = acknowledged
        
        return {"topic": session_topic, "acknowledged": acknowledged}

    async def _send_session_approval(
        self,
        pairing_topic: str,
        session_topic: str,
        responder_public_key: str,
        namespaces: Dict[str, Any],
        proposal_id: int,
        expiry: int,
        session_properties: Any = None,
        scoped_properties: Any = None,
        session_config: Any = None,
    ) -> None:
        """Send session approval message.
        
        Args:
            pairing_topic: Pairing topic (topic used for the proposal exchange)
            responder_public_key: Responder X25519 public key (hex)
            namespaces: Approved namespaces
            proposal_id: Proposal ID
        """
        # Official behavior (see @walletconnect/sign-client ENGINE_RPC_OPTS):
        # - respond to wc_sessionPropose with JSON-RPC result on pairing topic
        # - send wc_sessionSettle request on derived session topic

        proposal_response = {"relay": {"protocol": "irn"}, "responderPublicKey": responder_public_key}
        pairing_result = format_jsonrpc_result(proposal_id, proposal_response)
        encoded = await self._crypto.encode(pairing_topic, pairing_result)
        self._capture_wc("session_propose_res", {
            "pairing_topic": pairing_topic,
            "session_topic": session_topic,
            "proposal_id": proposal_id,
            "responder_public_key": responder_public_key,
            "encoded": encoded,
            "sym_key": self._crypto.keychain.get(pairing_topic),
        })
        # wc_sessionPropose.res => ttl=300, prompt=false, tag=1101
        await self._relayer.publish(pairing_topic, encoded, {"tag": 1101, "ttl": 300, "prompt": False})

        settle_params: Dict[str, Any] = {
                "relay": {"protocol": "irn"},
            "namespaces": namespaces,
            "controller": {"publicKey": responder_public_key, "metadata": self.metadata},
            "expiry": expiry,
        }
        if session_properties is not None:
            settle_params["sessionProperties"] = session_properties
        if scoped_properties is not None:
            settle_params["scopedProperties"] = scoped_properties
        if session_config is not None:
            settle_params["sessionConfig"] = session_config

        settle_request = {
            "jsonrpc": "2.0",
            "id": get_big_int_rpc_id(),
            "method": "wc_sessionSettle",
            "params": settle_params,
        }
        encoded_settle = await self._crypto.encode(session_topic, settle_request)
        self._capture_wc("session_settle_req", {
            "session_topic": session_topic,
            "proposal_id": proposal_id,
            "responder_public_key": responder_public_key,
            "encoded": encoded_settle,
            "sym_key": self._crypto.keychain.get(session_topic),
        })
        # wc_sessionSettle.req => ttl=300, prompt=false, tag=1102
        await self._relayer.publish(session_topic, encoded_settle, {"tag": 1102, "ttl": 300, "prompt": False})

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
        
        encoded = await self._crypto.encode(topic, payload)
        # wc_sessionPropose.reject => ttl=300, prompt=false, tag=1120
        await self._relayer.publish(topic, encoded, {"tag": 1120, "ttl": 300, "prompt": False})
        
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
        
        encoded = await self._crypto.encode(topic, payload)
        await self._relayer.publish(topic, encoded, {"tag": 1117, "ttl": 3600, "prompt": True})
        
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
        expiry = int(time.time()) + (7 * 24 * 60 * 60)
        
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
        
        encoded = await self._crypto.encode(topic, payload)
        # Auth request tag observed from Venice is 1116; response tag should be 1117.
        await self._relayer.publish(topic, encoded, {"tag": 1117, "ttl": 24 * 60 * 60, "prompt": False})
        
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
        encoded = await self._crypto.encode(topic, response)
        await self._relayer.publish(topic, encoded)
        
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
        
        encoded = await self._crypto.encode(topic, payload)
        # Mirror JS engine opts observed via Docker oracle.
        await self._relayer.publish(topic, encoded, {"tag": 1117, "ttl": 3600, "prompt": True})
        
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
        
        encoded = await self._crypto.encode(topic, payload)
        # Auth request tag observed from Venice is 1116; response tag should be 1117.
        await self._relayer.publish(topic, encoded, {"tag": 1117, "ttl": 24 * 60 * 60, "prompt": False})

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
        
        # Get pending auth request. Venice/AppKit may emit duplicates; if we've already
        # approved this auth_id, treat it as idempotent.
        auth_request = self._pending_auth_requests.get(auth_id)
        if not auth_request:
            cached = self._approved_auth.get(auth_id)
            if cached:
                return {"session": {"topic": cached.get("session_topic")}}
            raise ValueError(f"Auth request not found: {auth_id}")
        
        params_obj = auth_request.get("params") or {}
        requester = params_obj.get("requester") if isinstance(params_obj, dict) else None
        requester_public_key = None
        requester_metadata = None
        if isinstance(requester, dict):
            requester_public_key = requester.get("publicKey")
            requester_metadata = requester.get("metadata")
        if not requester_public_key:
            raise ValueError("Auth requester publicKey not found")
        
        # Official sign-client:
        # - response topic = hashKey(requesterPublicKey)
        # - response is JSON-RPC result (tag 1117) encrypted as TYPE_1 using requesterPublicKey
        response_topic = hash_key(requester_public_key)

        # Idempotency: reuse responder/session for duplicate auth ids.
        cached = self._approved_auth.get(auth_id)
        if cached:
            responder_public_key = cached["responder_public_key"]
            session_topic = cached["session_topic"]
        else:
            responder_public_key = await self._crypto.generate_key_pair()
            session_topic = await self._crypto.generate_shared_key(
                responder_public_key, requester_public_key
            )
            self._approved_auth[auth_id] = {
                "responder_public_key": responder_public_key,
                "session_topic": session_topic,
                "response_topic": response_topic,
                "requester_public_key": requester_public_key,
            }
        await self._relayer.subscribe(session_topic)

        result = {
            "cacaos": auths,
            "responder": {"publicKey": responder_public_key, "metadata": self.metadata},
        }
        response_payload = format_jsonrpc_result(auth_id, result)
        encode_opts = {
            "type": 1,  # TYPE_1
            "receiverPublicKey": requester_public_key,
            "senderPublicKey": responder_public_key,
        }
        encoded = await self._crypto.encode(response_topic, response_payload, encode_opts)
        self._capture_wc("session_auth_res", {
            "auth_id": auth_id,
            "response_topic": response_topic,
            "requester_public_key": requester_public_key,
            "responder_public_key": responder_public_key,
            "encoded": encoded,
            "sym_key": self._crypto.keychain.get(response_topic),
            "encode_opts": encode_opts,
        })
        # wc_sessionAuthenticate.res => ttl=ONE_HOUR(3600), prompt=false, tag=1117
        await self._relayer.publish(response_topic, encoded, {"tag": 1117, "ttl": 3600, "prompt": False})
        
        # Wait for session settlement (similar to approve flow)
        # For now, we'll create a session from the auth request
        # In a real implementation, we'd wait for wc_sessionSettle
        import time
        expiry = int(time.time()) + (7 * 24 * 60 * 60)
        
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
            "topic": session_topic,
            "expiry": expiry,
            "namespaces": namespaces,
            "peer": requester_metadata or {},
        }
        
        # Store session
        await self.session.set(session_topic, session)
        
        # Register expiry
        self.core.expirer.set(session_topic, expiry)
        
        # Remove pending auth request (idempotent: Venice may retry / duplicate events)
        self._pending_auth_requests.pop(auth_id, None)
        
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
        
        params_obj = auth_request.get("params") or {}
        requester = params_obj.get("requester") if isinstance(params_obj, dict) else None
        requester_public_key = None
        if isinstance(requester, dict):
            requester_public_key = requester.get("publicKey")
        if not requester_public_key:
            raise ValueError("Auth requester publicKey not found")

        response_topic = hash_key(requester_public_key)
        responder_public_key = await self._crypto.generate_key_pair()
        
        # Send JSON-RPC error to response topic (wc_sessionAuthenticate reject path)
        error_payload = format_jsonrpc_error(auth_id, reason)
        encode_opts = {
            "type": 1,  # TYPE_1
            "receiverPublicKey": requester_public_key,
            "senderPublicKey": responder_public_key,
        }
        encoded = await self._crypto.encode(response_topic, error_payload, encode_opts)
        # wc_sessionAuthenticate.reject => ttl=300, prompt=false, tag=1118
        await self._relayer.publish(response_topic, encoded, {"tag": 1118, "ttl": 300, "prompt": False})
        
        # Remove pending auth request (idempotent)
        self._pending_auth_requests.pop(auth_id, None)

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
        
        # Statement (may be absent). WalletConnect also appends a Recap-derived
        # authorization statement when a `urn:recap:` resource is present.
        statement = request.get("statement")
        resources = request.get("resources", [])
        if isinstance(resources, list) and resources:
            recap = resources[-1]
            if isinstance(recap, str) and "urn:recap:" in recap:
                statement = self._append_recap_statement(statement, recap)
        # JS uses `statement || undefined`, i.e. empty string becomes omitted.
        if statement == "":
            statement = None
        
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
        resources_line = None
        if isinstance(resources, list) and resources:
            resources_lines = "\n".join([f"- {r}" for r in resources])
            resources_line = f"Resources:\n{resources_lines}"
        
        # Build message (match @walletconnect/utils `formatMessage` behavior):
        # - Keep empty strings to preserve intentional blank lines
        # - Only remove None values
        message_parts = [
            header,
            wallet_address,
            "",
            statement,  # may be None
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
        
        message = "\n".join([part for part in message_parts if part is not None])
        
        return message

    def _append_recap_statement(self, statement: Any, recap_resource: str) -> str:
        """Mirror @walletconnect/utils `formatStatementFromRecap` behavior.

        This appends a fixed authorization sentence derived from the Recap (CAIP-122 resources)
        to the provided statement.
        """
        base = "" if statement is None else str(statement)
        prefix = "I further authorize the stated URI to perform the following actions on my behalf: "
        if prefix in base:
            return base

        encoded = recap_resource.replace("urn:recap:", "")
        # base64url (no padding) -> bytes
        padded = encoded + "=" * ((4 - (len(encoded) % 4)) % 4)
        try:
            data = base64.urlsafe_b64decode(padded.encode("utf-8"))
            recap = json.loads(data.decode("utf-8"))
        except Exception:
            # If recap parsing fails, do not mutate the statement (best-effort).
            return base

        att = recap.get("att") if isinstance(recap, dict) else None
        if not isinstance(att, dict) or not att:
            return base

        parts: list[str] = []
        counter = 0
        for resource in att.keys():
            resource_att = att.get(resource)
            if not isinstance(resource_att, dict) or not resource_att:
                continue

            abilities_actions: list[dict[str, str]] = []
            for k in resource_att.keys():
                if not isinstance(k, str) or "/" not in k:
                    continue
                ability, action = k.split("/", 1)
                abilities_actions.append({"ability": ability, "action": action})

            abilities_actions.sort(key=lambda x: x["action"])
            grouped: dict[str, list[str]] = {}
            for item in abilities_actions:
                grouped.setdefault(item["ability"], []).append(item["action"])

            ability_chunks: list[str] = []
            for ability in grouped.keys():
                counter += 1
                actions = grouped[ability]
                ability_chunks.append(
                    f"({counter}) '{ability}': '" + "', '".join(actions) + f"' for '{resource}'."
                )

            chunk = ", ".join(ability_chunks).replace(".,", ".")
            if chunk:
                parts.append(chunk)

        if not parts:
            return base

        recap_stmt = prefix + " ".join(parts)
        return (base + " " if base else "") + recap_stmt

    def _capture_wc(self, kind: str, payload: Dict[str, Any]) -> None:
        """Append a JSONL capture record for debugging against JS reference tools."""
        path = os.getenv("WC_CAPTURE_PATH")
        if not path:
            return
        record = {
            "ts": int(time.time()),
            "kind": kind,
            **payload,
        }
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            # Never break protocol flow due to capture I/O.
            pass
    
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

