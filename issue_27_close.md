## Solution Implemented

Successfully addressed code duplication by:

1. **Created `src/walletkit/utils/decorators.py`** with:
   - `handle_errors` decorator for async/sync error handling and logging
   - `require_initialized` decorator for initialization checks

2. **Refactored `client.py`** to use `@handle_errors` decorator on all 16+ engine method calls, eliminating repetitive try/except blocks

3. **All tests passing** (82 passed, 3 skipped)

**Commit:** 0331f11
