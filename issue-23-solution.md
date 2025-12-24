## Proposed Solution for Issue #23: Version Pinning Inconsistencies

**Current State:**
- Dependencies use `>=` with no upper bounds
- `requirements.txt` and `pyproject.toml` may drift

**Solution:**
1. Keep `>=` constraints in `pyproject.toml` for flexibility (allows users to get compatible updates)
2. Add upper bounds for major versions where appropriate (e.g., `>=11.0.0,<12.0.0`)
3. Set up `pip-compile` workflow to generate locked `requirements.txt` from `pyproject.toml`
4. Document version policy in README

**Implementation Plan:**
- Review each dependency and add appropriate upper bounds
- Install `pip-tools` if needed
- Generate `requirements.txt` from `pyproject.toml` using `pip-compile`
- Update documentation
