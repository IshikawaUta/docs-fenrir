# Dependency Injection

Fenrir supports FastAPI-style dependency injection with `Depends`, parameter markers, and generator-based cleanup.

### Basic Dependency Injection

```python
from fenrir import Depends, Header

# Define a dependency
async def get_current_user(x_token: str = Header(default=None)):
    if x_token != "valid_token":
        raise HTTPException(status_code=401)
    return {"user_id": 1, "name": "John"}

# Use dependency
@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"message": f"Hello {current_user['name']}"}
```

### Parameter Markers

Fenrir provides markers to specify where parameters come from:

#### `Query` — Query Parameters

```python
from fenrir import Query

@app.get("/search")
async def search(q: str = Query(default=None)):
    return {"query": q}
```

#### `Header` — HTTP Headers

```python
from fenrir import Header

@app.get("/check")
async def check(authorization: str = Header(default=None)):
    return {"has_auth": authorization is not None}
```

#### `Cookie` — Cookies

```python
from fenrir import Cookie

@app.get("/preferences")
async def get_prefs(theme: str = Cookie(default="light")):
    return {"theme": theme}
```

#### `Body` — Request Body (explicit)

```python
from fenrir import Body

@app.post("/items")
async def create_item(name: str = Body(...), price: float = Body(...)):
    return {"name": name, "price": price}
```

#### `Form` — Form Data

```python
from fenrir import Form

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    return {"username": username}
```

#### `File` — File Uploads

```python
from fenrir import File, UploadFile

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    return {"filename": file.filename}
```

#### `FormParam` and `FileParam` — Base Classes

`FormParam` and `FileParam` are the base classes for `Form()` and `File()` markers. You can use them directly if needed:

```python
from fenrir.dependencies import FormParam, FileParam

# FormParam is the base class for Form()
# FileParam is the base class for File()

# These are equivalent:
async def route1(data: str = Form(...)): ...
async def route2(data: str = FormParam(default=...)): ...

# These are equivalent:
async def route3(file: UploadFile = File(...)): ...
async def route4(file: UploadFile = FileParam(default=...)): ...
```

#### `Path` — Path Parameters

```python
from fenrir import Path

@app.get("/users/<user_id:int>")
async def get_user(user_id: int = Path(...)):
    return {"user_id": user_id}
```

### Annotated Type Markers (Python 3.9+)

Use `Annotated` for cleaner parameter declarations. This avoids polluting default values and keeps type hints clean:

```python
from typing import Annotated
from fenrir import Query, Header, Cookie, Body, Form, File, Depends

# Query parameters
@app.get("/search")
async def search(
    q: Annotated[str, Query(default=None)],
    authorization: Annotated[str, Header(default=None)],
    theme: Annotated[str, Cookie(default="light")],
):
    return {"query": q, "has_auth": authorization is not None, "theme": theme}

# Body and Form with Annotated
@app.post("/items")
async def create_item(
    name: Annotated[str, Body(...)],
    price: Annotated[float, Body(...)],
):
    return {"name": name, "price": price}

@app.post("/login")
async def login(
    username: Annotated[str, Form(...)],
    password: Annotated[str, Form(...)],
):
    return {"username": username}

# File upload with Annotated
@app.post("/upload")
async def upload(
    file: Annotated[UploadFile, File(...)],
):
    return {"filename": file.filename}

# Dependencies with Annotated
async def get_db():
    db = {"connection": "active"}
    try:
        yield db
    finally:
        await db.close()

@app.get("/users/<user_id:int>")
async def get_user(
    user_id: int,
    db: Annotated[dict, Depends(get_db)],
):
    return {"user_id": user_id, "from_db": True}
```

### Yield Dependencies (Generator-Based Cleanup)

Dependencies can be generator functions that yield a value and perform cleanup after the request finishes. Both sync and async generators are supported:

#### Async Generator Dependencies

```python
async def get_db():
    db = await create_connection()
    try:
        yield db
    finally:
        await db.close()

@app.get("/users")
async def get_users(db = Depends(get_db)):
    users = await db.fetch_all("SELECT * FROM users")
    return users
```

#### Sync Generator Dependencies

```python
def get_db_sync():
    db = create_connection_sync()
    try:
        yield db
    finally:
        db.close()

@app.get("/users")
async def get_users(db = Depends(get_db_sync)):
    users = db.fetch_all("SELECT * FROM users")
    return users
```

#### Complex Cleanup Example

```python
from contextlib import asynccontextmanager

async def get_database_session():
    session = await create_session()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

async def get_current_user(
    session = Depends(get_database_session),
    token: str = Header(default=None),
):
    if not token:
        raise HTTPException(status_code=401)
    user = await session.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

@app.get("/profile")
async def get_profile(user = Depends(get_current_user)):
    return {"name": user.name, "email": user.email}
```

### Dependency with Sub-dependencies

Dependencies can depend on other dependencies. Fenrir resolves them automatically:

```python
async def verify_token(authorization: str = Header(default=None)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)
    token = authorization.replace("Bearer ", "")
    return token

async def get_current_user(token: str = Depends(verify_token)):
    return {"user_id": 1}

@app.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user
```

### Dependency Caching

By default, dependencies are cached per request. This means if multiple parameters depend on the same dependency, it will only be resolved once:

```python
# This dependency is called once per request, even if used twice
async def get_db():
    print("Creating database connection")  # Only printed once
    return {"connection": "active"}

@app.get("/items")
async def get_items(
    db1 = Depends(get_db),
    db2 = Depends(get_db),  # Uses cached result from db1
):
    return {"db1": db1, "db2": db2, "same": db1 is db2}  # same: True
```

#### Disabling Cache with `use_cache=False`

Disable per-request caching to get a fresh instance every time:

```python
@app.get("/random")
async def get_random(value: int = Depends(get_random_value, use_cache=False)):
    return {"value": value}

# Each call to get_random_value returns a new value
async def get_random_value():
    import random
    return random.randint(1, 100)
```

### Circular Dependency Detection

Fenrir detects circular dependencies and raises a `RuntimeError`:

```python
async def dep_a(dep_b=Depends(dep_b)):
    return "a"

async def dep_b(dep_a=Depends(dep_a)):
    return "b"

@app.get("/circular")
async def circular(a=Depends(dep_a)):
    return a

# This will raise: RuntimeError: Circular dependency detected for 'dep_a'
```

### Dependency Overrides for Testing

Override dependencies during testing to mock external services:

```python
# Production dependency
async def get_db():
    db = await create_production_connection()
    try:
        yield db
    finally:
        await db.close()

# Test override
async def override_get_db():
    yield {"connection": "test-mock", "query": lambda sql: []}

# In test setup
app.dependency_overrides[get_db] = override_get_db

# In test
async def test_get_users():
    response = await client.get("/users")
    assert response.status_code == 200

# In test teardown
app.dependency_overrides.clear()
```

#### Overriding Multiple Dependencies

```python
# Override multiple dependencies at once
app.dependency_overrides = {
    get_db: override_get_db,
    get_current_user: override_get_user,
    verify_token: override_verify_token,
}

# Clear all overrides
app.dependency_overrides.clear()
```

### Lazy Lambda Dependency Unwrapping

You can use lambdas to defer dependency resolution. Fenrir automatically unwraps lazy lambdas:

```python
# Lambda that returns a dependency function
@app.get("/items")
async def get_items(
    db = Depends(lambda: get_db),  # Unwrapped to get_db
):
    return await db.fetch_all("SELECT * FROM items")

# Lambda with configuration
def create_db_dependency(connection_string: str):
    async def get_db():
        db = await create_connection(connection_string)
        try:
            yield db
        finally:
            await db.close()
    return get_db

@app.get("/items")
async def get_items(
    db = Depends(lambda: create_db_dependency("postgresql://localhost/mydb")),
):
    return await db.fetch_all("SELECT * FROM items")
```

### BackgroundTasks Auto-Injection

Add `background_tasks: BackgroundTasks` as a parameter to automatically inject background task support:

```python
from fenrir import BackgroundTasks

def send_email(to: str, subject: str, body: str):
    # Send email logic
    print(f"Sending email to {to}")

@app.post("/notify")
async def notify(background_tasks: BackgroundTasks):
    background_tasks.add_task(send_email, to="user@example.com", subject="Hello", body="World")
    return {"status": "queued"}

# With other dependencies
async def get_user(token: str = Header(default=None)):
    return {"user_id": 1, "email": "user@example.com"}

@app.post("/notify-user")
async def notify_user(
    user: dict = Depends(get_user),
    background_tasks: BackgroundTasks = None,
):
    background_tasks.add_task(
        send_email,
        to=user["email"],
        subject="Welcome!",
        body="Thanks for signing up"
    )
    return {"status": "queued"}
```

### WebSocket Auto-Injection

Parameters named `websocket` or `ws` automatically receive the WebSocket object:

```python
from fenrir import WebSocket

# By parameter name
@app.websocket("/ws")
async def websocket_handler(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message: {data}")

# Also works with "ws"
@app.websocket("/ws-alt")
async def websocket_handler_alt(ws: WebSocket):
    await ws.accept()
    data = await ws.receive_text()
    await ws.send_text(f"Echo: {data}")

# With dependencies
async def get_user_from_ws(websocket: WebSocket):
    token = await websocket.receive_text()
    return {"user_id": 1, "token": token}

@app.websocket("/ws/auth")
async def websocket_auth(
    websocket: WebSocket,
    user: dict = Depends(get_user_from_ws),
):
    await websocket.accept()
    await websocket.send_json({"user": user})
```

### Request/Response Auto-Injection

Parameters named `req`/`request` get the Request object, and `resp`/`response` get the Response object:

```python
from fenrir import Request, Response

# Request auto-injection
@app.get("/items")
async def get_items(req: Request):
    # Access request properties
    user_agent = req.headers.get("user-agent")
    ip = req.host
    return {"user_agent": user_agent, "ip": ip}

# Response auto-injection
@app.get("/items")
async def get_items(resp: Response):
    # Modify response headers
    resp.headers["X-Custom"] = "value"
    return {"items": []}

# Both Request and Response
@app.get("/items")
async def get_items(req: Request, resp: Response):
    # Log request and modify response
    print(f"Request: {req.method} {req.path}")
    resp.headers["X-Request-ID"] = req.headers.get("x-request-id", "unknown")
    return {"items": []}

# With other parameters
@app.get("/users/<user_id:int>")
async def get_user(
    user_id: int,
    req: Request,
    resp: Response,
    token: str = Header(default=None),
):
    # Access all injected parameters
    return {
        "user_id": user_id,
        "method": req.method,
        "token": token,
    }
```

### Complete Example

Here's a complete example combining multiple features:

```python
from fenrir import Fenrir, Depends, Header, Query, Form, File, BackgroundTasks, Request, Response
from typing import Annotated

app = Fenrir()

# Database dependency with cleanup
async def get_db():
    db = await create_database_connection()
    try:
        yield db
    finally:
        await db.close()

# Authentication dependency
async def get_current_user(
    db = Depends(get_db),
    authorization: str = Header(default=None),
):
    if not authorization:
        raise HTTPException(status_code=401)
    token = authorization.replace("Bearer ", "")
    user = await db.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

# Background task function
def send_welcome_email(email: str, name: str):
    print(f"Sending welcome email to {email} for {name}")

@app.post("/register")
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    avatar: UploadFile = File(None),
    background_tasks: BackgroundTasks = None,
    req: Request = None,
    resp: Response = None,
):
    # Create user
    db = await get_db()
    user = await db.create_user(username, email, password)
    
    # Handle file upload
    if avatar:
        await save_avatar(user.id, avatar)
    
    # Schedule background task
    background_tasks.add_task(send_welcome_email, email, username)
    
    # Add custom headers
    resp.headers["X-User-ID"] = str(user.id)
    
    return {"user_id": user.id, "message": "Registration successful"}

@app.get("/profile")
async def get_profile(
    user: dict = Depends(get_current_user),
    req: Request = None,
):
    return {
        "user": user,
        "ip": req.host,
    }

@app.get("/items")
async def get_items(
    q: str = Query(default=None),
    page: int = Query(default=1),
    db = Depends(get_db),
):
    items = await db.search_items(q, page=page)
    return {"items": items, "page": page}
```