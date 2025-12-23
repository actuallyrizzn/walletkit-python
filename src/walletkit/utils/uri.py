"""URI parsing and formatting utilities."""
import base64
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse


def parse_relay_params(params: Dict[str, Any], delimiter: str = "-") -> Dict[str, Any]:
    """Parse relay parameters from query params.
    
    Args:
        params: Query parameters
        delimiter: Parameter delimiter
        
    Returns:
        Relay parameters
    """
    relay: Dict[str, Any] = {}
    prefix = f"relay{delimiter}"
    
    for key, value in params.items():
        if key.startswith(prefix):
            name = key.replace(prefix, "")
            relay[name] = value
    
    return relay


def parse_topic(topic: str) -> str:
    """Parse topic from URI path.
    
    Args:
        topic: Topic string
        
    Returns:
        Parsed topic
    """
    if topic.startswith("//"):
        return topic[2:]
    return topic


def parse_uri(uri: str) -> Dict[str, Any]:
    """Parse WalletConnect URI.
    
    Args:
        uri: WalletConnect URI string
        
    Returns:
        Parsed URI parameters
    """
    # Handle base64 encoded URIs
    if "wc:" not in uri:
        try:
            decoded = base64.b64decode(uri).decode("utf-8")
            if "wc:" in decoded:
                uri = decoded
        except Exception:
            pass
    
    # Extract protocol
    protocol = "wc"
    if uri.startswith("wc://"):
        uri = uri[5:]  # Remove "wc://"
        protocol = "wc"
    elif uri.startswith("wc:"):
        uri = uri[3:]  # Remove "wc:"
        protocol = "wc"
    
    # Parse path (topic@version)
    path_end = uri.index("?") if "?" in uri else len(uri)
    path = uri[:path_end]
    
    # Split topic@version
    if "@" not in path:
        raise ValueError("Invalid URI format: missing version")
    
    required_values = path.split("@")
    if len(required_values) != 2:
        raise ValueError("Invalid URI format: missing version")
    
    topic = parse_topic(required_values[0])
    version = int(required_values[1])
    
    # Parse query string
    query_string = uri[path_end + 1 :] if path_end else ""
    query_params = parse_qs(query_string)
    
    # Convert to simple dict (parse_qs returns lists)
    params: Dict[str, Any] = {}
    for key, value_list in query_params.items():
        params[key] = value_list[0] if value_list else None
    
    # Parse methods
    methods: Optional[List[str]] = None
    if "methods" in params and params["methods"]:
        methods = params["methods"].split(",")
    
    # Parse expiry timestamp
    expiry_timestamp: Optional[int] = None
    if "expiryTimestamp" in params and params["expiryTimestamp"]:
        expiry_timestamp = int(params["expiryTimestamp"])
    
    return {
        "protocol": protocol,
        "topic": topic,
        "version": version,
        "symKey": params.get("symKey"),
        "relay": parse_relay_params(params),
        "methods": methods,
        "expiryTimestamp": expiry_timestamp,
    }


def format_relay_params(relay: Dict[str, Any], delimiter: str = "-") -> Dict[str, str]:
    """Format relay parameters for URI.
    
    Args:
        relay: Relay parameters
        delimiter: Parameter delimiter
        
    Returns:
        Formatted parameters
    """
    params: Dict[str, str] = {}
    prefix = "relay"
    
    for key, value in relay.items():
        if value:
            k = f"{prefix}{delimiter}{key}"
            params[k] = str(value)
    
    return params


def format_uri(params: Dict[str, Any]) -> str:
    """Format WalletConnect URI.
    
    Args:
        params: URI parameters with keys:
            - protocol: Protocol name
            - topic: Topic
            - version: Version number
            - symKey: Symmetric key
            - relay: Relay parameters
            - expiryTimestamp: Optional expiry timestamp
            - methods: Optional methods list
            
    Returns:
        Formatted URI string
    """
    all_params: Dict[str, str] = {}
    
    # Add relay params
    if "relay" in params:
        all_params.update(format_relay_params(params["relay"]))
    
    # Add other params
    if "symKey" in params:
        all_params["symKey"] = params["symKey"]
    
    if "expiryTimestamp" in params and params["expiryTimestamp"]:
        all_params["expiryTimestamp"] = str(params["expiryTimestamp"])
    
    if "methods" in params and params["methods"]:
        all_params["methods"] = ",".join(params["methods"])
    
    # Sort and build query string
    sorted_params = sorted(all_params.items())
    query_string = urlencode(sorted_params)
    
    protocol = params.get("protocol", "wc")
    topic = params["topic"]
    version = params["version"]
    
    return f"{protocol}:{topic}@{version}?{query_string}"

