# Implementation Notes and Decisions

## Purpose

This document serves as a log of design decisions, challenges encountered, solutions implemented, and lessons learned during the Python port implementation. It should be updated as work progresses.

## Table of Contents

1. [Design Decisions](#design-decisions)
2. [Challenges Encountered](#challenges-encountered)
3. [Solutions and Alternatives](#solutions-and-alternatives)
4. [Performance Considerations](#performance-considerations)
5. [Threading vs Asyncio](#threading-vs-asyncio)
6. [Reference Implementation Learnings](#reference-implementation-learnings)

## Design Decisions

### Decision Log

#### 2024-XX-XX: Event System Implementation

**Decision:** Implement custom EventEmitter class instead of using existing library.

**Rationale:**
- Need exact API compatibility with TypeScript EventEmitter
- Existing libraries (pydispatch, blinker) have different APIs
- Custom implementation allows full control
- Can optimize for async/await patterns

**Alternatives Considered:**
- `pydispatch` - Different API, not async-friendly
- `blinker` - Signal-based, different pattern
- `asyncio.Event` - Too low-level, need higher-level API

**Status:** TODO - To be implemented

---

#### 2024-XX-XX: Storage Backend Selection

**Decision:** Start with file-based storage, add SQLite later.

**Rationale:**
- File-based is simplest to implement
- No external dependencies
- SQLite can be added as optional backend
- Matches Node.js localStorage pattern

**Alternatives Considered:**
- SQLite only - More complex, requires dependency
- In-memory only - Not persistent
- Multiple backends from start - More work upfront

**Status:** TODO - To be implemented

---

#### 2024-XX-XX: WebSocket Library Selection

**Decision:** Use `websockets` library for WebSocket connections.

**Rationale:**
- Native async/await support
- Good reconnection handling
- Active maintenance
- Well-documented

**Alternatives Considered:**
- `aiohttp` WebSocket - More complex, HTTP-focused
- `websocket-client` - Synchronous, not suitable

**Status:** TODO - To be implemented

---

#### 2024-XX-XX: Crypto Library Selection

**Decision:** Use `cryptography` library for cryptographic operations.

**Rationale:**
- Comprehensive algorithm support
- Well-maintained and secure
- Standard in Python ecosystem
- Supports X25519 and ChaCha20-Poly1305

**Alternatives Considered:**
- `pycryptodome` - Good but less comprehensive
- `pynacl` - Limited algorithm support

**Status:** TODO - To be implemented

---

#### 2024-XX-XX: Type System Approach

**Decision:** Use Python type hints with `typing` module.

**Rationale:**
- Standard Python approach
- Good IDE support
- Can use `mypy` for type checking
- Compatible with Python 3.8+

**Alternatives Considered:**
- No type hints - Less maintainable
- Runtime type checking - Overhead, not standard

**Status:** Adopted

---

#### 2024-XX-XX: Package Structure

**Decision:** Use `src/` layout with namespace package.

**Rationale:**
- Standard Python package structure
- Better for testing
- Clearer separation

**Alternatives Considered:**
- Flat structure - Less organized
- Multiple packages - More complex

**Status:** TODO - To be implemented

---

#### 2024-XX-XX: Testing Framework

**Decision:** Use `pytest` for testing.

**Rationale:**
- Standard in Python ecosystem
- Good async support
- Excellent fixtures
- Good plugin ecosystem

**Alternatives Considered:**
- `unittest` - Standard library but less features
- `nose2` - Less popular

**Status:** Adopted

---

#### 2024-XX-XX: Build Tool Selection

**Decision:** Use `poetry` for dependency management and building.

**Rationale:**
- Modern Python tooling
- Good dependency resolution
- Integrated building and publishing
- `pyproject.toml` standard

**Alternatives Considered:**
- `setuptools` - Traditional but verbose
- `hatchling` - Newer, less established

**Status:** TODO - To be implemented

## Challenges Encountered

### Challenge: Async Event System

**Description:** TypeScript EventEmitter is synchronous but used with async handlers. Need to support both sync and async handlers in Python.

**Status:** TODO - To be solved

**Potential Solutions:**
1. Always use async handlers
2. Support both sync and async
3. Use asyncio.Queue for async events

---

### Challenge: Storage Persistence

**Description:** Node.js uses localStorage/IndexedDB. Python needs file-based or database storage.

**Status:** TODO - To be solved

**Potential Solutions:**
1. File-based JSON storage
2. SQLite database
3. Multiple backends with abstraction

---

### Challenge: WebSocket Reconnection

**Description:** Need robust reconnection logic for WebSocket connections.

**Status:** TODO - To be solved

**Potential Solutions:**
1. Use `websockets` library reconnection
2. Custom reconnection logic
3. Exponential backoff

---

### Challenge: Crypto Compatibility

**Description:** Ensure crypto operations are compatible with JavaScript implementation.

**Status:** TODO - To be solved

**Potential Solutions:**
1. Use same algorithms (ChaCha20-Poly1305, X25519)
2. Test compatibility
3. Document any differences

---

### Challenge: Type System Differences

**Description:** TypeScript has more advanced type system than Python type hints.

**Status:** TODO - To be solved

**Potential Solutions:**
1. Use `typing_extensions` for advanced features
2. Use `Protocol` for structural typing
3. Document type limitations

---

### Challenge: Error Handling

**Description:** JavaScript errors vs Python exceptions.

**Status:** TODO - To be solved

**Potential Solutions:**
1. Create custom exception hierarchy
2. Map JavaScript errors to Python exceptions
3. Document error handling

## Solutions and Alternatives

### Event System Solutions

#### Solution 1: Custom Async EventEmitter

```python
class AsyncEventEmitter:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)
    
    def on(self, event: str, listener: Callable) -> 'AsyncEventEmitter':
        self._listeners[event].append(listener)
        return self
    
    async def emit(self, event: str, *args, **kwargs) -> bool:
        if event in self._listeners:
            for listener in self._listeners[event]:
                if asyncio.iscoroutinefunction(listener):
                    await listener(*args, **kwargs)
                else:
                    listener(*args, **kwargs)
            return True
        return False
```

**Pros:**
- Supports both sync and async handlers
- Simple implementation
- Good performance

**Cons:**
- Need to handle both cases
- Slightly more complex

**Status:** Recommended

---

#### Solution 2: Sync-Only EventEmitter

**Pros:**
- Simpler
- Matches some use cases

**Cons:**
- Doesn't support async handlers
- May need wrapper for async

**Status:** Not recommended

---

### Storage Solutions

#### Solution 1: File-Based JSON Storage

```python
class FileStorage:
    def __init__(self, path: Path):
        self.path = path
    
    async def get_item(self, key: str) -> Optional[Any]:
        data = await self._load()
        return data.get(key)
    
    async def set_item(self, key: str, value: Any) -> None:
        data = await self._load()
        data[key] = value
        await self._save(data)
```

**Pros:**
- Simple
- No dependencies
- Human-readable

**Cons:**
- Not concurrent-safe
- Slower for large data

**Status:** Good for initial implementation

---

#### Solution 2: SQLite Storage

**Pros:**
- Concurrent-safe
- Faster for large data
- Standard database

**Cons:**
- Requires dependency
- More complex

**Status:** Good for production

---

### WebSocket Solutions

#### Solution 1: websockets Library

**Pros:**
- Native async
- Good reconnection
- Well-maintained

**Cons:**
- External dependency

**Status:** Recommended

---

## Performance Considerations

### Async Performance

- Use `asyncio` efficiently
- Avoid blocking operations
- Use connection pooling where applicable

### Memory Management

- Be mindful of event listener storage
- Clean up resources properly
- Use weak references if needed

### Crypto Performance

- Cache keys where possible
- Use efficient crypto operations
- Consider hardware acceleration if available

## Threading vs Asyncio

### Decision: Use Asyncio

**Rationale:**
- JavaScript is single-threaded with async
- Python asyncio matches this pattern
- Better for I/O-bound operations
- Simpler than threading

### Threading Considerations

- Avoid threading for core functionality
- Use threading only if absolutely necessary
- Prefer asyncio for all async operations

## Reference Implementation Learnings

### Patterns Observed in Core/Utils

1. **Controller Pattern:**
   - Each controller handles specific concern
   - Controllers communicate via Core
   - Good separation of concerns

2. **Event-Driven Architecture:**
   - Events for all state changes
   - Hierarchical event propagation
   - Event history tracking

3. **Storage Abstraction:**
   - Abstract storage interface
   - Multiple backend support
   - Async operations

4. **Error Handling:**
   - Structured error types
   - Error propagation
   - Error logging

### Architecture Decisions to Replicate or Adapt

1. **Replicate:**
   - Controller pattern
   - Event-driven architecture
   - Storage abstraction

2. **Adapt:**
   - Python naming conventions
   - Python type system
   - Python async patterns

### Performance Optimizations to Consider

1. **Connection Pooling:**
   - Reuse WebSocket connections
   - Connection management

2. **Caching:**
   - Cache frequently accessed data
   - Cache crypto keys

3. **Lazy Loading:**
   - Load data on demand
   - Initialize components lazily

## TODO

- [ ] Document each design decision as it's made
- [ ] Document challenges as they're encountered
- [ ] Document solutions as they're implemented
- [ ] Update performance considerations
- [ ] Document any deviations from reference implementation

