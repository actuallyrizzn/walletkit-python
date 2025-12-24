# Issue Groups for Concurrent Development

This document organizes all GitHub issues into groups that can be worked on concurrently by different agents without conflicts. Each group targets different files/areas to minimize merge conflicts.

## Group 1: Versioning & Testing (Priority: High)

**Can work together:** These are independent and can be done in parallel.

### Versioning
- **#44** - Set up proper package versioning strategy
  - Files: `pyproject.toml`, `setup.py`, `src/walletkit/__init__.py`
  - Create: `CHANGELOG.md`, version automation

### Testing Coverage & Quality
- **#34** - Test Coverage (aim for 90%+, add error path tests)
  - Files: `tests/unit/`, `tests/integration/`
  - Independent: Can add tests without touching source
  
- **#35** - Test Quality (simplify tests, add assertions)
  - Files: `tests/unit/`, `tests/integration/`
  - Independent: Refactoring tests only
  
- **#33** - Test Organization (extract shared utilities)
  - Files: `tests/shared/`, test fixtures
  - Independent: Creating new test utilities

**Branch Strategy:** `versioning-testing` - Can be one branch or split into `versioning` and `testing` sub-branches

---

## Group 2: Type System & Protocol Definitions (Priority: High)

**Can work in parallel:** Type annotations and protocol definitions are mostly additive.

### Type System Core
- **#7** - Excessive Any Types (replace with proper types)
  - Files: `src/walletkit/client.py`, `src/walletkit/core.py`, `src/walletkit/controllers/*.py`
  - Impact: Many files but mostly type annotations
  
- **#8** - TODO Type Definitions (create TypedDict classes)
  - Files: `src/walletkit/types/client.py`
  - Independent: New type definitions
  
- **#9** - Missing Type Annotations (add return types)
  - Files: `src/walletkit/controllers/*.py`, `src/walletkit/utils/*.py`
  - Independent: Adding annotations only

### Protocol/Interface Definitions
- **#25** - Logger Type Annotations (create Logger Protocol)
  - Files: `src/walletkit/types/logger.py` (new), update all `logger: Any`
  - Independent: New protocol file + updates
  
- **#26** - Core Interface Not Defined (create ICore Protocol)
  - Files: `src/walletkit/types/core.py` (new), update all `core: Any`
  - Independent: New protocol file + updates

**Branch Strategy:** `type-system` - All type-related work can be on one branch

---

## Group 3: Error Handling & Exception Hierarchy (Priority: High)

**Can work together:** Error handling changes are mostly independent of other work.

- **#19** - Bare Exception Handlers (replace with specific exceptions)
  - Files: `src/walletkit/controllers/*.py`, `src/walletkit/utils/*.py`
  - Impact: Many files but focused on exception handling
  
- **#20** - Inconsistent Error Handling Patterns (standardize)
  - Files: `src/walletkit/client.py`, `src/walletkit/controllers/*.py`
  - Impact: Standardizing patterns
  
- **#21** - Missing Exception Hierarchy (create exception classes)
  - Files: `src/walletkit/exceptions.py` (new), update error handling
  - Independent: New file + updates

**Branch Strategy:** `error-handling` - All error handling work on one branch

---

## Group 4: Configuration & Dependencies (Priority: Medium)

**Single agent recommended:** These all touch the same configuration files.

- **#22** - Duplicate Configuration (remove setup.py or consolidate)
  - Files: `setup.py`, `pyproject.toml`
  
- **#23** - Version Pinning Inconsistencies (add upper bounds, pip-compile)
  - Files: `pyproject.toml`, `requirements.txt`
  
- **#24** - Missing Dependency Groups (reorganize optional dependencies)
  - Files: `pyproject.toml`, `requirements-dev.txt`
  
- **#14** - Dependency Versions (regular updates, security monitoring)
  - Files: `pyproject.toml`, `requirements.txt`
  
- **#15** - Unused Dependencies (audit and remove)
  - Files: `pyproject.toml`, `requirements.txt`

**Branch Strategy:** `configuration` - Single branch for all config work

---

## Group 5: Code Quality & Refactoring (Priority: Medium)

**Can split into sub-groups:** Different areas of code quality.

### Code Patterns & Organization
- **#27** - Code Duplication (extract decorators, common patterns)
  - Files: `src/walletkit/client.py`, `src/walletkit/utils/decorators.py` (new)
  - Independent: New utility file + refactoring
  
- **#28** - Magic Strings and Numbers (extract to constants)
  - Files: `src/walletkit/constants/timing.py` (new), various controllers
  - Independent: New constants file + updates
  
- **#29** - Import Organization (run isort, fix imports)
  - Files: All Python files
  - Independent: Formatting only

### Architecture Refactoring
- **#41** - God Objects (split SignClient into smaller classes)
  - Files: `src/walletkit/controllers/sign_client.py` (split)
  - Impact: Large refactor, but isolated to one area
  
- **#42** - Primitive Obsession (create value objects)
  - Files: `src/walletkit/types/` (new value objects)
  - Independent: New type definitions
  
- **#43** - Feature Envy (reduce coupling, dependency injection)
  - Files: `src/walletkit/controllers/sign_client.py`, interfaces
  - Can work with #41

**Branch Strategy:** 
- `code-quality` for #27, #28, #29 (can be one branch)
- `refactoring` for #41, #42, #43 (should be together as they affect SignClient)

---

## Group 6: Security Improvements (Priority: Medium)

**Can work in parallel:** Different security areas.

- **#30** - Cryptographic Operations (constant-time comparisons, review)
  - Files: `src/walletkit/utils/crypto_utils.py`
  - Independent: Crypto code only
  
- **#31** - File Storage Security (file permissions, encryption)
  - Files: `src/walletkit/utils/storage.py`
  - Independent: Storage code only
  
- **#32** - Input Validation (pydantic, schema validation)
  - Files: `src/walletkit/utils/uri.py`, new validation modules
  - Independent: Validation logic

**Branch Strategy:** `security` - Can be one branch or split into `crypto`, `storage`, `validation` sub-branches

---

## Group 7: Performance Optimizations (Priority: Low)

**Can work in parallel:** Different performance areas.

- **#38** - Synchronous File I/O (use aiofiles for async I/O)
  - Files: `src/walletkit/utils/storage.py`
  - Note: May conflict with #31 (storage security), coordinate
  
- **#39** - Memory Usage (add size limits, LRU eviction)
  - Files: `src/walletkit/controllers/store.py`, `src/walletkit/utils/storage.py`
  - Note: May conflict with #38, coordinate
  
- **#40** - WebSocket Performance (queue limits, backpressure)
  - Files: `src/walletkit/controllers/relayer.py`
  - Independent: Relayer only

**Branch Strategy:** `performance` - Coordinate #38 and #39, #40 can be separate

---

## Group 8: Documentation (Priority: Low)

**Single agent recommended:** All documentation work.

- **#36** - Docstring Quality (standardize format, add examples)
  - Files: All Python files (docstrings)
  - Independent: Documentation only
  
- **#37** - API Documentation (generate with Sphinx, keep in sync)
  - Files: `docs/`, Sphinx configuration
  - Independent: Documentation generation

**Branch Strategy:** `documentation` - Single branch for all docs work

---

## Group 9: Platform & Compatibility (Priority: Low)

**Single agent recommended:** Testing and CI setup.

- **#12** - Windows Compatibility (test on Windows, document)
  - Files: CI configuration, documentation
  - Independent: Testing/CI only
  
- **#13** - Python Version Support (test matrix, CI)
  - Files: CI configuration (GitHub Actions)
  - Independent: CI only

**Branch Strategy:** `platform-compatibility` - Single branch for CI/testing setup

---

## Group 10: Implementation Details & TODOs (Priority: Low)

**Can work together:** Cleaning up incomplete implementations.

- **#10** - TODO Comments (address or create issues)
  - Files: `src/walletkit/controllers/pairing.py`, `src/walletkit/types/client.py`
  - Independent: Cleanup work
  
- **#11** - Incomplete Error Recovery (circuit breaker, retry logic)
  - Files: `src/walletkit/controllers/relayer.py`, new resilience modules
  - Independent: New features

**Branch Strategy:** `implementation-details` - Can be one branch

---

## Group 11: Specific Implementation Improvements (Priority: Medium)

**Can work in parallel:** Different controller implementations.

- **#16** - Relayer Implementation (narrow exceptions, rate limiting, metrics)
  - Files: `src/walletkit/controllers/relayer.py`
  - Independent: Relayer only
  
- **#17** - Crypto Implementation (error messages, constant-time, tests)
  - Files: `src/walletkit/controllers/crypto.py`, `src/walletkit/utils/crypto_utils.py`
  - Note: May overlap with #30, coordinate
  
- **#18** - Storage Implementation (async I/O, file locking, encryption)
  - Files: `src/walletkit/utils/storage.py`
  - Note: May conflict with #31, #38, coordinate

**Branch Strategy:** 
- `relayer-improvements` for #16
- `crypto-improvements` for #17 (coordinate with #30)
- `storage-improvements` for #18 (coordinate with #31, #38)

---

## Summary: Recommended Branch Strategy

### Phase 1: Foundation (Do First)
1. **`versioning-testing`** - Issues #44, #33, #34, #35
2. **`type-system`** - Issues #7, #8, #9, #25, #26
3. **`error-handling`** - Issues #19, #20, #21

### Phase 2: Configuration & Code Quality
4. **`configuration`** - Issues #22, #23, #24, #14, #15
5. **`code-quality`** - Issues #27, #28, #29
6. **`refactoring`** - Issues #41, #42, #43

### Phase 3: Security & Performance
7. **`security`** - Issues #30, #31, #32
8. **`performance`** - Issues #38, #39, #40 (coordinate #38/#39)

### Phase 4: Implementation & Platform
9. **`implementation-details`** - Issues #10, #11
10. **`relayer-improvements`** - Issue #16
11. **`crypto-improvements`** - Issue #17 (coordinate with #30)
12. **`storage-improvements`** - Issue #18 (coordinate with #31, #38)
13. **`platform-compatibility`** - Issues #12, #13
14. **`documentation`** - Issues #36, #37

### Coordination Notes

**Must coordinate (touch same files):**
- #38 and #39 (both touch storage.py)
- #31 and #18 (both touch storage.py)
- #30 and #17 (both touch crypto code)
- #38 and #18 (both touch storage.py)

**Can work in parallel (different files):**
- All type system issues (#7, #8, #9, #25, #26)
- All error handling issues (#19, #20, #21)
- Security issues (#30, #31, #32) - different areas
- Documentation issues (#36, #37)
- Platform issues (#12, #13)

**Recommended order to minimize conflicts:**
1. Type system first (affects many files but mostly annotations)
2. Error handling second (affects many files but focused changes)
3. Configuration third (touches few files)
4. Then other groups can proceed in parallel

