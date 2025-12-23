"""Protocol compatibility tests for WalletConnect protocol."""
import pytest
import json
from typing import Dict, Any

from walletkit.utils.uri import parse_uri, format_uri
from walletkit.utils.jsonrpc import (
    format_jsonrpc_request,
    format_jsonrpc_result,
    format_jsonrpc_error,
    is_jsonrpc_request,
    is_jsonrpc_response,
    is_jsonrpc_result,
    is_jsonrpc_error,
)
from walletkit.utils.crypto_utils import (
    generate_key_pair,
    derive_sym_key,
    encrypt_message,
    decrypt_message,
    hash_message,
)


class TestURIParsing:
    """Test WalletConnect URI parsing and formatting."""
    
    def test_parse_valid_uri(self):
        """Test parsing a valid WalletConnect URI."""
        # Example URI format: wc:topic@version?symKey=...&relay-protocol=irn
        uri = "wc:abc123@2?symKey=def456&relay-protocol=irn"
        
        parsed = parse_uri(uri)
        
        assert parsed["protocol"] == "wc"
        assert parsed["topic"] == "abc123"
        assert parsed["version"] == 2
        assert parsed["symKey"] == "def456"
        assert parsed["relay"]["protocol"] == "irn"
    
    def test_format_valid_uri(self):
        """Test formatting a valid WalletConnect URI."""
        params = {
            "protocol": "wc",
            "topic": "abc123",
            "version": 2,
            "symKey": "def456",
            "relay": {"protocol": "irn"},
        }
        
        uri = format_uri(params)
        
        assert uri.startswith("wc:")
        assert "abc123" in uri
        assert "@2" in uri
        assert "symKey=def456" in uri
        assert "relay-protocol=irn" in uri
    
    def test_parse_format_roundtrip(self):
        """Test that parse and format are inverse operations."""
        original_params = {
            "protocol": "wc",
            "topic": "test_topic_123",
            "version": 2,
            "symKey": "test_sym_key",
            "relay": {"protocol": "irn"},
            "expiryTimestamp": 1234567890,
        }
        
        uri = format_uri(original_params)
        parsed = parse_uri(uri)
        
        assert parsed["protocol"] == original_params["protocol"]
        assert parsed["topic"] == original_params["topic"]
        assert parsed["version"] == original_params["version"]
        assert parsed["symKey"] == original_params["symKey"]
        assert parsed["relay"]["protocol"] == original_params["relay"]["protocol"]
    
    def test_parse_uri_with_methods(self):
        """Test parsing URI with methods parameter."""
        uri = "wc:topic@2?symKey=key&methods=wc_sessionPropose,wc_sessionApprove"
        
        parsed = parse_uri(uri)
        
        assert "methods" in parsed
        assert isinstance(parsed["methods"], list)
        assert "wc_sessionPropose" in parsed["methods"]
        assert "wc_sessionApprove" in parsed["methods"]
    
    def test_parse_uri_with_expiry(self):
        """Test parsing URI with expiry timestamp."""
        expiry = 1234567890
        uri = f"wc:topic@2?symKey=key&expiryTimestamp={expiry}"
        
        parsed = parse_uri(uri)
        
        assert parsed["expiryTimestamp"] == expiry


class TestJSONRPCCompatibility:
    """Test JSON-RPC 2.0 protocol compatibility."""
    
    def test_format_request(self):
        """Test formatting JSON-RPC request."""
        request = format_jsonrpc_request(
            method="wc_sessionPropose",
            params={"id": 1, "relay": {"protocol": "irn"}},
            request_id=123,
        )
        
        assert request["jsonrpc"] == "2.0"
        assert request["id"] == 123
        assert request["method"] == "wc_sessionPropose"
        assert request["params"]["id"] == 1
        assert is_jsonrpc_request(request)
    
    def test_format_result(self):
        """Test formatting JSON-RPC result."""
        result = format_jsonrpc_result(
            request_id=123,
            result={"topic": "abc", "session": {}},
        )
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 123
        assert "result" in result
        assert is_jsonrpc_result(result)
        assert is_jsonrpc_response(result)
    
    def test_format_error(self):
        """Test formatting JSON-RPC error."""
        error = format_jsonrpc_error(
            request_id=123,
            error={"code": -32000, "message": "Test error"},
        )
        
        assert error["jsonrpc"] == "2.0"
        assert error["id"] == 123
        assert "error" in error
        assert error["error"]["code"] == -32000
        assert is_jsonrpc_error(error)
        assert is_jsonrpc_response(error)
    
    def test_session_proposal_request_format(self):
        """Test session proposal request format matches WalletConnect spec."""
        request = format_jsonrpc_request(
            method="wc_sessionPropose",
            params={
                "id": 1,
                "relay": {"protocol": "irn"},
                "proposer": {
                    "publicKey": "pubkey",
                    "metadata": {
                        "name": "Test DApp",
                        "description": "Test Description",
                        "url": "https://test.com",
                        "icons": [],
                    },
                },
                "requiredNamespaces": {
                    "eip155": {
                        "chains": ["eip155:1"],
                        "methods": ["eth_sendTransaction"],
                        "events": ["chainChanged"],
                    },
                },
            },
            request_id=1,
        )
        
        assert request["method"] == "wc_sessionPropose"
        assert "params" in request
        assert "id" in request["params"]
        assert "relay" in request["params"]
        assert "proposer" in request["params"]
        assert "requiredNamespaces" in request["params"]
    
    def test_session_approval_response_format(self):
        """Test session approval response format matches WalletConnect spec."""
        response = format_jsonrpc_result(
            request_id=1,
            result={
                "relay": {"protocol": "irn"},
                "responderPublicKey": "responder_pubkey",
                "namespaces": {
                    "eip155": {
                        "chains": ["eip155:1"],
                        "methods": ["eth_sendTransaction"],
                        "events": ["chainChanged"],
                    },
                },
            },
        )
        
        assert "result" in response
        assert "relay" in response["result"]
        assert "responderPublicKey" in response["result"]
        assert "namespaces" in response["result"]


class TestCryptoCompatibility:
    """Test cryptographic operations compatibility."""
    
    def test_key_generation(self):
        """Test key pair generation produces valid keys."""
        key_pair = generate_key_pair()
        priv_key = key_pair["privateKey"]
        pub_key = key_pair["publicKey"]
        
        assert priv_key is not None
        assert pub_key is not None
        assert len(priv_key) == 64  # 32 bytes in hex
        assert len(pub_key) == 64  # 32 bytes in hex
    
    def test_key_derivation_commutative(self):
        """Test that key derivation is commutative (X25519 property)."""
        key_pair_a = generate_key_pair()
        key_pair_b = generate_key_pair()
        
        key_ab = derive_sym_key(key_pair_a["privateKey"], key_pair_b["publicKey"])
        key_ba = derive_sym_key(key_pair_b["privateKey"], key_pair_a["publicKey"])
        
        assert key_ab == key_ba, "Key derivation should be commutative"
    
    def test_encryption_decryption_roundtrip(self):
        """Test that encryption and decryption are inverse operations."""
        key_pair = generate_key_pair()
        sym_key = derive_sym_key(key_pair["privateKey"], key_pair["publicKey"])
        
        message = {"jsonrpc": "2.0", "id": 1, "method": "test"}
        message_str = json.dumps(message)
        
        encrypted = encrypt_message(sym_key, message_str)
        decrypted = decrypt_message(sym_key, encrypted)
        
        assert decrypted == message_str
        assert json.loads(decrypted) == message
    
    def test_hash_message(self):
        """Test message hashing produces consistent results."""
        message = "test message"
        
        hash1 = hash_message(message)
        hash2 = hash_message(message)
        
        assert hash1 == hash2, "Hash should be deterministic"
        assert len(hash1) == 64  # SHA256 in hex
    
    def test_different_messages_different_hashes(self):
        """Test that different messages produce different hashes."""
        hash1 = hash_message("message 1")
        hash2 = hash_message("message 2")
        
        assert hash1 != hash2, "Different messages should produce different hashes"


class TestMessageEnvelopeFormat:
    """Test WalletConnect message envelope format."""
    
    def test_envelope_structure(self):
        """Test that encrypted messages have correct envelope structure."""
        # WalletConnect uses a specific envelope format for encrypted messages
        # This is typically: base64(encrypted_payload)
        key_pair = generate_key_pair()
        sym_key = derive_sym_key(key_pair["privateKey"], key_pair["publicKey"])
        
        message = {"jsonrpc": "2.0", "id": 1, "method": "test"}
        message_str = json.dumps(message)
        
        encrypted = encrypt_message(sym_key, message_str)
        
        # Encrypted message should be a string (base64 encoded)
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
    
    def test_topic_derivation(self):
        """Test topic derivation from symmetric key."""
        # Topics in WalletConnect are derived from symmetric keys
        # This is typically done via hashing
        sym_key = "test_symmetric_key_32_bytes_long!!"
        
        # Topic should be derived from sym_key
        # In WalletConnect, this is typically done via hashing
        topic_hash = hash_message(sym_key)
        
        assert topic_hash is not None
        assert len(topic_hash) == 64  # SHA256 in hex


class TestProtocolMessageTypes:
    """Test WalletConnect protocol message types."""
    
    def test_session_propose_message(self):
        """Test session proposal message structure."""
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "wc_sessionPropose",
            "params": {
                "id": 1,
                "relay": {"protocol": "irn"},
                "proposer": {
                    "publicKey": "pubkey",
                    "metadata": {
                        "name": "Test",
                        "description": "Test",
                        "url": "https://test.com",
                        "icons": [],
                    },
                },
                "requiredNamespaces": {
                    "eip155": {
                        "chains": ["eip155:1"],
                        "methods": ["eth_sendTransaction"],
                        "events": ["chainChanged"],
                    },
                },
            },
        }
        
        assert message["method"] == "wc_sessionPropose"
        assert "params" in message
        assert "id" in message["params"]
        assert "proposer" in message["params"]
        assert is_jsonrpc_request(message)
    
    def test_session_approve_message(self):
        """Test session approval message structure."""
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "wc_sessionApprove",
            "params": {
                "id": 1,
                "relay": {"protocol": "irn"},
                "responderPublicKey": "responder_pubkey",
                "namespaces": {
                    "eip155": {
                        "chains": ["eip155:1"],
                        "methods": ["eth_sendTransaction"],
                        "events": ["chainChanged"],
                    },
                },
            },
        }
        
        assert message["method"] == "wc_sessionApprove"
        assert "params" in message
        assert "responderPublicKey" in message["params"]
        assert "namespaces" in message["params"]
        assert is_jsonrpc_request(message)
    
    def test_session_request_message(self):
        """Test session request message structure."""
        message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "wc_sessionRequest",
            "params": {
                "topic": "session_topic",
                "chainId": "eip155:1",
                "request": {
                    "method": "eth_sendTransaction",
                    "params": [{"to": "0x123", "value": "0x0"}],
                },
            },
        }
        
        assert message["method"] == "wc_sessionRequest"
        assert "params" in message
        assert "topic" in message["params"]
        assert "chainId" in message["params"]
        assert "request" in message["params"]
        assert is_jsonrpc_request(message)
    
    def test_session_delete_message(self):
        """Test session deletion message structure."""
        message = {
            "jsonrpc": "2.0",
            "method": "wc_sessionDelete",
            "params": {
                "topic": "session_topic",
                "reason": {"code": 6000, "message": "User disconnected"},
            },
        }
        
        assert message["method"] == "wc_sessionDelete"
        assert "params" in message
        assert "topic" in message["params"]
        assert "reason" in message["params"]


class TestNamespaceFormat:
    """Test WalletConnect namespace format compatibility."""
    
    def test_eip155_namespace_format(self):
        """Test EIP-155 namespace format."""
        namespace = {
            "eip155": {
                "chains": ["eip155:1", "eip155:137"],
                "methods": ["eth_sendTransaction", "eth_sign"],
                "events": ["chainChanged", "accountsChanged"],
            },
        }
        
        assert "eip155" in namespace
        assert "chains" in namespace["eip155"]
        assert "methods" in namespace["eip155"]
        assert "events" in namespace["eip155"]
        assert isinstance(namespace["eip155"]["chains"], list)
        assert isinstance(namespace["eip155"]["methods"], list)
        assert isinstance(namespace["eip155"]["events"], list)
    
    def test_chain_id_format(self):
        """Test chain ID format (namespace:chain_id)."""
        chain_ids = ["eip155:1", "eip155:137", "eip155:42161"]
        
        for chain_id in chain_ids:
            parts = chain_id.split(":")
            assert len(parts) == 2
            assert parts[0] == "eip155"
            assert parts[1].isdigit()


class TestErrorCodeCompatibility:
    """Test WalletConnect error code compatibility."""
    
    def test_standard_error_codes(self):
        """Test standard JSON-RPC error codes."""
        # Standard JSON-RPC error codes
        assert format_jsonrpc_error(1, {"code": -32700, "message": "Parse error"})["error"]["code"] == -32700
        assert format_jsonrpc_error(1, {"code": -32600, "message": "Invalid Request"})["error"]["code"] == -32600
        assert format_jsonrpc_error(1, {"code": -32601, "message": "Method not found"})["error"]["code"] == -32601
    
    def test_walletconnect_error_codes(self):
        """Test WalletConnect-specific error codes."""
        # WalletConnect uses custom error codes (5000+)
        error_codes = [5000, 5001, 6000, 6001]
        
        for code in error_codes:
            error = format_jsonrpc_error(1, {"code": code, "message": "Test"})
            assert error["error"]["code"] == code

