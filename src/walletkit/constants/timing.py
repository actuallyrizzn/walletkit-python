"""Timing constants for WalletKit."""

# TTL values (in seconds)
DEFAULT_TTL = 6 * 60 * 60  # 6 hours

# Heartbeat intervals (in seconds)
DEFAULT_HEARTBEAT_INTERVAL = 30.0
HEARTBEAT_TIMEOUT = 35.0  # DEFAULT_HEARTBEAT_INTERVAL + 5s buffer

# Reconnection delays (in seconds)
MAX_RECONNECT_DELAY = 30.0
INITIAL_RECONNECT_DELAY = 1.0

# Store limits
RECENTLY_DELETED_LIMIT = 200
