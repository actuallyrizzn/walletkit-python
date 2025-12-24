## Proposed Solution for Issue #24: Missing Dependency Groups

**Current State:**
- `pyproject.toml` has `dev` and `storage` groups
- `requirements-dev.txt` has additional dependencies not in `dev` group
- No clear separation between dev tools, test tools, and docs tools

**Solution:**
1. Reorganize `[project.optional-dependencies]` into logical groups:
   - `dev`: Development tools (black, flake8, isort, mypy)
   - `test`: Testing tools (pytest, pytest-asyncio, pytest-cov, pytest-mock)
   - `docs`: Documentation tools (sphinx, sphinx-rtd-theme)
   - `storage`: Storage backends (aiosqlite)
   - `all-dev`: Meta-group that includes dev, test, docs
2. Consolidate all dependencies from `requirements-dev.txt` into appropriate groups
3. Update `requirements-dev.txt` to be generated from pyproject.toml or make it a simple reference

**Implementation Plan:**
- Audit all dependencies in `requirements-dev.txt`
- Categorize and add to appropriate groups in `pyproject.toml`
- Update `requirements-dev.txt`
- Test installation with different groups
