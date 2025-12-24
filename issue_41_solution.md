## Proposed Solution for Issue #41: God Objects (SignClient Split)

### Analysis
SignClient is 1218 lines with 32 methods, handling:
- Message routing and handling (8 handler methods)
- Session lifecycle (approve, reject, update, extend, disconnect)
- Authentication flows
- Event management
- Internal utilities

### Solution
I will extract message handlers into a separate `SignMessageHandler` class to reduce SignClient size and improve testability:

1. **Create `src/walletkit/controllers/sign_message_handler.py`** with:
   - All `_handle_*` methods moved from SignClient
   - Takes SignClient as dependency for accessing stores/events

2. **Refactor SignClient** to:
   - Delegate message handling to SignMessageHandler
   - Keep public API methods (approve, reject, update, etc.)
   - Maintain backward compatibility

### Benefits
- Reduced SignClient size (~200-300 lines)
- Better separation of concerns
- Easier to test message handling logic
- Maintains existing API

### Implementation Plan
1. Create SignMessageHandler class
2. Move handler methods to new class
3. Update SignClient to use handler
4. Run full test suite to ensure 100% green
5. Verify no regressions
