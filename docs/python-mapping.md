# JavaScript/TypeScript to Python Mapping

## Purpose

This document maps JavaScript/TypeScript language features, patterns, and libraries to their Python equivalents. This serves as a reference guide for porting the WalletKit SDK to Python.

## Table of Contents

1. [Language Feature Mappings](#language-feature-mappings)
2. [Library Equivalents](#library-equivalents)
3. [Reference Implementation Mappings](#reference-implementation-mappings)
4. [Code Style and Conventions](#code-style-and-conventions)

## Language Feature Mappings

### TypeScript Types → Python Typing

#### Basic Types

**TypeScript:**
```typescript
let name: string = "WalletKit";
let version: number = 1.0;
let active: boolean = true;
```

**Python:**
```python
name: str = "WalletKit"
version: float = 1.0
active: bool = True
```

#### Interfaces and Type Aliases

**TypeScript:**
```typescript
interface Options {
  core: ICore;
  metadata: Metadata;
  name?: string;
}

type Event = "session_proposal" | "session_request";
```

**Python:**
```python
from typing import Protocol, Optional, Literal
from dataclasses import dataclass

@dataclass
class Options:
    core: ICore
    metadata: Metadata
    name: Optional[str] = None

Event = Literal["session_proposal", "session_request"]
```

#### Generic Types

**TypeScript:**
```typescript
function getValue<T>(key: string): T | undefined {
  // ...
}
```

**Python:**
```python
from typing import TypeVar, Optional

T = TypeVar('T')

def get_value(key: str) -> Optional[T]:
    # ...
```

#### Abstract Classes

**TypeScript:**
```typescript
abstract class IWalletKit {
  public abstract pair(params: { uri: string }): Promise<void>;
}
```

**Python:**
```python
from abc import ABC, abstractmethod

class IWalletKit(ABC):
    @abstractmethod
    async def pair(self, params: dict[str, str]) -> None:
        pass
```

### EventEmitter → Python Event System

#### TypeScript EventEmitter

**TypeScript:**
```typescript
import EventEmitter from "events";

class MyClass extends EventEmitter {
  emit(event: string, data: any): boolean {
    return super.emit(event, data);
  }
  
  on(event: string, listener: (data: any) => void) {
    return super.on(event, listener);
  }
}
```

**Python Options:**

**Option 1: Custom EventEmitter**
```python
from typing import Callable, Any
from collections import defaultdict

class EventEmitter:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)
    
    def on(self, event: str, listener: Callable[[Any], None]) -> 'EventEmitter':
        self._listeners[event].append(listener)
        return self
    
    def emit(self, event: str, *args, **kwargs) -> bool:
        if event in self._listeners:
            for listener in self._listeners[event]:
                listener(*args, **kwargs)
            return True
        return False
```

**Option 2: Using asyncio.Event and asyncio.Queue**
```python
import asyncio
from typing import Callable, Any
from collections import defaultdict

class AsyncEventEmitter:
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)
        self._queues: dict[str, asyncio.Queue] = defaultdict(asyncio.Queue)
    
    def on(self, event: str, listener: Callable[[Any], None]) -> 'AsyncEventEmitter':
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

### Promises/Async-Await → Python asyncio

#### TypeScript Async/Await

**TypeScript:**
```typescript
async function initialize(): Promise<void> {
  await this.core.init();
  await this.engine.init();
}

async function getData(): Promise<Data> {
  const response = await fetch(url);
  return await response.json();
}
```

**Python:**
```python
import asyncio

async def initialize() -> None:
    await self.core.init()
    await self.engine.init()

async def get_data() -> Data:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

#### Promise.all()

**TypeScript:**
```typescript
const results = await Promise.all([
  task1(),
  task2(),
  task3()
]);
```

**Python:**
```python
results = await asyncio.gather(
    task1(),
    task2(),
    task3()
)
```

#### Promise.race()

**TypeScript:**
```typescript
const result = await Promise.race([
  task1(),
  task2()
]);
```

**Python:**
```python
done, pending = await asyncio.wait(
    [task1(), task2()],
    return_when=asyncio.FIRST_COMPLETED
)
result = done.pop().result()
```

### Classes and Inheritance

#### TypeScript Classes

**TypeScript:**
```typescript
class WalletKit extends IWalletKit {
  public name: string;
  private engine: Engine;
  
  constructor(opts: Options) {
    super(opts);
    this.name = opts.name || "walletkit";
  }
}
```

**Python:**
```python
class WalletKit(IWalletKit):
    def __init__(self, opts: Options):
        super().__init__(opts)
        self.name: str = opts.name or "walletkit"
        self._engine: Engine = Engine(self)
```

#### Static Methods

**TypeScript:**
```typescript
class WalletKit {
  static async init(opts: Options): Promise<WalletKit> {
    const client = new WalletKit(opts);
    await client.initialize();
    return client;
  }
}
```

**Python:**
```python
class WalletKit:
    @classmethod
    async def init(cls, opts: Options) -> 'WalletKit':
        client = cls(opts)
        await client.initialize()
        return client
```

### Module System

#### ES Modules → Python Packages

**TypeScript:**
```typescript
// index.ts
export { WalletKit } from "./client.js";
export * from "./types/index.js";

// client.ts
import { Engine } from "./controllers/index.js";
```

**Python:**
```python
# __init__.py
from .client import WalletKit
from .types import *

# client.py
from .controllers import Engine
```

## Library Equivalents

### EventEmitter

**JavaScript:** `events` package (Node.js built-in)

**Python Options:**
- Custom EventEmitter class (see above)
- `pydispatch` library
- `blinker` library (for signals)

**Recommendation:** Custom implementation for full control and compatibility.

### Type Definitions

**JavaScript:** TypeScript type system

**Python:**
- `typing` module (standard library)
- `typing_extensions` for advanced features
- `dataclasses` for data structures
- `Protocol` for structural typing

### Error Handling

**JavaScript:**
```typescript
try {
  await operation();
} catch (error: any) {
  this.logger.error(error.message);
  throw error;
}
```

**Python:**
```python
try:
    await operation()
except Exception as error:
    self.logger.error(str(error))
    raise
```

### WebSocket

**JavaScript:** `@walletconnect/jsonrpc-ws-connection`

**Python Options:**
- `websockets` library (recommended)
- `aiohttp` WebSocket support
- `websocket-client` (synchronous)

**Recommendation:** `websockets` for async/await support.

### Storage

**JavaScript:** `@walletconnect/keyvaluestorage`

**Python Options:**
- File-based storage (JSON, pickle)
- SQLite via `aiosqlite`
- In-memory storage
- Redis via `aioredis`

**Recommendation:** Abstract storage interface with multiple backends.

### Crypto

**JavaScript:** `@noble/ciphers`, `@noble/curves`, `@noble/hashes`

**Python Options:**
- `cryptography` library (comprehensive, recommended)
- `pycryptodome` (alternative)
- `pynacl` (for specific algorithms)

**Recommendation:** `cryptography` for broad algorithm support.

### JSON-RPC

**JavaScript:** `@walletconnect/jsonrpc-provider`, `@walletconnect/jsonrpc-utils`

**Python Options:**
- Custom JSON-RPC implementation
- `jsonrpc-async` library
- `jsonrpcclient` library

**Recommendation:** Custom implementation for full control and WalletConnect-specific needs.

### Logging

**JavaScript:** `@walletconnect/logger`

**Python:**
- `logging` module (standard library)
- `structlog` for structured logging

**Recommendation:** `logging` with custom formatter for structured logs.

### MessagePack

**JavaScript:** `@msgpack/msgpack`

**Python:**
- `msgpack` library

### Base Encoding

**JavaScript:** `@scure/base`, `bs58`

**Python:**
- `base64` (standard library)
- `base58` library
- `base58check` for Bitcoin-style encoding

### HTTP Client

**JavaScript:** `fetch` or `axios`

**Python:**
- `aiohttp` (async, recommended)
- `httpx` (async, alternative)
- `requests` (synchronous)

**Recommendation:** `aiohttp` for async support.

## Reference Implementation Mappings

### Core Controllers → Python Classes

#### Crypto Controller

**TypeScript:**
```typescript
export class Crypto {
  public async init(): Promise<void> { }
  public async encode(topic: string, message: string): Promise<string> { }
  public async decode(topic: string, encrypted: string): Promise<string> { }
}
```

**Python:**
```python
class Crypto:
    async def init(self) -> None:
        pass
    
    async def encode(self, topic: str, message: str) -> str:
        pass
    
    async def decode(self, topic: str, encrypted: str) -> str:
        pass
```

#### Relayer Controller

**TypeScript:**
```typescript
export class Relayer {
  public async init(): Promise<void> { }
  public async publish(topic: string, message: string): Promise<void> { }
  public async subscribe(topic: string): Promise<void> { }
}
```

**Python:**
```python
class Relayer:
    async def init(self) -> None:
        pass
    
    async def publish(self, topic: str, message: str) -> None:
        pass
    
    async def subscribe(self, topic: str) -> None:
        pass
```

### Utils Functions → Python Functions/Modules

#### CAIP Utilities

**TypeScript:**
```typescript
export function parseChainId(chainId: string): ChainId { }
export function formatChainId(chainId: ChainId): string { }
```

**Python:**
```python
def parse_chain_id(chain_id: str) -> ChainId:
    pass

def format_chain_id(chain_id: ChainId) -> str:
    pass
```

#### URI Utilities

**TypeScript:**
```typescript
export function parseUri(uri: string): ParsedUri { }
export function formatUri(params: FormatUriParams): string { }
```

**Python:**
```python
def parse_uri(uri: str) -> ParsedUri:
    pass

def format_uri(params: FormatUriParams) -> str:
    pass
```

## Code Style and Conventions

### Naming Conventions

**TypeScript (camelCase):**
```typescript
const clientName = "WalletKit";
function getActiveSessions() { }
```

**Python (snake_case):**
```python
client_name = "WalletKit"
def get_active_sessions():
    pass
```

### Type Hints

**Python:**
```python
from typing import Optional, Dict, List

def get_sessions() -> Dict[str, Session]:
    pass

def find_session(topic: Optional[str] = None) -> Optional[Session]:
    pass
```

### Async Context Managers

**Python:**
```python
async with websocket_connection() as ws:
    await ws.send(message)
    response = await ws.recv()
```

### Error Types

**Python:**
```python
class WalletKitError(Exception):
    pass

class SessionError(WalletKitError):
    pass

class PairingError(WalletKitError):
    pass
```

## TODO

- [ ] Create example port of a simple controller
- [ ] Document async patterns in detail
- [ ] Document error handling patterns
- [ ] Document testing patterns
- [ ] Create code comparison examples
- [ ] Document performance considerations

