## Proposed Solution for Issue #43: Feature Envy

### Analysis
SignClient directly accesses:
- `self.core.crypto` - for encryption/decryption
- `self.core.relayer` - for message sending
- Should use dependency injection and interfaces

### Solution
I will use dependency injection to reduce coupling:

1. **Inject dependencies** in SignClient `__init__`:
   - Accept `crypto` and `relayer` as parameters (with defaults from core for backward compatibility)

2. **Update SignClient** to use injected dependencies instead of `self.core.crypto` and `self.core.relayer`

3. **Maintain backward compatibility** by defaulting to core attributes if not provided

### Benefits
- Reduced coupling
- Easier to test (can mock dependencies)
- Better separation of concerns
- More flexible architecture

### Implementation Plan
1. Add optional dependency parameters to SignClient.__init__
2. Update SignClient to use injected dependencies
3. Maintain backward compatibility
4. Run full test suite to ensure 100% green
