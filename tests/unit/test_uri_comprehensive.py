"""Comprehensive tests for URI utilities."""
import pytest

from walletkit.utils.uri import (
    format_uri,
    parse_uri,
    format_relay_params,
    parse_relay_params,
)


def test_format_relay_params():
    """Test formatting relay parameters."""
    relay = {
        "protocol": "irn",
        "data": "test_data",
    }
    
    params = format_relay_params(relay)
    
    assert "relay-protocol" in params
    assert params["relay-protocol"] == "irn"
    assert "relay-data" in params
    assert params["relay-data"] == "test_data"


def test_parse_relay_params():
    """Test parsing relay parameters."""
    query_params = {
        "relay-protocol": "irn",
        "relay-data": "test_data",
        "symKey": "key",
    }
    
    relay = parse_relay_params(query_params)
    
    assert relay["protocol"] == "irn"
    assert relay["data"] == "test_data"
    assert "symKey" not in relay


# Note: format_topic_target and format_id_target are in expirer.py, not uri.py


def test_parse_uri_with_methods():
    """Test parsing URI with methods."""
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test_topic",
        "symKey": "key",
        "relay": {"protocol": "irn"},
        "methods": ["eth_sendTransaction", "eth_sign"],
    }
    
    uri = format_uri(params)
    parsed = parse_uri(uri)
    
    assert parsed["methods"] == ["eth_sendTransaction", "eth_sign"]


def test_format_uri_with_methods():
    """Test formatting URI with methods."""
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test_topic",
        "symKey": "key",
        "relay": {"protocol": "irn"},
        "methods": ["method1", "method2"],
    }
    
    uri = format_uri(params)
    assert "methods=method1%2Cmethod2" in uri or "methods=method2%2Cmethod1" in uri


def test_parse_uri_base64_encoded():
    """Test parsing base64 encoded URI."""
    import base64
    
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test",
        "symKey": "key",
        "relay": {"protocol": "irn"},
    }
    uri = format_uri(params)
    encoded = base64.b64encode(uri.encode()).decode()
    
    # Should decode and parse correctly
    parsed = parse_uri(encoded)
    assert parsed["topic"] == "test"


def test_format_uri_minimal():
    """Test formatting URI with minimal params."""
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test",
        "relay": {"protocol": "irn"},
    }
    
    uri = format_uri(params)
    assert uri.startswith("wc:")
    assert "test@2" in uri

