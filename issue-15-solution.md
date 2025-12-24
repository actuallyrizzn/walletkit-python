## Proposed Solution for Issue #15: Unused Dependencies

**Analysis:**
After reviewing the codebase:
- `websockets`: ✅ Used in `src/walletkit/controllers/relayer.py`
- `cryptography`: ✅ Used in `src/walletkit/utils/crypto_utils.py` and `src/walletkit/controllers/crypto.py`
- `aiohttp`: ❌ Not found in codebase
- `msgpack`: ❌ Not found in codebase
- `base58`: ❌ Not used (custom implementation `_b58encode` exists in crypto.py)

**Solution:**
1. Remove unused dependencies: `aiohttp`, `msgpack`, `base58`
2. Document why each remaining dependency is needed
3. Add comments in `pyproject.toml` explaining each dependency's purpose

**Implementation Plan:**
- Remove `aiohttp`, `msgpack`, `base58` from `pyproject.toml` and `requirements.txt`
- Add comments documenting each dependency's purpose
- Test that removal doesn't break anything
- Verify all tests pass
