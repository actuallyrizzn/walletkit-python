## Proposed Solution for Issue #28: Magic Strings and Numbers

### Analysis
After reviewing the codebase, I've identified the following magic values:

1. **Time Constants:**
   - `6 * 60 * 60` - TTL in seconds (6 hours) in `relayer.py`
   - `30.0` - Heartbeat interval in seconds in `relayer.py` (appears twice)
   - `30.0` - Max reconnect delay in `relayer.py`

2. **Size Limits:**
   - `200` - Recently deleted limit in `store.py`

### Solution
I will create a constants module to extract all magic numbers:

1. **Create `src/walletkit/constants/timing.py`** with:
   - `DEFAULT_TTL` = 6 * 60 * 60 (6 hours)
   - `DEFAULT_HEARTBEAT_INTERVAL` = 30.0 seconds
   - `MAX_RECONNECT_DELAY` = 30.0 seconds
   - `RECENTLY_DELETED_LIMIT` = 200

2. **Update `relayer.py`** to use timing constants and make heartbeat interval configurable

3. **Update `store.py`** to use the recently deleted limit constant

### Benefits
- Self-documenting code (no mental calculation needed)
- Single source of truth for timing values
- Easier to maintain and modify
- Can be made configurable where appropriate

### Implementation Plan
1. Create constants/timing.py module
2. Replace magic numbers in relayer.py
3. Replace magic number in store.py
4. Update constants/__init__.py to export new constants
5. Run full test suite to ensure 100% green
