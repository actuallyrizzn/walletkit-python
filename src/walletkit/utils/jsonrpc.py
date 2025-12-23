"""JSON-RPC utilities."""
from typing import Any, Dict, Optional, Union


class JsonRpcError(Exception):
    """JSON-RPC error."""

    def __init__(self, code: int, message: str, data: Optional[Any] = None) -> None:
        """Initialize JSON-RPC error.
        
        Args:
            code: Error code
            message: Error message
            data: Optional error data
        """
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"JSON-RPC Error {code}: {message}")


def format_jsonrpc_request(method: str, params: Optional[Any] = None, request_id: Optional[int] = None) -> Dict[str, Any]:
    """Format a JSON-RPC request.
    
    Args:
        method: RPC method name
        params: Method parameters
        request_id: Request ID (auto-generated if None)
        
    Returns:
        JSON-RPC request object
    """
    if request_id is None:
        import time
        request_id = int(time.time() * 1000)

    request: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "method": method,
        "id": request_id,
    }

    if params is not None:
        request["params"] = params

    return request


def format_jsonrpc_result(request_id: int, result: Any) -> Dict[str, Any]:
    """Format a JSON-RPC result response.
    
    Args:
        request_id: Request ID
        result: Result value
        
    Returns:
        JSON-RPC result object
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    }


def format_jsonrpc_error(request_id: int, error: Union[JsonRpcError, Dict[str, Any]]) -> Dict[str, Any]:
    """Format a JSON-RPC error response.
    
    Args:
        request_id: Request ID
        error: Error object or dict with code, message, data
        
    Returns:
        JSON-RPC error object
    """
    if isinstance(error, JsonRpcError):
        error_dict = {
            "code": error.code,
            "message": error.message,
        }
        if error.data is not None:
            error_dict["data"] = error.data
    else:
        error_dict = error

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": error_dict,
    }


def is_jsonrpc_request(payload: Dict[str, Any]) -> bool:
    """Check if payload is a JSON-RPC request.
    
    Args:
        payload: Payload to check
        
    Returns:
        True if request, False otherwise
    """
    return "method" in payload and "id" in payload


def is_jsonrpc_response(payload: Dict[str, Any]) -> bool:
    """Check if payload is a JSON-RPC response.
    
    Args:
        payload: Payload to check
        
    Returns:
        True if response, False otherwise
    """
    return ("result" in payload or "error" in payload) and "id" in payload


def is_jsonrpc_result(payload: Dict[str, Any]) -> bool:
    """Check if payload is a JSON-RPC result.
    
    Args:
        payload: Payload to check
        
    Returns:
        True if result, False otherwise
    """
    return "result" in payload and "id" in payload


def is_jsonrpc_error(payload: Dict[str, Any]) -> bool:
    """Check if payload is a JSON-RPC error.
    
    Args:
        payload: Payload to check
        
    Returns:
        True if error, False otherwise
    """
    return "error" in payload and "id" in payload

