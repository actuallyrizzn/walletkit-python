"""Tests for URI utilities."""
import pytest

from walletkit.utils.uri import format_uri, parse_uri


def test_format_uri():
    """Test formatting WalletConnect URI."""
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test_topic",
        "symKey": "test_sym_key",
        "relay": {"protocol": "irn"},
    }
    
    uri = format_uri(params)
    assert uri.startswith("wc:")
    assert "test_topic" in uri
    assert "test_sym_key" in uri


def test_parse_uri():
    """Test parsing WalletConnect URI."""
    # Use format_uri to generate a valid URI, then parse it
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test_topic",
        "symKey": "test_sym_key",
        "relay": {"protocol": "irn"},
    }
    uri = format_uri(params)
    
    parsed = parse_uri(uri)
    assert parsed["protocol"] == "wc"
    assert parsed["version"] == 2
    assert parsed["topic"] == "test_topic"
    assert parsed["symKey"] == "test_sym_key"
    assert parsed["relay"]["protocol"] == "irn"


def test_parse_uri_with_expiry():
    """Test parsing URI with expiry timestamp."""
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test_topic",
        "symKey": "test_sym_key",
        "relay": {"protocol": "irn"},
        "expiryTimestamp": 1234567890,
    }
    uri = format_uri(params)
    
    parsed = parse_uri(uri)
    assert parsed.get("expiryTimestamp") == 1234567890


def test_format_parse_roundtrip():
    """Test format and parse roundtrip."""
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "roundtrip_topic",
        "symKey": "roundtrip_key",
        "relay": {"protocol": "irn"},
        "expiryTimestamp": 1234567890,
    }
    
    uri = format_uri(params)
    parsed = parse_uri(uri)
    
    assert parsed["topic"] == params["topic"]
    assert parsed["symKey"] == params["symKey"]
    assert parsed["relay"]["protocol"] == params["relay"]["protocol"]
    assert parsed.get("expiryTimestamp") == params["expiryTimestamp"]


def test_parse_uri_base64_encoded():
    """Test parsing base64 encoded URI."""
    from walletkit.utils.uri import parse_uri
    import base64
    
    # Create a valid URI and encode it
    uri = "wc:test_topic@2?symKey=test_key"
    encoded = base64.b64encode(uri.encode()).decode()
    
    parsed = parse_uri(encoded)
    assert parsed["topic"] == "test_topic"
    assert parsed["version"] == 2


def test_parse_uri_wc_protocol():
    """Test parsing URI with wc:// protocol."""
    from walletkit.utils.uri import parse_uri
    
    uri = "wc://test_topic@2?symKey=test_key"
    parsed = parse_uri(uri)
    assert parsed["protocol"] == "wc"
    assert parsed["topic"] == "test_topic"


def test_parse_uri_topic_with_slashes():
    """Test parsing topic with // prefix."""
    from walletkit.utils.uri import parse_uri, parse_topic
    
    # Test parse_topic directly
    assert parse_topic("//test_topic") == "test_topic"
    assert parse_topic("test_topic") == "test_topic"
    
    # Test in full URI
    uri = "wc:////test_topic@2?symKey=test_key"
    parsed = parse_uri(uri)
    assert parsed["topic"] == "test_topic"


def test_parse_uri_invalid_format():
    """Test parsing invalid URI format."""
    from walletkit.utils.uri import parse_uri
    
    # Missing version
    with pytest.raises(ValueError, match="Invalid URI format"):
        parse_uri("wc:test_topic")
    
    # Invalid version format
    with pytest.raises(ValueError, match="Invalid URI format"):
        parse_uri("wc:test_topic@2@3")


def test_parse_relay_params():
    """Test parse_relay_params function."""
    from walletkit.utils.uri import parse_relay_params
    
    params = {
        "relay-protocol": "irn",
        "relay-data": "test_data",
        "other-param": "value",
    }
    
    relay = parse_relay_params(params)
    assert relay["protocol"] == "irn"
    assert relay["data"] == "test_data"
    assert "other-param" not in relay


def test_format_relay_params():
    """Test format_relay_params function."""
    from walletkit.utils.uri import format_relay_params
    
    relay = {
        "protocol": "irn",
        "data": "test_data",
    }
    
    params = format_relay_params(relay)
    assert "relay-protocol" in params
    assert params["relay-protocol"] == "irn"
    assert "relay-data" in params


def test_format_relay_params_empty():
    """Test format_relay_params with empty values."""
    from walletkit.utils.uri import format_relay_params
    
    relay = {
        "protocol": "irn",
        "empty": None,
        "empty_str": "",
    }
    
    params = format_relay_params(relay)
    assert "relay-protocol" in params
    assert "relay-empty" not in params
    assert "relay-empty_str" not in params


def test_format_uri_with_methods():
    """Test format_uri with methods."""
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test_topic",
        "symKey": "test_key",
        "relay": {"protocol": "irn"},
        "methods": ["eth_sendTransaction", "eth_sign"],
    }
    
    uri = format_uri(params)
    assert "methods" in uri
    assert "eth_sendTransaction" in uri
    assert "eth_sign" in uri


def test_parse_uri_with_methods():
    """Test parse_uri with methods."""
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test_topic",
        "symKey": "test_key",
        "relay": {"protocol": "irn"},
        "methods": ["eth_sendTransaction", "eth_sign"],
    }
    uri = format_uri(params)
    
    parsed = parse_uri(uri)
    assert parsed["methods"] == ["eth_sendTransaction", "eth_sign"]


def test_format_uri_minimal():
    """Test format_uri with minimal params."""
    params = {
        "protocol": "wc",
        "version": 2,
        "topic": "test_topic",
    }
    
    uri = format_uri(params)
    assert uri.startswith("wc:test_topic@2")
    # Should have query string even if empty params
    assert "?" in uri or uri.endswith("@2")
