## Proposed Solution for Issue #22: Duplicate Configuration

After reviewing the codebase, I've confirmed that dependencies are defined in multiple places:
- `setup.py` has `install_requires`
- `pyproject.toml` has `dependencies` (identical list)
- `requirements.txt` also lists dependencies

**Solution:**
1. Remove `install_requires` from `setup.py` since modern setuptools reads from `pyproject.toml`
2. Keep `setup.py` minimal (only for package discovery if needed, or remove entirely if not needed)
3. Update `requirements.txt` to be a pinned/locked version file (can be generated via pip-compile later)
4. Document that `pyproject.toml` is the single source of truth

**Implementation Plan:**
- Remove `install_requires` from `setup.py`
- Verify `pyproject.toml` has all necessary dependencies
- Update `requirements.txt` to reference pyproject.toml or document its purpose
- Test that installation still works correctly
