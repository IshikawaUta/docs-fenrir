# Blueprints

Blueprints provide a way to organize your application into modular components. Each blueprint can have its own routes, middleware, and error handlers, which are registered with the main application when ready.

## Creating Blueprints

```python
from fenrir import Blueprint

api_bp = Blueprint("api", url_prefix="/api")

@api_bp.get("/items")
async def list_items():
    return [{"id": 1, "name": "Item 1"}]

@api_bp.get("/items/<item_id:int>")
async def get_item(item_id: int):
    return {"id": item_id, "name": f"Item {item_id}"}

@api_bp.post("/items")
async def create_item(data: dict):
    return {"id": 2, "name": data.get("name", "New Item"), "created": True}
```

## Registering Blueprints

```python
from fenrir import Fenrir

app = Fenrir()
app.register_blueprint(api_bp)
```

## Blueprint with Middleware

Apply middleware to all routes within a blueprint:

```python
from fenrir import Blueprint, HTTPUnauthorized, request

api_bp = Blueprint("api", url_prefix="/api")

@api_bp.before_request
async def check_api_key():
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPUnauthorized(detail="Missing API key")

@api_bp.get("/data")
async def get_data():
    return {"data": "protected"}

app.register_blueprint(api_bp)
```

## Multiple Blueprints

Organize your application into multiple modules:

```python
from fenrir import Fenrir, Blueprint

# users_bp.py
users_bp = Blueprint("users", url_prefix="/users")

@users_bp.get("")
async def list_users():
    return [{"id": 1, "name": "User 1"}]

@users_bp.get("/<user_id:int>")
async def get_user(user_id: int):
    return {"id": user_id, "name": f"User {user_id}"}

# products_bp.py
products_bp = Blueprint("products", url_prefix="/products")

@products_bp.get("")
async def list_products():
    return [{"id": 1, "name": "Product 1"}]

@products_bp.post("")
async def create_product(data: dict):
    return {"id": 2, **data, "created": True}

# app.py
app = Fenrir()
app.register_blueprint(users_bp)
app.register_blueprint(products_bp)
```

## Blueprint with Error Handlers

Register error handlers that apply only to routes within a blueprint:

```python
from fenrir import Blueprint, JSONResponse

api_bp = Blueprint("api", url_prefix="/api")

@api_bp.errorhandler(404)
async def api_not_found(req, exc):
    return JSONResponse({"error": "API resource not found"}, status_code=404)

@api_bp.get("/items")
async def list_items():
    return [{"id": 1}]
```

## Blueprint with Teardown

Register cleanup functions that run after each request within the blueprint:

```python
api_bp = Blueprint("api", url_prefix="/api")

@api_bp.teardown_request
async def cleanup(exc):
    if exc:
        print(f"Request ended with error: {exc}")
    # Release resources, close connections, etc.
```

## Nested Blueprint Organization

Organize large applications with domain-specific blueprints:

```python
from fenrir import Fenrir, Blueprint

# Auth module
auth_bp = Blueprint("auth", url_prefix="/auth")

@auth_bp.post("/login")
async def login(credentials: dict):
    return {"token": "abc123"}

@auth_bp.post("/register")
async def register(user_data: dict):
    return {"id": 1, "created": True}

# API module
api_bp = Blueprint("api", url_prefix="/api")

@api_bp.get("/users")
async def list_users():
    return [{"id": 1, "name": "Alice"}]

# Admin module
admin_bp = Blueprint("admin", url_prefix="/admin")

@admin_bp.get("/stats")
async def get_stats():
    return {"total_users": 100}

# Register all blueprints
app = Fenrir()
app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)
```

## Blueprint URL Prefix

The `url_prefix` is prepended to all routes in the blueprint:

```python
# All routes will be under /api/v1
api_v1 = Blueprint("api_v1", url_prefix="/api/v1")

@api_v1.get("/users")  # Becomes /api/v1/users
async def list_users():
    return []
```

## Best Practices

- **One blueprint per domain**: Group related routes (users, products, auth) into separate blueprints.
- **Use descriptive names**: Blueprint names appear in error messages and logs.
- **Keep blueprints focused**: Avoid creating monolithic blueprints with unrelated routes.
- **Use `url_prefix`**: Always set a prefix to avoid route collisions between blueprints.
