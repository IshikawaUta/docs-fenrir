# Hook System

Fenrir v4.1.2 includes a powerful hook/extension point system for intercepting and modifying framework behavior.

## Overview

The hook system provides:

- **Priority Ordering**: Control execution order with numeric priorities
- **One-Time Hooks**: Auto-remove after first execution
- **Wildcard Hooks**: Listen to all events with `*`
- **Async/Sync Support**: Mix async and sync handlers
- **Middleware Integration**: Use hooks as middleware
- **Hook Cancellation**: Stop hook execution chain

## Basic Usage

```python
from fenrir.hooks import HookRegistry

hooks = HookRegistry()

# Register a hook
@hooks.register("request.start")
async def on_request_start(request):
    print(f"Request started: {request.method} {request.path}")

# Register with priority (lower = earlier)
@hooks.register("request.end", priority=10)
async def on_request_end(request, response):
    print("Request ended")
```

## Hook Events

### Built-in Events

```python
# Request lifecycle
hooks.register("request.start")      # Before request handling
hooks.register("request.end")        # After request handling
hooks.register("request.error")      # On request error

# Response lifecycle
hooks.register("response.start")     # Before response sent
hooks.register("response.end")       # After response sent

# App lifecycle
hooks.register("app.start")          # App startup
hooks.register("app.stop")           # App shutdown

# Custom events
hooks.register("user.login")         # Custom event
hooks.register("order.created")      # Custom event
```

### Wildcard Hooks

Listen to all events:

```python
@hooks.register("*")
async def on_any_event(event, **kwargs):
    print(f"Event: {event}")
```

## Priority Ordering

Control execution order with numeric priorities (lower = earlier):

```python
@hooks.register("request.start", priority=10)
async def first_handler(request):
    print("First")  # Runs first

@hooks.register("request.start", priority=20)
async def second_handler(request):
    print("Second")  # Runs second

@hooks.register("request.start", priority=5)
async def third_handler(request):
    print("Third")  # Runs first (lowest priority)
```

## One-Time Hooks

Auto-remove after first execution:

```python
@hooks.register("app.start", once=True)
async def startup_hook():
    print("Runs only once on startup")
```

## Async/Sync Support

Mix async and sync handlers:

```python
# Async handler
@hooks.register("request.start")
async def async_handler(request):
    await some_async_operation()

# Sync handler
@hooks.register("request.end")
def sync_handler(request, response):
    # Runs in thread pool
    some_sync_operation()
```

## Emission

### Async Emission

```python
# Emit hook and collect results
results = await hooks.emit("user.login", user=user)

# Check if any hook returned False to cancel
if False in results:
    # Hook cancelled the operation
    pass
```

### Sync Emission

```python
# Emit hook synchronously
results = hooks.emit_sync("user.login", user=user)
```

## Hook Cancellation

Return `False` to stop hook execution:

```python
@hooks.register("request.start", priority=1)
async def auth_check(request):
    if not request.headers.get("authorization"):
        return False  # Cancels subsequent hooks

@hooks.register("request.start", priority=2)
async def other_handler(request):
    # Won't run if auth_check returns False
    pass
```

## Clearing Hooks

```python
# Clear hooks for specific event
hooks.clear("request.start")

# Clear all hooks
hooks.clear()
```
