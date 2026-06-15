# Class-Based Resources

Fenrir supports both Falcon-style resource controllers and Flask-style class-based views via the `View` and `MethodView` base classes.

---

## Falcon-Style Resources

Define `on_get`, `on_post`, `on_delete` methods for each HTTP method:

```python
from fenrir import View

class ItemResource:
    async def on_get(self, req, resp, item_id: int):
        """Get item"""
        resp.status = 200
        resp.media = {
            "item_id": item_id,
            "name": f"Item {item_id}",
            "status": "active"
        }

    async def on_post(self, req, resp, item_id: int):
        """Create or update item"""
        data = req.json
        resp.status = 201
        resp.media = {
            "item_id": item_id,
            "data": data,
            "created": True
        }

    async def on_delete(self, req, resp, item_id: int):
        """Delete item"""
        resp.status = 204

# Register resource
app.add_route("/items/<item_id:int>", ItemResource())
```

---

## The `View` Base Class

`View` is the base class for all class-based resources. It provides the contract that Fenrir's router expects.

### Class Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `methods` | `Optional[List[str]]` | `None` | Allowed HTTP methods. When `None`, auto-detected from defined handler methods. |
| `provide_automatic_options` | `Optional[bool]` | `None` | Controls auto OPTIONS handling. `None` = auto-detect, `True` = always add OPTIONS, `False` = never add OPTIONS. |

### `dispatch_request(*args, **kwargs)`

Abstract method that must be overridden by subclasses. Called by the framework when a matched route invokes this view.

```python
from fenrir import View

class BaseView(View):
    def dispatch_request(self, *args, **kwargs):
        raise NotImplementedError()
```

### `as_view(name, *class_args, **class_kwargs)` (classmethod)

Creates a view function from a class that can be registered with `app.add_route()`. This is the bridge between class-based views and Fenrir's routing system.

```python
from fenrir import View

class DashboardView(View):
    methods = ["GET", "POST"]

    async def get(self):
        return {"dashboard": "data"}

    async def post(self):
        data = request.json
        return {"saved": True}

# Register as a standalone view function
app.add_route("/dashboard", DashboardView.as_view("dashboard"))
```

**What `as_view()` does:**

1. Creates a closure that instantiates the class and calls `dispatch_request()`.
2. Auto-detects allowed HTTP methods by inspecting the class for `get`, `post`, `put`, `delete`, `patch`, `options`, and `head` attributes. If none are found, defaults to `["GET"]`.
3. Copies `provide_automatic_options` from the class to the view function.
4. Sets `__name__`, `__doc__`, and `__module__` on the view function for introspection.

**Arguments:**

- `name` — The view function name (used for debugging and URL building).
- `*class_args, **class_kwargs` — Forwarded to the class constructor on every request.

---

## The `MethodView` Class

`MethodView` extends `View` with automatic HTTP method dispatch and dependency injection. Define methods named after HTTP verbs (`get`, `post`, `put`, `delete`, `patch`) and Fenrir routes to them automatically.

```python
from fenrir import MethodView, request

class ItemListView(MethodView):
    async def get(self):
        """List all items"""
        return [{"id": 1, "name": "Item 1"}]

    async def post(self):
        """Create new item"""
        data = request.json
        return {"id": 2, "name": data["name"], "created": True}

app.add_route("/items", ItemListView())
```

### Method Resolution

`MethodView.dispatch_request()` resolves the handler as follows:

| HTTP Method | Handler | Fallback |
|-------------|---------|----------|
| `GET` | `self.get()` | — |
| `POST` | `self.post()` | — |
| `PUT` | `self.put()` | — |
| `DELETE` | `self.delete()` | — |
| `PATCH` | `self.patch()` | — |
| `HEAD` | `self.get()` | Falls back to GET handler automatically |
| `OPTIONS` | Auto-generated response | Returns `Allow` header listing all available methods |

If no handler is found for the requested method (other than HEAD/OPTIONS), a `RuntimeError` is raised.

### HEAD Falls Back to GET

When a `HEAD` request arrives and no `head()` method is defined, `MethodView` automatically delegates to `get()`. This follows the HTTP specification where HEAD must return the same headers as GET but no body.

```python
class DataView(MethodView):
    async def get(self):
        return {"data": "value"}

# HEAD /data → delegates to get(), returns same headers without body
```

### Automatic OPTIONS Response

When a `OPTIONS` request arrives and no `options()` method is defined, `MethodView` automatically returns a `200` response with an `Allow` header listing all available methods:

```python
class ResourceView(MethodView):
    async def get(self):
        return {"data": "value"}

    async def post(self):
        return {"created": True}

# OPTIONS /resource returns:
# HTTP/1.1 200 OK
# Allow: GET, HEAD, OPTIONS, POST
```

The `Allow` header is automatically constructed by:

1. Scanning the instance for all defined HTTP method handlers (`get`, `post`, `put`, `delete`, `patch`, `options`, `head`).
2. Adding `HEAD` if `GET` is present (since HEAD falls back to GET).
3. Always adding `OPTIONS`.
4. Sorting the list alphabetically.

---

## Dependency Injection in MethodView

`MethodView` integrates with Fenrir's dependency injection system via `resolve_parameters()`. Handler parameters are automatically resolved from path parameters, the request, and the response.

### Path Parameters

Path parameters from the URL are injected into handler method parameters by name and type:

```python
from fenrir import MethodView

class ItemResource(MethodView):
    async def get(self, item_id: int):
        return {"item_id": item_id, "name": f"Item {item_id}"}

app.add_route("/items/<item_id:int>", ItemResource())
```

The `item_id` parameter is extracted from the URL, coerced to `int`, and passed to `get()`.

### Request and Response Injection

The `req` and `resp` objects are available via the context, but can also be injected as parameters:

```python
from fenrir import MethodView
from fenrir.request import Request
from fenrir.response import Response

class ItemView(MethodView):
    async def get(self, req: Request, resp: Response, item_id: int):
        resp.headers["X-Item-ID"] = str(item_id)
        return {"item_id": item_id}
```

### Query Parameters and Body

Use `Annotated` with `Query`, `Body`, and other parameter markers:

```python
from typing import Annotated
from fenrir import MethodView
from fenrir import Query, Body

class SearchView(MethodView):
    async def get(self, q: Annotated[str, Query()], limit: Annotated[int, Query()] = 10):
        return {"query": q, "limit": limit}

class CreateView(MethodView):
    async def post(self, data: Annotated[dict, Body()]):
        return {"created": True, "data": data}
```

### Background Tasks

`BackgroundTasks` is auto-injected when declared as a parameter:

```python
from fenrir import MethodView
from fenrir.background import BackgroundTasks

class ExportView(MethodView):
    async def post(self, background_tasks: BackgroundTasks):
        background_tasks.add_task(send_email, "user@example.com")
        return {"export": "started"}
```

---

## Complete Example

```python
from fenrir import Fenrir, MethodView, request
from typing import Annotated
from fenrir import Query, Body

app = Fenrir()

class ItemListView(MethodView):
    async def get(self, limit: Annotated[int, Query()] = 20):
        """List items with optional limit"""
        return {"items": [], "limit": limit}

    async def post(self, data: Annotated[dict, Body()]):
        """Create a new item"""
        return {"id": 1, **data, "created": True}

class ItemDetailView(MethodView):
    async def get(self, item_id: int):
        """Get a single item"""
        return {"item_id": item_id, "name": f"Item {item_id}"}

    async def put(self, item_id: int, data: Annotated[dict, Body()]):
        """Update an item"""
        return {"item_id": item_id, **data, "updated": True}

    async def delete(self, item_id: int):
        """Delete an item"""
        return {"deleted": True}

app.add_route("/items", ItemListView())
app.add_route("/items/<item_id:int>", ItemDetailView())
```

**Behavior summary:**

| Route | Method | Handler | Notes |
|-------|--------|---------|-------|
| `GET /items` | GET | `ItemListView.get` | `limit` defaults to 20 |
| `POST /items` | POST | `ItemListView.post` | JSON body injected |
| `HEAD /items` | HEAD | `ItemListView.get` | Falls back to GET |
| `OPTIONS /items` | OPTIONS | Auto | Returns `Allow: GET, HEAD, OPTIONS, POST` |
| `GET /items/42` | GET | `ItemDetailView.get` | `item_id=42` |
| `PUT /items/42` | PUT | `ItemDetailView.put` | `item_id=42` + JSON body |
| `DELETE /items/42` | DELETE | `ItemDetailView.delete` | `item_id=42` |
| `OPTIONS /items/42` | OPTIONS | Auto | Returns `Allow: DELETE, GET, HEAD, OPTIONS, PUT` |

---

## View vs MethodView

| Feature | `View` | `MethodView` |
|---------|--------|-------------|
| Method dispatch | Manual (`dispatch_request`) | Automatic (routes to `self.get`, `self.post`, etc.) |
| Dependency injection | Manual | Automatic via `resolve_parameters()` |
| HEAD fallback | Manual | Automatic (falls back to GET) |
| OPTIONS handling | Manual | Automatic (returns Allow header) |
| Path params | Via `req.path_params` or kwargs | Injected into handler parameters |

Use `View` when you need full control over dispatch. Use `MethodView` for the convention-over-configuration approach with automatic routing and DI.
