"""Tests for JSON-RPC utilities."""
import pytest

from walletkit.utils.jsonrpc import (
    JsonRpcError,
    format_jsonrpc_error,
    format_jsonrpc_request,
    format_jsonrpc_result,
    is_jsonrpc_error,
    is_jsonrpc_request,
    is_jsonrpc_response,
    is_jsonrpc_result,
)


def test_format_jsonrpc_request():
    """Test formatting JSON-RPC request."""
    request = format_jsonrpc_request("test_method", {"param": "value"})

    assert request["jsonrpc"] == "2.0"
    assert request["method"] == "test_method"
    assert request["params"] == {"param": "value"}
    assert "id" in request


def test_format_jsonrpc_result():
    """Test formatting JSON-RPC result."""
    result = format_jsonrpc_result(123, {"data": "value"})

    assert result["jsonrpc"] == "2.0"
    assert result["id"] == 123
    assert result["result"] == {"data": "value"}


def test_format_jsonrpc_error():
    """Test formatting JSON-RPC error."""
    error = format_jsonrpc_error(123, JsonRpcError(-32000, "Test error"))

    assert error["jsonrpc"] == "2.0"
    assert error["id"] == 123
    assert error["error"]["code"] == -32000
    assert error["error"]["message"] == "Test error"


def test_is_jsonrpc_request():
    """Test checking if payload is request."""
    request = format_jsonrpc_request("test_method")
    assert is_jsonrpc_request(request) is True

    result = format_jsonrpc_result(123, "data")
    assert is_jsonrpc_request(result) is False


def test_is_jsonrpc_response():
    """Test checking if payload is response."""
    result = format_jsonrpc_result(123, "data")
    assert is_jsonrpc_response(result) is True

    error = format_jsonrpc_error(123, JsonRpcError(-32000, "Error"))
    assert is_jsonrpc_response(error) is True

    request = format_jsonrpc_request("test_method")
    assert is_jsonrpc_response(request) is False


def test_is_jsonrpc_result():
    """Test checking if payload is result."""
    result = format_jsonrpc_result(123, "data")
    assert is_jsonrpc_result(result) is True

    error = format_jsonrpc_error(123, JsonRpcError(-32000, "Error"))
    assert is_jsonrpc_result(error) is False


def test_is_jsonrpc_error():
    """Test checking if payload is error."""
    error = format_jsonrpc_error(123, JsonRpcError(-32000, "Error"))
    assert is_jsonrpc_error(error) is True

    result = format_jsonrpc_result(123, "data")
    assert is_jsonrpc_error(result) is False

