# Best Practices

This guide outlines recommended patterns for building production-ready Fenrir v4.0.0 applications.

---

## 1. Dependency Injection for Reusable Logic

Use `Depends` to encapsulate reusable logic like database sessions, authentication, and validation. Dependencies are automatically resolved and cached per request.

```python
from fenrir import Fenrir, Depends, Header

app = Fenrir()

async def get_db():
    db = await create_database_connection()
    try:
        yield db
    finally:
        await db.close()

async def get_current_user(
    db = Depends(get_db),
    authorization: str = Header(default=None),
):
    if not authorization:
        raise HTTPUnauthorized(detail="Missing token")
    return await db.get_user_by_token(authorization)

@app.get("/profile")
async def get_profile(user = Depends(get_current_user)):
    return {"name": user.name}
```

**Benefits:**

- Single responsibility: each dependency handles one concern
- Automatic caching: same dependency is resolved once per request
- Composable: dependencies can depend on other dependencies

---

## 2. Yield Dependencies for Cleanup

Use generator-based dependencies to ensure resources are properly cleaned up after the request, even if an exception occurs.

```python
async def get_database_session():
    session = await create_session()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

@app.post("/users")
async def create_user(
    data: UserCreate,
    session = Depends(get_database_session),
):
    user = User(**data.dict())
    session.add(user)
    await session.commit()
    return {"id": user.id}
```

**Key points:**

- Use `try/finally` to guarantee cleanup
- Handle exceptions before cleanup if needed (e.g., rollback)
- Both sync and async generators are supported

---

## 3. Use `dependency_overrides` for Testing

Replace real dependencies with mocks during testing without modifying application code.

```python
import pytest
from fenrir import Fenrir, Depends
from fenrir.testing import TestClient

app = Fenrir()

async def get_db():
    db = await create_real_connection()
    try:
        yield db
    finally:
        await db.close()

async def override_get_db():
    yield {"connection": "test-mock", "query": lambda sql: []}

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
async def client():
    async with TestClient(app) as c:
        yield c

@pytest.mark.asyncio
async def test_get_users(client):
    response = await client.get("/users")
    assert response.status_code == 200

# Cleanup after tests
app.dependency_overrides.clear()
```

**Best practices:**

- Clear overrides after each test or test suite
- Override multiple dependencies at once when needed
- Use `app.dependency_overrides = {dep1: mock1, dep2: mock2}` for batch overrides

---

## 4. Use `APIRouter` for Modular Code Organization

Group related routes into reusable routers with optional URL prefixes.

```python
from fenrir import Fenrir, APIRouter

app = Fenrir()
users_router = APIRouter()
products_router = APIRouter()

@users_router.get("")
async def list_users():
    return [{"id": 1, "name": "User 1"}]

@users_router.post("")
async def create_user():
    return {"id": 2, "name": "New User"}

@products_router.get("")
async def list_products():
    return [{"id": 1, "name": "Product 1"}]

app.include_router(users_router, prefix="/api/users")
app.include_router(products_router, prefix="/api/products")
```

**Advantages:**

- Clean separation of concerns
- Reusable across multiple applications
- Supports circular inclusion detection
- Can include other routers for nested structures

---

## 5. Use Blueprints for Large Applications

Blueprints provide modular organization with middleware scoping and lifecycle hooks.

```python
from fenrir import Blueprint, Fenrir

api_bp = Blueprint("api", url_prefix="/api")

@api_bp.before_request
async def check_api_key():
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPUnauthorized()

@api_bp.get("/data")
async def get_data():
    return {"data": "protected"}

app = Fenrir()
app.register_blueprint(api_bp)
```

**Blueprint vs APIRouter:**

- **Blueprints**: Include middleware, lifecycle hooks, and template registration
- **APIRouter**: Lightweight route grouping without middleware support

---

## 6. Use `BackgroundTasks` for Non-Blocking Operations

Schedule tasks to run after the response is sent without blocking the request.

```python
from fenrir import Fenrir, BackgroundTasks

app = Fenrir()

def send_email(to: str, subject: str, body: str):
    # Send email logic (runs in background)
    print(f"Sending email to {to}")

@app.post("/notify")
async def notify(background_tasks: BackgroundTasks):
    background_tasks.add_task(
        send_email,
        to="user@example.com",
        subject="Hello",
        body="World"
    )
    return {"status": "queued"}

# Also works with async functions
async def process_data(data_id: int):
    await asyncio.sleep(2)
    print(f"Processed data {data_id}")

@app.post("/process")
async def process(background_tasks: BackgroundTasks):
    background_tasks.add_task(process_data, data_id=42)
    return {"status": "processing"}
```

**Use cases:**

- Sending emails or notifications
- Logging analytics
- File processing
- Cache invalidation

---

## 7. Use `ConnectionPool` for Database Connections

Manage database connections efficiently with built-in pooling, health checks, and retry logic.

```python
from fenrir import Fenrir
from fenrir.pool import ConnectionPool, DatabasePool

app = Fenrir()

# Generic connection pool
pool = ConnectionPool(
    create_func=lambda: create_engine("postgresql://localhost/mydb"),
    close_func=lambda engine: engine.dispose(),
    min_size=2,
    max_size=10,
    max_idle_seconds=300,
    health_check_interval=60,
    retry_attempts=3,
)

# Database-specific pool with query retry
db_pool = DatabasePool(
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

# With retry logic
@app.get("/users/<user_id:int>")
async def get_user(user_id: int):
    result = await db_pool.execute_with_retry(
        lambda conn: conn.execute(
            text("SELECT * FROM users WHERE id = :id"),
            {"id": user_id}
        )
    )
    return result.fetchone()
```

**Pool configuration:**

- `min_size`: Minimum connections to keep ready
- `max_size`: Maximum concurrent connections
- `health_check_interval`: Seconds between connection health checks
- `retry_attempts`: Number of retries on connection failure

---

## 8. Use Middleware for Cross-Cutting Concerns

Apply CORS, rate limiting, compression, and other cross-cutting concerns via middleware.

```python
from fenrir import Fenrir
from fenrir.middleware import (
    CORSMiddleware,
    RateLimitMiddleware,
    GZipMiddleware,
    BodyLimitMiddleware,
    RequestIDMiddleware,
)

app = Fenrir()

# Add middleware in order (outermost first)
app.add_middleware(CORSMiddleware, allow_origins=["https://example.com"])
app.add_middleware(BodyLimitMiddleware, max_content_length=1_048_576)  # 1MB
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)
app.add_middleware(RequestIDMiddleware)
```

**Middleware execution order:**

1. `CORSMiddleware` — Handle CORS preflight
2. `BodyLimitMiddleware` — Reject oversized payloads
3. `RateLimitMiddleware` — Rate limit before processing
4. `GZipMiddleware` — Compress responses
5. `RequestIDMiddleware` — Add request IDs for tracing

---

## 9. Use Context Locals Appropriately

Use `request`, `g`, and `session` for request-scoped data, but understand their lifecycle.

```python
from fenrir import request, g, session

@app.before_request
async def load_user():
    token = request.headers.get("authorization")
    g.user = await db.get_user_by_token(token)

@app.get("/profile")
async def get_profile():
    # Access user loaded in before_request
    return {"user": g.user.name}

@app.get("/login")
async def login():
    # Store data in session
    session["user_id"] = 123
    return {"status": "logged in"}

@app.get("/dashboard")
async def dashboard():
    # Access session data
    user_id = session.get("user_id")
    if not user_id:
        return {"error": "not logged in"}, 401
    return {"user_id": user_id}
```

**Key rules:**

- `g` is reset per request — don't store data across requests
- `session` persists across requests (cookie or server-side)
- `request` is only available during request handling
- Use `current_app` to access app configuration outside requests

---

## 10. Use Async Handlers for I/O-Bound Operations

Prefer async handlers for operations that involve I/O (database queries, HTTP calls, file operations).

```python
import aiohttp

@app.get("/external-data")
async def fetch_external_data():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/data") as resp:
            data = await resp.json()
            return data

@app.get("/users")
async def list_users():
    # Async database query
    users = await db.fetch_all("SELECT * FROM users")
    return {"users": users}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Async file write
    content = await file.read()
    await async_write_file(f"uploads/{file.filename}", content)
    return {"filename": file.filename}
```

**When to use async:**

- Database queries
- HTTP client requests
- File I/O operations
- WebSocket communication
- Any operation that can yield control

---

## 11. Use Sync Handlers for CPU-Bound Operations

Fenrir automatically offloads sync handlers to a thread pool, preventing event-loop blocking.

```python
import time
import hashlib

def heavy_computation(data: str) -> str:
    """CPU-intensive operation that blocks the event loop."""
    # Simulate heavy computation
    result = hashlib.sha256(data.encode()).hexdigest()
    time.sleep(0.1)  # Simulate work
    return result

@app.post("/process")
def process_data(data: dict):
    # This runs in a thread pool automatically
    result = heavy_computation(str(data))
    return {"result": result}

def parse_large_file(file_path: str) -> list:
    """Synchronous file parsing."""
    with open(file_path, "r") as f:
        return [line.strip() for line in f.readlines()]

@app.get("/parse")
def parse_file():
    data = parse_large_file("large_file.txt")
    return {"lines": len(data)}
```

**When to use sync:**

- CPU-intensive computations
- Synchronous library calls
- File operations without async alternatives
- Legacy code that cannot be refactored to async

**Important:** Sync handlers lose access to `contextvars` by default. If you need `session` or other context-local data, pass them as parameters.

---

## 12. Use `response_model` for Automatic Serialization

Define response schemas with Pydantic models for automatic validation and documentation.

```python
from pydantic import BaseModel
from typing import List

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int

@app.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users",
    description="Retrieve a paginated list of users"
)
async def list_users():
    users = await db.fetch_all("SELECT * FROM users")
    return {"users": users, "total": len(users)}

# Exclude sensitive fields
class UserSecure(BaseModel):
    id: int
    name: str
    email: str
    password: str

@app.get(
    "/users/<user_id:int>",
    response_model=UserSecure,
    response_model_exclude={"password"}
)
async def get_user(user_id: int):
    user = await db.get_user(user_id)
    return user
```

**Benefits:**

- Automatic response validation
- OpenAPI documentation generation
- Field filtering with `include`/`exclude`
- Multiple response models per status code

---

## 13. Use Exception Handlers for Custom Error Pages

Register custom error handlers for consistent error responses across your application.

```python
from fenrir import Fenrir, JSONResponse, render_template

app = Fenrir()

@app.exception(404)
async def page_not_found(req, exc):
    return render_template("404.html", detail=exc.detail), 404

@app.exception(500)
async def server_error(req, exc):
    return render_template("500.html", detail="Internal error"), 500

# Custom exception classes
class DatabaseError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class AuthenticationError(Exception):
    def __init__(self, detail: str):
        self.detail = detail

@app.exception(DatabaseError)
async def handle_db_error(req, exc):
    return JSONResponse(
        {"error": "Database error", "detail": exc.detail},
        status=500
    )

@app.exception(AuthenticationError)
async def handle_auth_error(req, exc):
    return JSONResponse(
        {"error": "Authentication failed", "detail": exc.detail},
        status=401
    )

@app.get("/data")
async def get_data():
    try:
        data = await db.fetch_data()
    except DatabaseError as e:
        raise  # Will be caught by handler
    return data
```

**Handler resolution order:**

1. Status code handlers (e.g., `404`)
2. Exception class handlers (e.g., `HTTPNotFound`)
3. Default fallback

---

## 14. Use Signals for Cross-Cutting Logging

Implement event-driven logging and monitoring with signals.

```python
from fenrir import Fenrir
from fenrir.signals import (
    signal,
    request_started,
    request_finished,
    got_request_exception,
)

app = Fenrir()

# Custom signals
user_created = signal("user-created")
order_completed = signal("order-completed")

# Built-in signal: request logging
@request_started.connect
def log_request_start(sender, **kwargs):
    print(f"Request started: {request.method} {request.path}")

@request_finished.connect
def log_request_end(sender, response=None, **kwargs):
    status = response.status if response else "unknown"
    print(f"Request finished with status {status}")

@got_request_exception.connect
def log_exception(sender, exception=None, **kwargs):
    print(f"Exception occurred: {exception}")

# Custom signal: audit logging
@user_created.connect
def audit_user_creation(sender, user_id=None, **kwargs):
    print(f"User created: {user_id}")
    # Send to external audit system

@app.post("/users")
async def create_user(data: UserCreate):
    user = await db.create_user(data)
    user_created.send(sender=None, user_id=user.id)
    return {"id": user.id}

# Async receivers are automatically supported
@order_completed.connect
async def send_confirmation_email(sender, order_id=None, **kwargs):
    await send_email(f"Order {order_id} completed")
```

**Use cases:**

- Request/response logging
- Audit trails
- Metrics collection
- Cache invalidation
- Real-time notifications

---

## Summary

| Practice | When to Use |
|----------|-------------|
| **Dependency Injection** | Reusable logic (DB, auth, validation) |
| **Yield Dependencies** | Resource cleanup (connections, files) |
| **dependency_overrides** | Testing with mocked dependencies |
| **APIRouter** | Route organization without middleware |
| **Blueprints** | Modular apps with middleware/hooks |
| **BackgroundTasks** | Non-blocking operations (email, logging) |
| **ConnectionPool** | Database connection management |
| **Middleware** | Cross-cutting concerns (CORS, rate limiting) |
| **Context Locals** | Request-scoped data (g, session) |
| **Async Handlers** | I/O-bound operations |
| **Sync Handlers** | CPU-bound operations |
| **response_model** | Automatic serialization & docs |
| **Exception Handlers** | Custom error pages |
| **Signals** | Event-driven logging & monitoring |
