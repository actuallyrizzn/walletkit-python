"""Extended tests for JSON-RPC utilities."""
import pytest

from walletkit.utils.jsonrpc import (
    format_jsonrpc_error,
    format_jsonrpc_request,
    format_jsonrpc_result,
    get_big_int_rpc_id,
    is_jsonrpc_error,
    is_jsonrpc_request,
    is_jsonrpc_response,
    is_jsonrpc_result,
)


def test_get_big_int_rpc_id():
    """Test generating big int RPC ID."""
    id1 = get_big_int_rpc_id()
    assert isinstance(id1, int)
    assert id1 > 0
    
    # Should be different (or very close if called rapidly)
    import time
    time.sleep(0.01)
    id2 = get_big_int_rpc_id()
    # IDs should be large integers
    assert id2 > 0


def test_format_jsonrpc_request_with_params():
    """Test formatting JSON-RPC request with params."""
    request = format_jsonrpc_request("test_method", {"param1": "value1"})
    
    assert request["jsonrpc"] == "2.0"
    assert request["method"] == "test_method"
    assert request["params"] == {"param1": "value1"}
    assert "id" in request


def test_format_jsonrpc_result():
    """Test formatting JSON-RPC result."""
    result = format_jsonrpc_result(123, {"data": "test"})
    
    assert result["jsonrpc"] == "2.0"
    assert result["id"] == 123
    assert result["result"] == {"data": "test"}


def test_format_jsonrpc_error():
    """Test formatting JSON-RPC error."""
    error_dict = {"code": -32000, "message": "Test error", "data": {"details": "more info"}}
    error = format_jsonrpc_error(123, error_dict)
    
    assert error["jsonrpc"] == "2.0"
    assert error["id"] == 123
    assert "error" in error
    assert error["error"]["code"] == -32000
    assert error["error"]["message"] == "Test error"
    assert error["error"]["data"] == {"details": "more info"}


def test_is_jsonrpc_request():
    """Test is_jsonrpc_request check."""
    request = format_jsonrpc_request("test_method")
    assert is_jsonrpc_request(request) is True
    
    result = format_jsonrpc_result(1, {})
    assert is_jsonrpc_request(result) is False


def test_is_jsonrpc_response():
    """Test is_jsonrpc_response check."""
    result = format_jsonrpc_result(1, {})
    assert is_jsonrpc_response(result) is True
    
    error = format_jsonrpc_error(1, {"code": -32000, "message": "Error"})
    assert is_jsonrpc_response(error) is True
    
    request = format_jsonrpc_request("test")
    assert is_jsonrpc_response(request) is False


def test_is_jsonrpc_result():
    """Test is_jsonrpc_result check."""
    result = format_jsonrpc_result(1, {})
    assert is_jsonrpc_result(result) is True
    
    error = format_jsonrpc_error(1, {"code": -32000, "message": "Error"})
    assert is_jsonrpc_result(error) is False


def test_is_jsonrpc_error():
    """Test is_jsonrpc_error check."""
    error = format_jsonrpc_error(1, {"code": -32000, "message": "Error"})
    assert is_jsonrpc_error(error) is True
    
    result = format_jsonrpc_result(1, {})
    assert is_jsonrpc_error(result) is False

