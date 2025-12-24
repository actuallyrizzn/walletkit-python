"""WalletKit Python SDK."""
from walletkit.client import WalletKit
from walletkit.core import Core
from walletkit.exceptions import (
    ConnectionError,  # Alias for RelayConnectionError
    CryptoError,
    InitializationError,
    OperationTimeoutError,
    ProtocolError,
    RelayConnectionError,
    StorageError,
    TimeoutError,  # Alias for OperationTimeoutError
    ValidationError,
    WalletKitError,
)

__all__ = [
    "WalletKit",
    "Core",
    "WalletKitError",
    "InitializationError",
    "RelayConnectionError",
    "ConnectionError",  # Alias for RelayConnectionError
    "ProtocolError",
    "StorageError",
    "CryptoError",
    "ValidationError",
    "OperationTimeoutError",
    "TimeoutError",  # Alias for OperationTimeoutError
]

__version__ = "0.1.0"
