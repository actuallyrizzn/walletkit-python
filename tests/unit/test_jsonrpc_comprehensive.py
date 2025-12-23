"""Comprehensive tests for JSON-RPC utilities."""
import pytest

from walletkit.utils.jsonrpc import (
    JsonRpcError,
    format_jsonrpc_error,
    format_jsonrpc_request,
    format_jsonrpc_result,
    get_big_int_rpc_id,
    is_jsonrpc_error,
    is_jsonrpc_request,
    is_jsonrpc_response,
    is_jsonrpc_result,
)


def test_jsonrpc_error_exception():
    """Test JsonRpcError exception."""
    error = JsonRpcError(-32000, "Test error", {"details": "more info"})
    
    assert error.code == -32000
    assert error.message == "Test error"
    assert error.data == {"details": "more info"}
    assert "JSON-RPC Error" in str(error)


def test_format_jsonrpc_error_with_exception():
    """Test formatting JSON-RPC error with JsonRpcError object."""
    error_obj = JsonRpcError(-32000, "Test error", {"details": "info"})
    error = format_jsonrpc_error(123, error_obj)
    
    assert error["jsonrpc"] == "2.0"
    assert error["id"] == 123
    assert error["error"]["code"] == -32000
    assert error["error"]["message"] == "Test error"
    assert error["error"]["data"] == {"details": "info"}


def test_format_jsonrpc_error_without_data():
    """Test formatting JSON-RPC error without data."""
    error = format_jsonrpc_error(123, {"code": -32000, "message": "Error"})
    
    assert error["jsonrpc"] == "2.0"
    assert error["id"] == 123
    assert "error" in error
    assert "data" not in error["error"]


def test_format_jsonrpc_request_without_params():
    """Test formatting JSON-RPC request without params."""
    request = format_jsonrpc_request("test_method")
    
    assert request["jsonrpc"] == "2.0"
    assert request["method"] == "test_method"
    assert "id" in request
    assert "params" not in request


def test_format_jsonrpc_request_with_custom_id():
    """Test formatting JSON-RPC request with custom ID."""
    request = format_jsonrpc_request("test_method", None, 999)
    
    assert request["id"] == 999


def test_is_jsonrpc_request_with_params():
    """Test is_jsonrpc_request with request that has params."""
    request = format_jsonrpc_request("test", {"param": "value"})
    assert is_jsonrpc_request(request) is True


def test_is_jsonrpc_response_with_result():
    """Test is_jsonrpc_response with result."""
    result = format_jsonrpc_result(1, {"data": "test"})
    assert is_jsonrpc_response(result) is True


def test_is_jsonrpc_response_with_error():
    """Test is_jsonrpc_response with error."""
    error = format_jsonrpc_error(1, {"code": -32000, "message": "Error"})
    assert is_jsonrpc_response(error) is True


def test_is_jsonrpc_result_with_result():
    """Test is_jsonrpc_result."""
    result = format_jsonrpc_result(1, {"data": "test"})
    assert is_jsonrpc_result(result) is True
    
    error = format_jsonrpc_error(1, {"code": -32000, "message": "Error"})
    assert is_jsonrpc_result(error) is False


def test_is_jsonrpc_error_with_error():
    """Test is_jsonrpc_error."""
    error = format_jsonrpc_error(1, {"code": -32000, "message": "Error"})
    assert is_jsonrpc_error(error) is True
    
    result = format_jsonrpc_result(1, {"data": "test"})
    assert is_jsonrpc_error(result) is False

