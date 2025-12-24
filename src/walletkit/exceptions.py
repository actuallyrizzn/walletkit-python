"""WalletKit exception hierarchy.

This module defines a comprehensive exception hierarchy for WalletKit errors.
All custom exceptions inherit from WalletKitError, allowing for both specific
and general error handling.
"""


class WalletKitError(Exception):
    """Base exception for all WalletKit errors.
    
    All custom exceptions in WalletKit should inherit from this class.
    This allows catching all WalletKit-specific errors with a single except clause.
    """
    pass


class InitializationError(WalletKitError):
    """Raised when initialization fails.
    
    This exception is raised when components fail to initialize properly,
    such as when storage cannot be accessed or required dependencies are missing.
    """
    pass


class RelayConnectionError(WalletKitError):
    """Raised when connection to relay fails.
    
    This exception is raised when the WebSocket connection to the WalletConnect
    relay server cannot be established or is lost.
    """
    pass


# Alias for backward compatibility (but prefer RelayConnectionError)
ConnectionError = RelayConnectionError


class ProtocolError(WalletKitError):
    """Raised when protocol errors occur.
    
    This exception is raised when there are issues with the WalletConnect protocol,
    such as invalid message formats, missing required fields, or protocol violations.
    """
    pass


class StorageError(WalletKitError):
    """Raised when storage operations fail.
    
    This exception is raised when storage operations (read, write, delete) fail,
    such as file I/O errors, permission issues, or corrupted data.
    """
    pass


class CryptoError(WalletKitError):
    """Raised when crypto operations fail.
    
    This exception is raised when cryptographic operations fail, such as
    encryption/decryption errors, key generation failures, or signature verification failures.
    """
    pass


class ValidationError(WalletKitError):
    """Raised when input validation fails.
    
    This exception is raised when input parameters are invalid, such as
    malformed URIs, missing required fields, or invalid data types.
    """
    pass


class OperationTimeoutError(WalletKitError):
    """Raised when operations timeout.
    
    This exception is raised when operations exceed their timeout period,
    such as connection timeouts, request timeouts, or heartbeat timeouts.
    """
    pass


# Alias for backward compatibility (but prefer OperationTimeoutError)
TimeoutError = OperationTimeoutError
