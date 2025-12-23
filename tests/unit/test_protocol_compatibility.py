"""Unit tests for protocol compatibility (no external dependencies)."""
import pytest
import json

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


class TestURIParsingUnit:
    """Unit tests for URI parsing (no network)."""
    
    def test_parse_minimal_uri(self):
        """Test parsing minimal valid URI."""
        uri = "wc:topic@2?symKey=key"
        parsed = parse_uri(uri)
        
        assert parsed["protocol"] == "wc"
        assert parsed["topic"] == "topic"
        assert parsed["version"] == 2
        assert parsed["symKey"] == "key"
    
    def test_parse_uri_invalid_format(self):
        """Test parsing invalid URI format raises error."""
        with pytest.raises((ValueError, KeyError)):
            parse_uri("invalid_uri")
    
    def test_format_uri_minimal(self):
        """Test formatting minimal URI."""
        params = {
            "protocol": "wc",
            "topic": "topic",
            "version": 2,
            "symKey": "key",
        }
        
        uri = format_uri(params)
        assert uri.startswith("wc:")
        assert "@2" in uri
        assert "symKey=key" in uri


class TestJSONRPCUnit:
    """Unit tests for JSON-RPC compatibility."""
    
    def test_request_format(self):
        """Test JSON-RPC request format."""
        request = format_jsonrpc_request("test_method", {"param": "value"}, 1)
        
        assert request["jsonrpc"] == "2.0"
        assert request["id"] == 1
        assert request["method"] == "test_method"
        assert request["params"] == {"param": "value"}
        assert is_jsonrpc_request(request)
    
    def test_result_format(self):
        """Test JSON-RPC result format."""
        result = format_jsonrpc_result(1, "result_value")
        
        assert result["jsonrpc"] == "2.0"
        assert result["id"] == 1
        assert result["result"] == "result_value"
        assert is_jsonrpc_result(result)
        assert is_jsonrpc_response(result)
    
    def test_error_format(self):
        """Test JSON-RPC error format."""
        error = format_jsonrpc_error(1, {"code": -32000, "message": "Error"})
        
        assert error["jsonrpc"] == "2.0"
        assert error["id"] == 1
        assert "error" in error
        assert error["error"]["code"] == -32000
        assert is_jsonrpc_error(error)
        assert is_jsonrpc_response(error)
    
    def test_is_jsonrpc_request(self):
        """Test JSON-RPC request detection."""
        assert is_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "method": "test"})
        assert not is_jsonrpc_request({"jsonrpc": "2.0", "id": 1, "result": "test"})
    
    def test_is_jsonrpc_response(self):
        """Test JSON-RPC response detection."""
        assert is_jsonrpc_response({"jsonrpc": "2.0", "id": 1, "result": "test"})
        assert is_jsonrpc_response({"jsonrpc": "2.0", "id": 1, "error": {"code": -32000}})
        assert not is_jsonrpc_response({"jsonrpc": "2.0", "id": 1, "method": "test"})


class TestMessageFormatUnit:
    """Unit tests for message format validation."""
    
    def test_session_propose_format(self):
        """Test session proposal message format."""
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "wc_sessionPropose",
            "params": {
                "id": 1,
                "relay": {"protocol": "irn"},
                "proposer": {"publicKey": "pk", "metadata": {}},
                "requiredNamespaces": {},
            },
        }
        
        assert is_jsonrpc_request(message)
        assert message["method"] == "wc_sessionPropose"
        assert "params" in message
    
    def test_session_approve_format(self):
        """Test session approval message format."""
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "wc_sessionApprove",
            "params": {
                "id": 1,
                "relay": {"protocol": "irn"},
                "responderPublicKey": "pk",
                "namespaces": {},
            },
        }
        
        assert is_jsonrpc_request(message)
        assert message["method"] == "wc_sessionApprove"
        assert "params" in message

