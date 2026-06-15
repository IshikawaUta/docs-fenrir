# Advanced Features

### WSGI Application Mounting

Mount legacy WSGI applications:

```python
from fenrir import Fenrir, WsgiToAsgi

app = Fenrir()

# Legacy WSGI app
def wsgi_app(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b'Hello from WSGI']

# Mount WSGI app
wsgi_asgi = WsgiToAsgi(wsgi_app)
app.mount_wsgi("/legacy", wsgi_asgi)
```

### Framework Compatibility Modes

#### Bottle Compatibility

```python
from fenrir import install_bottle_compat

install_bottle_compat()

# Now use Bottle-style features
from fenrir.bottle import Bottle
bottle_app = Bottle()
```

#### Falcon Compatibility

```python
from fenrir import install_falcon_compat

install_falcon_compat()

# Now use Falcon-style features
import fenrir.falcon as falcon
```

#### Sanic Compatibility

```python
from fenrir import install_sanic_compat

install_sanic_compat()

# Now use Sanic-style features
import fenrir.sanic as sanic
```

### Response Models

```python
from pydantic import BaseModel

class Item(BaseModel):
    id: int
    name: str
    price: float

@app.get("/items/<item_id:int>", response_model=Item)
async def get_item(item_id: int):
    return {"id": item_id, "name": "Item", "price": 9.99}
```

### Multiple Response Models per Status

Apply different response models based on the actual response status code:

```python
from pydantic import BaseModel

class SuccessResponse(BaseModel):
    id: int
    name: str

class ErrorResponse(BaseModel):
    detail: str
    code: int

@app.get(
    "/items/<item_id:int>",
    response_models={
        200: SuccessResponse,
        404: ErrorResponse
    }
)
async def get_item(item_id: int):
    if item_id < 0:
        return JSONResponse(
            status_code=404,
            content={"detail": "Item not found", "code": 404}
        )
    return {"id": item_id, "name": "Item"}
```

### Response Model Filtering

```python
class User(BaseModel):
    id: int
    name: str
    email: str
    password: str

@app.get(
    "/users/<user_id:int>",
    response_model=User,
    response_model_exclude={"password"}
)
async def get_user(user_id: int):
    return User(id=user_id, name="John", email="john@example.com", password="secret")
```

### Event Listeners

```python
@app.listener("before_server_start")
async def startup(app_instance):
    print("Server starting")

@app.listener("after_server_stop")
async def shutdown(app_instance):
    print("Server stopping")
```

### Connection Pooling

Built-in generic connection pooling for databases and external services:

```python
from fenrir.pool import ConnectionPool

# Create a connection pool
pool = ConnectionPool(
    create_func=lambda: create_engine("sqlite:///db.sqlite3"),
    close_func=lambda engine: engine.dispose(),
    min_size=2,
    max_size=10,
)

@app.get("/users")
async def list_users():
    async with pool.acquire() as conn:
        result = conn.execute("SELECT * FROM users")
        return {"users": [dict(row) for row in result]}
```

**Parameters:**

- `create_func`: Callable that creates a new connection
- `close_func`: Callable that closes a connection (optional)
- `min_size`: Minimum pool size (default: `1`)
- `max_size`: Maximum pool size (default: `10`)
- `max_idle_seconds`: Max idle time before recycling (default: `300`)
- `max_lifetime_seconds`: Max connection lifetime (default: `3600`)
- `health_check_interval`: Interval between health checks (default: `60`)
- `retry_attempts`: Number of retry attempts on failure (default: `3`)
- `retry_backoff`: Base backoff multiplier for retries (default: `0.5`)
- `validate_func`: Optional callable to validate a connection is still healthy; can be sync or async (default: `None`)

**ConnectionPool API:**

- `await pool.initialize()` — Initialize the pool and pre-fill with `min_size` connections. Called automatically on first `acquire()`.
- `await pool.acquire()` — Acquire a connection (async context manager). Returns a connection object.
- `await pool.close()` — Close all connections in the pool.
- `pool.stats` — Property returning a dict with `active`, `idle`, and `max_size` counts.

### DatabasePool

Extends `ConnectionPool` with built-in query retry logic:

```python
from fenrir.pool import DatabasePool

pool = DatabasePool(
    create_func=lambda: create_engine("sqlite:///db.sqlite3"),
    close_func=lambda engine: engine.dispose(),
    min_size=2,
    max_size=10,
)

async def get_user(user_id: int):
    result = await pool.execute_with_retry(
        lambda conn: conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": user_id})
    )
    return result.fetchone()
```

**DatabasePool API (in addition to ConnectionPool):**

- `await pool.execute_with_retry(func, *args, retries=None, **kwargs)` — Execute a function with automatic retry and exponential backoff. Acquires a connection, calls `func(conn, *args, **kwargs)`, and retries on failure. The `retries` parameter overrides the pool's `retry_attempts`.

### HTTP/2 Server Push

Proactively push resources to clients before they request them:

```python
from fenrir.http2 import HTTP2Push

push = HTTP2Push()

@app.get("/")
async def index():
    return push.push(
        "<html><link rel='stylesheet' href='/static/style.css'></html>",
        push_paths=["/static/style.css", "/static/app.js"],
    )
```

**Parameters:**

- `as_header`: If `True` (default), push promises are sent via `Link` headers. If `False`, the response body is returned as-is without headers.

**HTTP2Push API:**

- `push.push(content, push_paths=None)` — Return a `Response` with `Link` headers for HTTP/2 push promises. If `push_paths` is not provided, uses the paths added via `add_push_path()`. Content can be a string (wrapped as HTML), dict/list (wrapped as JSON), or a `Response` object.
- `push.add_push_path(path)` — Add a path to the auto-push list. Returns `self` for chaining.
- `push.clear_push_paths()` — Clear all auto-push paths. Returns `self` for chaining.
- `@push.auto_push(static_url="/static", paths=None)` — Decorator that automatically pushes static assets. `paths` is a list of file paths relative to `static_url` to push. If `paths` is `None`, no paths are pushed (use `add_push_path()` first).

**Chainable push path setup:**

```python
push = HTTP2Push()
push.add_push_path("/static/style.css").add_push_path("/static/app.js")

@app.get("/")
async def index():
    return push.push("<html>...</html>")
```

**Auto-push decorator:**

```python
@push.auto_push(static_url="/static", paths=["style.css", "app.js"])
async def index():
    return "<html>...</html>"
```

Note: HTTP/2 push requires the ASGI server to support HTTP/2 (e.g., Uvicorn with h2, Daphne, or Hypercorn). If the server does not support HTTP/2, push promises are silently ignored.

### Signals

Fenrir includes a signal system for event-driven communication between components. Signals are similar to Blinker's pattern.

#### signal() function

Get or create a named signal on the global signal bus:

```python
from fenrir.signals import signal

# Create or get a custom signal
my_signal = signal("my-custom-signal", doc="Fired when something happens")
```

#### Namespace class

A `Namespace` is a dict-like container for organizing signals. The global namespace is exposed as `signal_bus`:

```python
from fenrir.signals import signal_bus

# Create a signal within the namespace
custom_signal = signal_bus.signal("my-event")
```

#### Signal API

```python
from fenrir.signals import signal

my_signal = signal("my-event")

# Connect a receiver
@my_signal.connect
def handle_event(sender, **kwargs):
    print(f"Received from {sender}: {kwargs}")

# Connect with sender filter
@my_signal.connect(sender=specific_object)
def handle_specific(sender, **kwargs):
    print("Only fires for specific_object")

# Disconnect a receiver
my_signal.disconnect(handle_event)

# Send a signal (synchronous receivers are called immediately)
results = my_signal.send(sender="some_sender", data="hello")
```

#### Built-in signals

- `request_started` — Fired before a request is processed.
- `request_finished` — Fired after a response is prepared.
- `got_request_exception` — Fired when an exception occurs during request handling.
- `template_rendered` — Fired after a template is rendered.

```python
from fenrir.signals import request_started, request_finished

@request_started.connect
def on_request_start(sender, **kwargs):
    print("Request started")

@request_finished.connect
def on_request_end(sender, **kwargs):
    print("Request finished")
```

#### Async signal receivers

Async receivers are automatically scheduled as background tasks when the signal is sent. If no event loop is running, async receivers are skipped with a debug log.

```python
@my_signal.connect
async def async_handler(sender, **kwargs):
    await some_async_work(sender)
```

### AppContext and RequestContext

Context managers for accessing application and request-level data outside of request handling.

#### AppContext

Sets the current application context. Use `current_app` proxy to access it:

```python
from fenrir.context import current_app

with app.app_context():
    print(current_app.title)
```

On exit, `do_teardown_appcontext()` is called, running all registered teardown functions.

#### RequestContext

Sets both the application and request context. Use `request` and `g` proxies to access them:

```python
from fenrir.context import request, g

with app.test_request_context("/users", method="GET"):
    print(request.method)  # "GET"
    g.user_id = 42
```

**Global proxies:**

- `request` — The current request object (available inside `RequestContext`)
- `g` — A namespace for storing per-request temporary data
- `current_app` — The current application object (available inside `AppContext`)
- `session` — The session object (available inside `RequestContext`)

### Testing Utilities

#### app.test_client()

Create a test client for making requests without running a server:

```python
client = app.test_client()

# Make GET request
response = client.get("/users")
print(response.status_code, response.text)

# Make POST request
response = client.post("/users", json={"name": "John"})
```

#### app.test_request_context()

Create a request context for testing code that accesses `request` or `g`:

```python
with app.test_request_context("/users/1", method="GET", headers={"Authorization": "Bearer token"}):
    from fenrir.context import request
    print(request.method)   # "GET"
    print(request.path)     # "/users/1"
```

### OpenAPI Schema Generation

Generate an OpenAPI 3.0.3 schema from your registered routes:

```python
schema = app.openapi()
# Returns a dict with "openapi", "info", "paths", and "components" keys
```

The schema is automatically cached and invalidated when routes are added. Built-in endpoints are served at the configured URLs:

- `openapi_url` (default: `/openapi.json`) — The raw schema
- `docs_url` (default: `/docs`) — Swagger UI
- `redoc_url` (default: `/redoc`) — ReDoc

```python
app = Fenrir(openapi_url="/api/schema", docs_url="/api/docs", redoc_url="/api/redoc")
```

### Background Tasks

Schedule coroutines to run in the background:

```python
task = app.add_task(send_email, to="user@example.com")

# Also works with coroutine objects
task = app.add_task(some_coroutine())
```

`add_task()` accepts either a coroutine function (which is automatically called) or an already-created coroutine object. Returns an `asyncio.Task`.

### Error Handlers

Register custom error handlers for exceptions or HTTP status codes:

```python
@app.exception(404)
async def not_found(req, exc):
    return JSONResponse({"error": "Not found"}, status_code=404)

@app.exception(ValueError, TypeError)
async def handle_value_error(req, exc):
    return JSONResponse({"error": str(exc)}, status_code=400)

@app.exception(500)
async def server_error(req, exc):
    return JSONResponse({"error": "Internal server error"}, status_code=500)
```

Handlers can be registered for multiple exceptions or status codes in a single decorator call.

### App Context Teardown

Register functions to run when the application context is torn down:

```python
@app.teardown_appcontext
def cleanup(exc):
    if exc:
        print(f"Context ended with error: {exc}")
    else:
        print("Context ended normally")
```

Teardown functions are called in reverse order of registration. They receive the exception (if any) as an argument. This is useful for releasing resources like database connections or file handles.
