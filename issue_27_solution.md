## Proposed Solution for Issue #27: Code Duplication

### Analysis
After reviewing the codebase, I've identified the following duplication patterns:

1. **Error Handling Pattern** - Repeated 16+ times in `client.py`:
   ```python
   try:
       return await self.engine.some_method(...)
   except Exception as error:
       self.logger.error(str(error))
       raise
   ```

2. **Initialization Checks** - Present in multiple controllers:
   ```python
   def _check_initialized(self) -> None:
       if not self._initialized:
           raise RuntimeError("Not initialized")
   ```

### Solution
I will create decorators to eliminate this duplication:

1. **Create `src/walletkit/utils/decorators.py`** with:
   - `handle_errors` decorator for async error handling/logging
   - `require_initialized` decorator for initialization checks

2. **Refactor `client.py`** to use the `handle_errors` decorator on all engine method calls

3. **Refactor controllers** to use the `require_initialized` decorator where applicable

### Benefits
- Reduced code duplication (eliminate 16+ try/except blocks)
- Consistent error handling across all methods
- Cleaner, more readable code
- Centralized error handling logic for easier maintenance

### Implementation Plan
1. Create decorators module
2. Apply decorators to client.py methods
3. Apply decorators to controller initialization checks
4. Run full test suite to ensure 100% green
5. Verify no regressions
