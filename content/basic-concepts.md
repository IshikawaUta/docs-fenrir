# Basic Concepts

### Fenrir Application

```python
from fenrir import Fenrir

app = Fenrir(
    title="My Application",
    version="4.1.2",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
```

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `import_name` | `str` | `None` | Import name for root path detection (auto-detected from caller) |
| `title` | `str` | `"Fenrir API"` | Application title (shown in OpenAPI docs) |
| `version` | `str` | `"4.1.2"` | Application version |
| `docs_url` | `str` | `"/docs"` | Swagger UI endpoint path (`None` to disable) |
| `redoc_url` | `str` | `"/redoc"` | ReDoc endpoint path (`None` to disable) |
| `openapi_url` | `str` | `"/openapi.json"` | OpenAPI schema endpoint path (`None` to disable) |
| `template_folder` | `str` | `"templates"` | Template directory name |
| `renderer` | `BaseTemplateRenderer` | `None` | Custom template renderer (default: Jinja2) |
| `root_path` | `str` | `None` | ASGI root path for reverse proxies (auto-detected) |
| `instance_path` | `str` | `None` | Path to instance folder (default: `root_path/instance`) |
| `instance_relative_config` | `bool` | `False` | Whether config is loaded relative to instance_path |
| `strict_content_type` | `bool` | `False` | Require `application/json` content-type for JSON bodies |
| `route_class` | `Type[Route]` | `None` | Custom route class for the router |
| `dev_mode` | `bool` | `None` | Enable debug pages with stack traces (auto-enabled from `FENRIR_DEV_MODE=1` env var) |

```python
app = Fenrir(
    title="My API",
    version="1.0.0",
    strict_content_type=True,    # Require application/json
    instance_path="/var/myapp",  # Custom instance folder
)
```

### App Attributes

```python
app.title                     # str — app title
app.version                   # str — app version
app.config                    # Config — configuration object
app.json                      # DefaultJSONProvider — JSON serializer
app.renderer                  # Jinja2Renderer — template renderer
app.session_interface         # SessionInterface — session backend
app.router                    # Router — route registration system
app.root_path                 # str — resolved root path
app.instance_path             # str — instance directory path
app.template_folder           # str — templates directory name
app.docs_url                  # str — Swagger UI endpoint
app.redoc_url                 # str — ReDoc endpoint
app.openapi_url               # str — OpenAPI schema endpoint
app.strict_content_type       # bool — require JSON content-type
app.blueprints                # List[Blueprint] — registered blueprints
app.exception_handlers        # Dict — registered error handlers
app.listeners                 # Dict — lifecycle event listeners
app.teardown_request_funcs    # Dict — request teardown functions
app.teardown_appcontext_funcs # List — app-context teardown functions
app.dependency_overrides      # Dict — DI overrides for testing
```

```python
# Debug mode (enables debug pages with stack traces)
app = Fenrir(dev_mode=True)
# Or via environment variable: FENRIR_DEV_MODE=1

# Configuration
app.config["DEBUG"] = True
app.config["SECRET_KEY"] = "my-secret"
app.config["DATABASE_URL"] = "postgresql://localhost/mydb"

# Custom JSON serialization (uses orjson when available)
from fenrir.json import json_dumps, json_loads
data = json_dumps({"key": "value"})  # 7x faster with orjson
```

### App Methods

```python
# Routing
app.route(path, methods=None, **kwargs)          # Decorator for routes
app.get(path, **kwargs)                          # GET route
app.post(path, **kwargs)                         # POST route
app.put(path, **kwargs)                          # PUT route
app.delete(path, **kwargs)                       # DELETE route
app.patch(path, **kwargs)                        # PATCH route
app.add_route(path, handler, methods=None)       # Programmatic route
app.add_websocket_route(path, handler)           # WebSocket route
app.include_router(router, prefix="")            # Include APIRouter
app.websocket(path, timeout=None)                # WebSocket decorator

# Middleware
app.add_middleware(middleware_class, **options)   # Add ASGI middleware
app.before_request(f)                            # Request middleware
app.after_request(f)                             # Response middleware
app.middleware(middleware_type)                   # Middleware decorator

# Blueprints
app.register_blueprint(blueprint)                # Register a Blueprint

# Error handlers
app.exception(*exceptions)                       # Error handler decorator
app.register_error_handler(exc_class, handler)   # Programmatic error handler

# Lifecycle
app.listener(event_name)                         # Lifecycle listener
app.teardown_request(f)                          # Request teardown
app.teardown_appcontext(f)                       # App-context teardown
app.add_task(coro)                               # Schedule async task

# WSGI
app.mount_wsgi(path, wsgi_app)                   # Mount WSGI app

# OpenAPI
app.openapi()                                    # Generate OpenAPI schema

# Testing
app.test_client()                                # Create test client
app.test_request_context(*args, **kwargs)        # Create test request context
app.app_context()                                # Create app context
```

### HTTP Methods

Fenrir supports all standard HTTP methods:

```python
@app.get("/path")
async def get_handler():
    pass

@app.post("/path")
async def post_handler():
    pass

@app.put("/path")
async def put_handler():
    pass

@app.delete("/path")
async def delete_handler():
    pass

@app.patch("/path")
async def patch_handler():
    pass
```

**Automatic methods:**

- `HEAD` is automatically added for any route that supports `GET` (RFC 7231)
- `OPTIONS` is automatically added for all routes (CORS support)

### Multi-Method Routes

```python
@app.route("/resource", methods=["GET", "POST"])
async def resource():
    return {"message": "Resource"}
```

### Adding Middleware

```python
from fenrir import CORSMiddleware, GZipMiddleware

# ASGI middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(GZipMiddleware, minimum_size=500)

# Request/Response middleware
@app.before_request
async def log_request():
    print(f"Request: {request.method} {request.path}")

@app.after_request
async def add_headers(response):
    response.headers["X-Custom"] = "value"
    return response
```

### Adding Routes Programmatically

```python
# Function-based route
app.add_route("/users", list_users)

# Class-based resource
app.add_route("/items/<item_id:int>", ItemResource())

# WebSocket route
app.add_websocket_route("/ws", websocket_handler)

# APIRouter
from fenrir import APIRouter

router = APIRouter()

@router.get("/users")
async def list_users():
    return [{"id": 1}]

app.include_router(router, prefix="/api/v1")
```

### Blueprints

```python
from fenrir import Blueprint

api_bp = Blueprint("api", url_prefix="/api")

@api_bp.get("/items")
async def list_items():
    return [{"id": 1}]

@api_bp.before_request
async def check_auth():
    if not request.headers.get("Authorization"):
        raise HTTPUnauthorized()

app.register_blueprint(api_bp)
```

### Lifecycle Listeners

```python
@app.listener("before_server_start")
async def on_startup(app_instance):
    print("Server starting")
    # Initialize database pool, etc.

@app.listener("after_server_start")
async def on_after_startup(app_instance):
    print("Server started")

@app.listener("before_server_stop")
async def on_before_stop(app_instance):
    print("Server stopping")

@app.listener("after_server_stop")
async def on_shutdown(app_instance):
    print("Server stopped")
```

### Exception Handlers

```python
from fenrir import HTTPNotFound, HTTPException

@app.exception(404)
async def not_found(req, exc):
    return {"error": "Not found"}, 404

@app.exception(HTTPException)
async def handle_http(req, exc):
    return {"error": exc.detail}, exc.status_code

@app.exception(500, 502, 503)
async def server_errors(req, exc):
    return {"error": "Server error"}, 500
```

### Dependency Injection

```python
from fenrir import Depends

async def get_db():
    db = await create_connection()
    try:
        yield db
    finally:
        await db.close()

async def get_current_user(token: str = Header(default=None)):
    if not token:
        raise HTTPUnauthorized()
    return {"user_id": 1}

@app.get("/users")
async def list_users(
    db = Depends(get_db),
    user = Depends(get_current_user)
):
    return await db.fetch("SELECT * FROM users")

# Override for testing
app.dependency_overrides[get_db] = lambda: mock_db
```

### Background Tasks

```python
from fenrir import BackgroundTasks

async def send_email(email: str):
    await asyncio.sleep(2)
    print(f"Email sent to {email}")

@app.post("/send-email")
async def send(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, "user@example.com")
    return {"message": "Email queued"}
```

### Running the Application

```python
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
```

**`app.run()` parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `host` | `str` | `"127.0.0.1"` | Bind host |
| `port` | `int` | `8000` | Bind port |
| `workers` | `int` | `1` | Number of worker processes |
| `app_path` | `str` | `None` | App module path (auto-detected) |

**CLI commands:**

```bash
# Run development server
fenrir run app:app --host 0.0.0.0 --port 8000 --dev

# Run with hot reload
fenrir run app:app --reload

# List all routes
fenrir routes app:app

# Start interactive shell
fenrir shell app:app

# Run benchmarks
fenrir bench app:app -i 2000 -t 5

# Create new project
fenrir new myapp

# Show system info
fenrir info app:app
```
