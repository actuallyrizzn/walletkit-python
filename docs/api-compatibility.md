# API Compatibility Goals

## Purpose

This document analyzes the target API surface for the Python port, compares method signatures between JavaScript and Python, and defines compatibility goals and breaking changes.

## Table of Contents

1. [Target API Surface](#target-api-surface)
2. [Method Signatures Comparison](#method-signatures-comparison)
3. [Event Handling API](#event-handling-api)
4. [Backward Compatibility](#backward-compatibility)
5. [Breaking Changes](#breaking-changes)
6. [Reference Implementation API Analysis](#reference-implementation-api-analysis)

## Target API Surface

### WalletKit Client API

The main public API that users interact with.

#### Initialization

**JavaScript:**
```typescript
import { Core } from "@walletconnect/core";
import { WalletKit } from "@reown/walletkit";

const core = new Core({
  projectId: process.env.PROJECT_ID,
});

const walletkit = await WalletKit.init({
  core,
  metadata: {
    name: "Demo app",
    description: "Demo Client as Wallet/Peer",
    url: "www.walletconnect.com",
    icons: [],
  },
});
```

**Python (Target):**
```python
from walletconnect.core import Core
from walletkit import WalletKit

core = Core(project_id=os.getenv("PROJECT_ID"))

walletkit = await WalletKit.init(
    core=core,
    metadata={
        "name": "Demo app",
        "description": "Demo Client as Wallet/Peer",
        "url": "www.walletconnect.com",
        "icons": [],
    }
)
```

#### Session Management

**JavaScript:**
```typescript
// Approve session
const session = await walletkit.approveSession({
  id: proposal.id,
  namespaces,
});

// Reject session
await walletkit.rejectSession({
  id: proposal.id,
  reason: getSdkError("USER_REJECTED_METHODS"),
});

// Update session
await walletkit.updateSession({
  topic,
  namespaces: newNs,
});

// Extend session
await walletkit.extendSession({ topic });

// Disconnect session
await walletkit.disconnectSession({
  topic,
  reason: getSdkError("USER_DISCONNECTED"),
});
```

**Python (Target):**
```python
# Approve session
session = await walletkit.approve_session(
    id=proposal.id,
    namespaces=namespaces
)

# Reject session
await walletkit.reject_session(
    id=proposal.id,
    reason=get_sdk_error("USER_REJECTED_METHODS")
)

# Update session
await walletkit.update_session(
    topic=topic,
    namespaces=new_ns
)

# Extend session
await walletkit.extend_session(topic=topic)

# Disconnect session
await walletkit.disconnect_session(
    topic=topic,
    reason=get_sdk_error("USER_DISCONNECTED")
)
```

#### Request Handling

**JavaScript:**
```typescript
// Respond to request
await walletkit.respondSessionRequest({
  id,
  result: response,
});

// Emit event
await walletkit.emitSessionEvent({
  topic,
  event: {
    name: "accountsChanged",
    data: ["0xab16a96D359eC26a11e2C2b3d8f8B8942d5Bfcdb"],
  },
  chainId: "eip155:1",
});
```

**Python (Target):**
```python
# Respond to request
await walletkit.respond_session_request(
    id=id,
    result=response
)

# Emit event
await walletkit.emit_session_event(
    topic=topic,
    event={
        "name": "accountsChanged",
        "data": ["0xab16a96D359eC26a11e2C2b3d8f8B8942d5Bfcdb"],
    },
    chain_id="eip155:1"
)
```

#### Query Methods

**JavaScript:**
```typescript
const sessions = walletkit.getActiveSessions();
const proposals = walletkit.getPendingSessionProposals();
const requests = walletkit.getPendingSessionRequests();
```

**Python (Target):**
```python
sessions = walletkit.get_active_sessions()
proposals = walletkit.get_pending_session_proposals()
requests = walletkit.get_pending_session_requests()
```

#### Pairing

**JavaScript:**
```typescript
await walletkit.pair({ uri });
```

**Python (Target):**
```python
await walletkit.pair(uri=uri)
```

#### Authentication

**JavaScript:**
```typescript
await walletkit.approveSessionAuthenticate(params);
await walletkit.rejectSessionAuthenticate(params);
const message = walletkit.formatAuthMessage(params);
```

**Python (Target):**
```python
await walletkit.approve_session_authenticate(params)
await walletkit.reject_session_authenticate(params)
message = walletkit.format_auth_message(params)
```

#### Push Notifications

**JavaScript:**
```typescript
await walletkit.registerDeviceToken(params);
```

**Python (Target):**
```python
await walletkit.register_device_token(params)
```

## Method Signatures Comparison

### Naming Conventions

**JavaScript (camelCase):**
- `approveSession`
- `getActiveSessions`
- `respondSessionRequest`

**Python (snake_case):**
- `approve_session`
- `get_active_sessions`
- `respond_session_request`

### Parameter Types

#### Options Objects

**JavaScript:**
```typescript
await walletkit.approveSession({
  id: proposal.id,
  namespaces,
  sessionProperties: {...},
});
```

**Python:**
```python
# Option 1: Keyword arguments
await walletkit.approve_session(
    id=proposal.id,
    namespaces=namespaces,
    session_properties={...}
)

# Option 2: Dataclass
@dataclass
class ApproveSessionParams:
    id: int
    namespaces: Dict[str, Namespace]
    session_properties: Optional[Dict] = None

await walletkit.approve_session(ApproveSessionParams(...))
```

**Recommendation:** Use keyword arguments for simplicity, dataclasses for complex parameters.

### Return Types

**JavaScript:**
```typescript
const session: SessionTypes.Struct = await walletkit.approveSession(...);
```

**Python:**
```python
session: SessionStruct = await walletkit.approve_session(...)
```

### Async/Await

Both JavaScript and Python use async/await, so the pattern is similar:

**JavaScript:**
```typescript
const result = await walletkit.method();
```

**Python:**
```python
result = await walletkit.method()
```

## Event Handling API

### Event Registration

**JavaScript:**
```typescript
walletkit.on("session_proposal", async (proposal) => {
  // Handle proposal
});

walletkit.once("session_request", async (request) => {
  // Handle request once
});

walletkit.off("session_proposal", handler);
```

**Python (Target):**
```python
@walletkit.on("session_proposal")
async def handle_proposal(proposal):
    # Handle proposal
    pass

@walletkit.once("session_request")
async def handle_request(request):
    # Handle request once
    pass

walletkit.off("session_proposal", handler)
```

**Alternative Python API:**
```python
async def handle_proposal(proposal):
    # Handle proposal
    pass

walletkit.on("session_proposal", handle_proposal)
walletkit.once("session_request", handle_request)
walletkit.off("session_proposal", handle_proposal)
```

**Recommendation:** Support both decorator and function-based registration.

### Event Types

**JavaScript:**
```typescript
type Event =
  | "session_proposal"
  | "session_request"
  | "session_delete"
  | "proposal_expire"
  | "session_request_expire"
  | "session_authenticate";
```

**Python:**
```python
from typing import Literal

Event = Literal[
    "session_proposal",
    "session_request",
    "session_delete",
    "proposal_expire",
    "session_request_expire",
    "session_authenticate"
]
```

### Event Arguments

**JavaScript:**
```typescript
walletkit.on("session_proposal", (proposal: SessionProposal) => {
  // proposal is typed
});
```

**Python:**
```python
from walletkit.types import SessionProposal

@walletkit.on("session_proposal")
async def handle_proposal(proposal: SessionProposal):
    # proposal is typed
    pass
```

## Backward Compatibility

### API Compatibility Goals

1. **Functional Compatibility:**
   - All JavaScript functionality should be available in Python
   - Same protocol behavior
   - Same error handling

2. **API Similarity:**
   - Similar method names (adapted to Python conventions)
   - Similar parameter structures
   - Similar return types

3. **Protocol Compatibility:**
   - Must be compatible with WalletConnect protocol
   - Must work with existing dApps and wallets
   - Must handle same message formats

### Non-Goals

1. **Exact API Match:**
   - Python naming conventions will differ (snake_case vs camelCase)
   - Some TypeScript-specific features won't translate directly

2. **Type System:**
   - Python type hints instead of TypeScript types
   - Runtime type checking may differ

## Breaking Changes

### Expected Breaking Changes

1. **Naming Conventions:**
   - All methods use snake_case instead of camelCase
   - This is expected and follows Python conventions

2. **Type System:**
   - TypeScript types → Python type hints
   - Runtime behavior may differ

3. **Error Handling:**
   - Python exceptions instead of JavaScript errors
   - Error types may differ

### Migration Guide

A migration guide should be created to help users transition from JavaScript to Python:

1. Method name mappings
2. Parameter differences
3. Type differences
4. Error handling differences
5. Examples of common patterns

## Reference Implementation API Analysis

### Core API that WalletKit Exposes

From analysis of the codebase, WalletKit exposes:

1. **Initialization:**
   - `WalletKit.init()` - Static factory method

2. **Session Management:**
   - `approveSession()` - Approve session proposal
   - `rejectSession()` - Reject session proposal
   - `updateSession()` - Update session namespaces
   - `extendSession()` - Extend session expiry
   - `disconnectSession()` - Disconnect session

3. **Request Handling:**
   - `respondSessionRequest()` - Respond to session request
   - `emitSessionEvent()` - Emit session event

4. **Query Methods:**
   - `getActiveSessions()` - Get all active sessions
   - `getPendingSessionProposals()` - Get pending proposals
   - `getPendingSessionRequests()` - Get pending requests

5. **Pairing:**
   - `pair()` - Pair with URI

6. **Authentication:**
   - `approveSessionAuthenticate()` - Approve authentication
   - `rejectSessionAuthenticate()` - Reject authentication
   - `formatAuthMessage()` - Format auth message

7. **Push Notifications:**
   - `registerDeviceToken()` - Register device token

8. **Events:**
   - `on()` - Register event listener
   - `once()` - Register one-time event listener
   - `off()` - Remove event listener
   - `removeListener()` - Remove event listener

### Sign Client API Usage

WalletKit's Engine wraps SignClient and uses:

1. **Initialization:**
   - `SignClient.init()`

2. **Session Operations:**
   - `signClient.approve()`
   - `signClient.reject()`
   - `signClient.update()`
   - `signClient.extend()`
   - `signClient.disconnect()`
   - `signClient.respond()`
   - `signClient.emit()`

3. **Query Methods:**
   - `signClient.session.get()`
   - `signClient.session.getAll()`
   - `signClient.proposal.getAll()`
   - `signClient.getPendingSessionRequests()`

4. **Authentication:**
   - `signClient.approveSessionAuthenticate()`
   - `signClient.rejectSessionAuthenticate()`
   - `signClient.formatAuthMessage()`

5. **Events:**
   - `signClient.events.on()`
   - `signClient.events.off()`

### Event Patterns

**Sign Client → Engine → WalletKit:**

```
SignClient Event → Engine Handler → WalletKit Event → User Listener
```

**Event Flow:**
1. SignClient emits event
2. Engine handler receives event
3. Engine emits WalletKit event
4. User listener receives WalletKit event

**Python Implementation:**
- Same pattern
- Use async event system
- Type-safe event arguments

## TODO

- [ ] Create detailed method signature comparison table
- [ ] Create migration guide
- [ ] Document all event types and arguments
- [ ] Create API reference documentation
- [ ] Document error types and handling
- [ ] Create code examples for common patterns

