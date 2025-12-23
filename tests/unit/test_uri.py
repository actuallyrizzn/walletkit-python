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

