# Introduction

Welcome to **Fenrir**, a hybrid Python web framework that unifies the best patterns from Flask, FastAPI, Falcon, Sanic, and Bottle into a single, high-performance ASGI application. Fenrir v3.1.2 delivers 94 exported symbols across routing, dependency injection, middleware, security, sessions, and CLI tooling—eliminating the need to choose between paradigms.

---

## Core Philosophy

Fenrir embraces **Framework Hybridization**: rather than enforcing a single architectural style, it provides a polymorphic engine that natively executes code written in multiple paradigms. Teams with mixed Flask/FastAPI/Falcon experience can collaborate on the same application instance without friction. Legacy WSGI services can be mounted directly into the ASGI pipeline via built-in adapters for Bottle, Falcon, and Sanic.

---

## Architecture

Fenrir v3.1.2 is organized around two core modules and a trie-based router:

- **`_app_core.py`** — Application initialization, middleware registration, blueprint mounting, and lifecycle hooks.
- **`_app_dispatch.py`** — ASGI dispatch pipeline: request parsing, handler execution, response coercion, and error handling.
- **`routing.py`** — Trie-based `RouteTrie` for logarithmic-time path matching with type converters (`int`, `float`, `path`, `str`, and regex).

Synchronous handlers are automatically offloaded to a thread pool via `compat.to_thread`, preventing event-loop blocking. Asynchronous handlers are awaited directly.

---

## Five Pillars

### 1. Dependency Injection & Data Validation (FastAPI-style)
- **`Depends`**, **`Query`**, **`Header`**, **`Cookie`**, **`Body`**, **`Path`**, **`Form`**, **`File`** — Declare dependencies and parameters via type annotations; Fenrir parses, validates, and injects them automatically.
- **Automatic OpenAPI** — Pydantic models generate Swagger UI (`/docs`) and ReDoc (`/redoc`).

### 2. Context Locals & Templating (Flask-style)
- **`request`**, **`g`**, **`current_app`**, **`session`** — Thread-safe, async-safe context variables via `contextvars`.
- **`render_template`**, **`Jinja2Renderer`** — Pre-configured Jinja2 integration.
- **Teardown hooks** — `@app.teardown_request` for resource cleanup.

### 3. Class-Based Resources (Falcon-style)
- **`View`**, **`MethodView`** — Map URLs to classes with `on_get`, `on_post`, `on_put`, `on_delete` methods.
- Direct mutation of `req`/`resp` objects within resource methods.
- **`@before` / `@after`** hooks for per-resource middleware.

### 4. Async Lifecycle & Background Tasks (Sanic-style)
- **Lifecycle listeners** — `before_server_start`, `after_server_start`, `before_server_stop`, `after_server_stop`.
- **`BackgroundTasks`**, **`BackgroundTask`** — Schedule coroutines from handlers without blocking the request pipeline.
- **`EventSourceResponse`** — Server-Sent Events support.

### 5. WSGI Adapters (Bottle-style)
- **`Bottle`** — Built-in Bottle re-export.
- **`WsgiToAsgi`**, **`install_bottle_compat`**, **`install_falcon_compat`**, **`install_sanic_compat`** — Mount legacy WSGI apps under specific paths.

---

## Feature Overview

### Routing
- **`Router`**, **`Route`**, **`APIRouter`**, **`RouteTrie`** — Trie-based routing with Flask-style path converters (`<int:id>`, `<float:price>`, `<path:file>`) and regex support.
- **Blueprints** — Modular route grouping with prefix and middleware scoping.

### Middleware
| Middleware | Purpose |
|---|---|
| `CORSMiddleware` | Cross-Origin Resource Sharing headers |
| `GZipMiddleware` | Response compression |
| `RequestIDMiddleware` | Unique request ID injection |
| `RateLimitMiddleware` | Token-bucket rate limiting |
| `BodyLimitMiddleware` | Request body size caps |
| `CSRFMiddleware` | Cross-Site Request Forgery protection |

### Security & Authentication
Fenrir ships 10 authentication backends:

| Class | Mechanism |
|---|---|
| `APIKeyCookie` | API key via cookie |
| `APIKeyHeader` | API key via header |
| `APIKeyQuery` | API key via query parameter |
| `HTTPBasic` | HTTP Basic authentication |
| `HTTPBearer` | HTTP Bearer token |
| `HTTPDigest` | HTTP Digest authentication |
| `OAuth2PasswordBearer` | OAuth2 Resource Owner Password Credentials |
| `OAuth2AuthorizationCodeBearer` | OAuth2 Authorization Code flow |
| `OpenIDConnect` | OpenID Connect discovery |
| `WebSocketTokenAuth` | Token-based WebSocket authentication |

### Sessions
- **`SecureCookieSessionInterface`** — Signed cookie sessions (default).
- **`InMemorySessionInterface`** / **`InMemorySessionBackend`** — Server-side in-memory sessions with TTL cleanup.
- **`RedisSessionInterface`** — Server-side Redis-backed sessions.
- **`ServerSideSession`** — Base class for server-side session data.

### Connection Pooling
- **`ConnectionPool`** — Generic async connection pool with acquire/release semantics, validation, and stats.
- **`DatabasePool`** — Specialized pool with `execute_with_retry` for database connections.

### HTTP/2 Server Push
- **`HTTP2Push`** — Attach `Link` headers for HTTP/2 push promises (requires an HTTP/2-capable ASGI server).

### Pagination
- **`PaginationParams`** — Pydantic model for `page`/`size` query parameters.
- **`paginate`** / **`paginate_dict`** — Helpers that return `PaginatedResponse` with navigation links.

### Responses
`JSONResponse`, `HTMLResponse`, `TextResponse`, `PlainTextResponse`, `RedirectResponse`, `StreamingResponse`, `FileResponse`, `EventSourceResponse`.

### WebSocket Support
- **`WebSocket`**, **`WebSocketDisconnect`**, **`WebSocketTimeout`** — Full WebSocket lifecycle management.

### File Uploads
- **`UploadFile`** — Streaming file upload handling.

### Testing
- **`TestClient`**, **`FenrirTestClient`** — Synchronous test client for endpoint testing.

---

## CLI Tools

Fenrir provides a built-in CLI (`fenrir`):

| Command | Description |
|---|---|
| `fenrir run` | Start the development server with optional hot-reload |
| `fenrir routes` | Print all registered routes |
| `fenrir shell` | Interactive Python shell with app context |
| `fenrir bench` | Simple request benchmarking |
| `fenrir new` | Scaffold a new project from a template |
| `fenrir info` | Display app and environment information |
| `fenrir monitoring` | Enable, disable, or configure the monitoring dashboard |

---

## Getting Started

```bash
pip install fenrir-framework
```

Create `app.py`:

```python
from fenrir import Fenrir, Depends, Query

app = Fenrir()

async def verify_token(q: str = Query(...)):
    if q != "secret":
        from fenrir import HTTPUnauthorized
        raise HTTPUnauthorized("Invalid token")
    return True

@app.get("/")
async def index(authenticated: bool = Depends(verify_token)):
    return {"message": "Hello, Fenrir!"}
```

Run the server:

```bash
fenrir run app:app
```

Open `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

---

## Deployment

Fenrir pairs with the **Asteri** ASGI server for production deployment:

```bash
fenrir run app:app --workers 4
```

Asteri supports dynamic worker multiprocessing, hot-reloading, and advanced HTTP connection management. Fenrir is also compatible with Uvicorn, Hypercorn, and Daphne.

---

Explore the sidebar sections to learn about routing, data validation, middleware, background tasks, sessions, and deployment.