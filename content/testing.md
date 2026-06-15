# Testing

Fenrir provides an async `TestClient` based on `httpx` for testing your application, along with helper methods for manual context testing.

## Quick Start

```python
import pytest
from fenrir import Fenrir
from fenrir.testing import TestClient

app = Fenrir()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@pytest.mark.asyncio
async def test_read_root():
    async with TestClient(app) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}
```

## Creating a TestClient

### Direct Import

```python
from fenrir.testing import TestClient

async with TestClient(app) as client:
    response = await client.get("/")
```

### Via `app.test_client()`

```python
async with app.test_client() as client:
    response = await client.get("/")
```

Both forms are equivalent. The `test_client()` method returns a `FenrirTestClient` instance.

## HTTP Methods

The `TestClient` supports all standard HTTP methods:

```python
async with TestClient(app) as client:
    # GET
    response = await client.get("/items")

    # POST
    response = await client.post("/items", json={"name": "Widget"})

    # PUT
    response = await client.put("/items/1", json={"name": "Updated Widget"})

    # DELETE
    response = await client.delete("/items/1")

    # PATCH
    response = await client.patch("/items/1", json={"name": "Patched Widget"})

    # OPTIONS
    response = await client.options("/items")

    # HEAD
    response = await client.head("/items")

    # Generic request
    response = await client.request("GET", "/items")
```

## Request Parameters

### JSON Body

```python
response = await client.post("/items", json={"name": "Widget", "price": 9.99})
```

### Form Data

```python
response = await client.post("/login", data={"username": "admin", "password": "secret"})
```

### Raw Content

```python
response = await client.post(
    "/webhook",
    content=b"<raw binary data>",
    headers={"Content-Type": "application/octet-stream"}
)
```

### Query Parameters

```python
response = await client.get("/search", params={"q": "fenrir", "page": 1})
```

### Custom Headers

```python
response = await client.get("/protected", headers={"Authorization": "Bearer token123"})
```

### File Uploads

```python
# Single file
with open("test.txt", "rb") as f:
    response = await client.post("/upload", files={"file": f})

# Multiple files
with open("photo.jpg", "rb") as img, open("doc.pdf", "rb") as doc:
    response = await client.post(
        "/upload",
        files=[
            ("images", ("photo.jpg", img, "image/jpeg")),
            ("documents", ("doc.pdf", doc, "application/pdf")),
        ]
    )
```

### Combining Parameters

```python
response = await client.post(
    "/items",
    json={"name": "Widget"},
    headers={"X-Request-ID": "abc-123"},
    params={"version": "v2"}
)
```

## Pytest Fixtures

### Async Fixture

```python
import pytest
from fenrir.testing import TestClient
from app import app

@pytest.fixture
async def client():
    async with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_get_user(client):
    response = await client.get("/users/1")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_create_user(client):
    response = await client.post(
        "/users",
        json={"name": "John", "email": "john@example.com"}
    )
    assert response.status_code == 201
    assert response.json()["id"]
```

### Sync Fixture with `anyio`

If you prefer synchronous tests, use `anyio` to run async code:

```python
import pytest
from anyio import from_thread
from fenrir.testing import TestClient
from app import app

@pytest.fixture
def client():
    with from_thread.run(TestClient(app).__aenter__) as c:
        yield c

def test_get_user(client):
    response = from_thread.run(client.get, "/users/1")
    assert response.status_code == 200
```

## Dependency Overrides

Override dependencies during testing to mock external services:

```python
from fenrir import Depends

# Production dependency
async def get_db():
    db = await create_real_connection()
    try:
        yield db
    finally:
        await db.close()

# Test mock
async def override_get_db():
    yield {"connection": "mock"}

# Test setup
app.dependency_overrides[get_db] = override_get_db

@pytest.mark.asyncio
async def test_with_mock_db(client):
    response = await client.get("/users")
    assert response.status_code == 200

# Cleanup
app.dependency_overrides.clear()
```

## Manual Context Testing

For unit-testing functions that depend on request context without making HTTP requests, use `app.test_request_context()`:

```python
from app import app

def test_my_function():
    with app.test_request_context("/users", method="GET") as ctx:
        from fenrir.context import request
        # `request` is now available inside the context
        assert request.path == "/users"
        assert request.method == "GET"
```

### With Headers and Query String

```python
def test_auth_endpoint():
    with app.test_request_context(
        "/profile",
        method="GET",
        headers={"Authorization": "Bearer token123"},
        query_string=b"verbose=true"
    ):
        from fenrir.context import request
        # Access request properties
        assert request.path == "/profile"
```

## Testing Async Handlers

All handler tests are async by default with `@pytest.mark.asyncio`:

```python
import pytest
from fenrir import Fenrir
from fenrir.testing import TestClient

app = Fenrir()

@app.get("/slow")
async def slow_endpoint():
    import asyncio
    await asyncio.sleep(0.1)
    return {"done": True}

@pytest.mark.asyncio
async def test_async_handler():
    async with TestClient(app) as client:
        response = await client.get("/slow")
        assert response.status_code == 200
        assert response.json()["done"] is True
```

## Testing Middleware

### Request/Response Middleware (Decorator)

```python
from fenrir import Fenrir
from fenrir.testing import TestClient

app = Fenrir()

@app.middleware("request")
async def add_start_time(request):
    import time
    request.start_time = time.time()

@app.middleware("response")
async def add_server_header(request, response):
    response.headers["X-Server"] = "Fenrir"

@app.get("/items")
async def list_items():
    return [{"id": 1}]

@pytest.mark.asyncio
async def test_middleware():
    async with TestClient(app) as client:
        response = await client.get("/items")
        assert response.status_code == 200
        assert response.headers["x-server"] == "Fenrir"
```

### ASGI Middleware (Built-in)

```python
from fenrir import Fenrir
from fenrir.middleware import CORSMiddleware, RequestIDMiddleware
from fenrir.testing import TestClient

app = Fenrir()
app.add_middleware(CORSMiddleware, allow_origins=["https://example.com"])
app.add_middleware(RequestIDMiddleware)

@app.get("/items")
async def list_items():
    return [{"id": 1}]

@pytest.mark.asyncio
async def test_cors_and_request_id():
    async with TestClient(app) as client:
        # Test CORS preflight
        response = await client.options(
            "/items",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.headers.get("access-control-allow-origin") == "https://example.com"

        # Test Request ID
        response = await client.get("/items")
        assert "x-request-id" in response.headers
```

## Testing Error Handlers

Register custom error handlers and verify they respond correctly:

```python
from fenrir import Fenrir
from fenrir import HTTPNotFound
from fenrir.testing import TestClient

app = Fenrir()

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    if user_id == 0:
        raise HTTPNotFound(detail="User not found")
    return {"id": user_id, "name": "Test User"}

@app.register_error_handler(404)
async def custom_404(request, exc):
    return {"error": "custom", "detail": exc.detail}, 404

@pytest.mark.asyncio
async def test_not_found():
    async with TestClient(app) as client:
        response = await client.get("/users/0")
        assert response.status_code == 404
        assert response.json()["error"] == "custom"

@pytest.mark.asyncio
async def test_not_found_by_exception_class():
    """Error handlers can also be keyed by exception class."""
    @app.register_error_handler(HTTPNotFound)
    async def handle_not_found(request, exc):
        return {"error": "not_found", "detail": exc.detail}, 404

    async with TestClient(app) as client:
        response = await client.get("/users/0")
        assert response.status_code == 404
```

## Testing WebSocket Connections

Fenrir supports WebSocket endpoints. Test them using raw ASGI scope with `httpx.ASGITransport`:

```python
import pytest
from fenrir import Fenrir
from fenrir.websocket import WebSocket

app = Fenrir()

@app.websocket("/ws")
async def echo(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except Exception:
        await websocket.close()

@pytest.mark.asyncio
async def test_websocket_echo():
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        async with client.stream("GET", "/ws") as stream:
            # WebSocket testing requires ASGI-level tools
            # For basic endpoint verification, use httpx's WebSocket support
            pass
```

For more robust WebSocket testing, mock the WebSocket protocol or use a dedicated test utility:

```python
import pytest
from unittest.mock import AsyncMock
from fenrir import Fenrir
from fenrir.testing import TestClient

app = Fenrir()

@app.websocket("/ws/echo")
async def ws_echo(websocket):
    await websocket.accept()
    data = await websocket.receive_text()
    await websocket.send_text(f"Echo: {data}")
    await websocket.close()

@pytest.mark.asyncio
async def test_websocket_handler_directly():
    """Test WebSocket handler logic by mocking the protocol."""
    from fenrir.websocket import WebSocket

    messages_sent = []

    async def mock_receive():
        return {"type": "websocket.receive", "text": "hello"}

    async def mock_send(message):
        messages_sent.append(message)

    scope = {
        "type": "websocket",
        "path": "/ws/echo",
        "headers": [],
    }

    ws = WebSocket(scope, mock_receive, mock_send)
    await ws.accept()

    data = await ws.receive_text()
    assert data == "hello"

    await ws.send_text(f"Echo: {data}")
    assert messages_sent[-1] == {"type": "websocket.send", "text": "Echo: hello"}

    await ws.close()
    assert messages_sent[-1]["type"] == "websocket.close"
```

## Complete Example

```python
import pytest
from fenrir import Fenrir, Depends
from fenrir.testing import TestClient
from fenrir.middleware import CORSMiddleware

app = Fenrir()

# --- Setup ---

async def get_db():
    yield {"connection": "real"}

async def override_get_db():
    yield {"connection": "mock"}

app.dependency_overrides[get_db] = override_get_db
app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.get("/users")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

@app.post("/users")
async def create_user(data: dict):
    return {"id": 2, **data}, 201

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    if user_id == 0:
        from fenrir import HTTPNotFound
        raise HTTPNotFound("User not found")
    return {"id": user_id, "name": "Alice"}

# --- Fixtures ---

@pytest.fixture
async def client():
    async with TestClient(app) as c:
        yield c

# --- Tests ---

@pytest.mark.asyncio
async def test_list_users(client):
    response = await client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) == 1

@pytest.mark.asyncio
async def test_create_user(client):
    response = await client.post("/users", json={"name": "Bob"})
    assert response.status_code == 201
    assert response.json()["name"] == "Bob"

@pytest.mark.asyncio
async def test_get_user(client):
    response = await client.get("/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1

@pytest.mark.asyncio
async def test_user_not_found(client):
    response = await client.get("/users/0")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_cors_headers(client):
    response = await client.get("/users")
    assert response.headers.get("access-control-allow-origin") == "*"
```
