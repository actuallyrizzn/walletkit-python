## Proposed Solution for Issue #42: Primitive Obsession

### Analysis
Many functions use raw primitives:
- Session topics as strings
- Proposal IDs as ints
- No validation at boundaries

### Solution
I will create value objects for key domain concepts:

1. **Create `src/walletkit/types/session.py`** with:
   - `SessionTopic` - validated string wrapper for session topics
   - `ProposalId` - validated int wrapper for proposal IDs

2. **Update SignClient methods** to accept value objects where appropriate

3. **Add validation** at boundaries to ensure type safety

### Benefits
- Type safety and validation
- Self-documenting code
- Easier to refactor
- Better IDE support

### Implementation Plan
1. Create value object classes
2. Update SignClient to use value objects for new code paths
3. Maintain backward compatibility with existing string/int usage
4. Run full test suite to ensure 100% green
