# Sessions

Fenrir provides multiple session backends for storing user data across requests.

### Session Usage with Context Locals

Access the current session via the `session` context local, imported from `fenrir`:

```python
from fenrir import Fenrir, session

app = Fenrir()
app.config["SECRET_KEY"] = "your-secret-key"

@app.get("/set")
async def set_session():
    session["user_id"] = 123
    session["theme"] = "dark"
    return {"status": "set"}

@app.get("/get")
async def get_session():
    user_id = session.get("user_id")
    return {"user_id": user_id}

@app.get("/clear")
async def clear_session():
    session.clear()
    return {"status": "cleared"}
```

The `session` object is a dict-like object that automatically tracks modifications and is saved to the response at the end of each request.

---

### SessionMixin

Base class for all session objects. A `dict` subclass that tracks whether the session has been `modified` or `accessed`:

```python
from fenrir.sessions import SessionMixin

class CustomSession(SessionMixin):
    pass

s = CustomSession()
print(s.modified)  # False
s["key"] = "value"
print(s.modified)  # True
```

**Tracking behavior:**

| Operation | Sets `modified` |
|-----------|-----------------|
| `session["key"] = value` | Yes |
| `del session["key"]` | Yes |
| `session.clear()` | Yes |
| `session.pop("key")` | Yes |
| `session.update(...)` | Yes |
| `session["key"]` (read only) | No (only sets `accessed`) |

---

### SecureCookieSession

Cookie-based session (the default). Session data is serialized, signed, and stored in a cookie on the client:

```python
from fenrir import Fenrir
from fenrir.sessions import SecureCookieSession

app = Fenrir()
app.config["SECRET_KEY"] = "your-secret-key"

@app.get("/set")
async def set_session():
    session["user_id"] = 123
    return {"status": "set"}
```

---

### ServerSideSession

Server-side session with a `sid` (session ID) attribute. The session data is stored server-side; only the session ID is sent to the client as a cookie:

```python
from fenrir.sessions import ServerSideSession

s = ServerSideSession()
s.sid = "abc123"
s["user_id"] = 123

print(s.sid)        # "abc123"
print(s.modified)   # True
```

---

### SessionInterface (Abstract Base Class)

Base class for all session backends. Subclass this to implement custom storage:

```python
from fenrir.sessions import SessionInterface, SessionMixin

class SessionInterface:
    def open_session(self, app, request) -> SessionMixin:
        """Load and return a session from the request."""
        raise NotImplementedError()

    def save_session(self, app, session, response):
        """Save the session to the response."""
        raise NotImplementedError()
```

---

### SecureCookieSessionInterface

The default session interface. Serializes session data with `itsdangerous.URLSafeTimedSerializer`, signs it, and stores it in a cookie:

```python
from fenrir import Fenrir
from fenrir.sessions import SecureCookieSessionInterface

app = Fenrir()
app.config["SECRET_KEY"] = "your-secret-key"
app.session_interface = SecureCookieSessionInterface()
```

**How it works:**

- `open_session()` reads the cookie, verifies the signature, and returns a `SecureCookieSession`.
- `save_session()` serializes the session, signs it, and sets the cookie on the response.
- If the session is empty and modified, the cookie is deleted.

---

### InMemorySessionBackend

A simple in-memory session store for testing and single-process deployments. Sessions are stored in a Python dict with TTL-based expiration:

```python
from fenrir.sessions import InMemorySessionBackend

backend = InMemorySessionBackend()

# Store session data
backend.set("sid123", {"user_id": 1}, ttl=3600)

# Retrieve session data
data = backend.get("sid123")
print(data)  # {"user_id": 1}

# Delete session
backend.delete("sid123")
```

Expired sessions are automatically cleaned up on access.

---

### In-Memory Sessions

Server-side sessions backed by `InMemorySessionBackend`:

```python
from fenrir import Fenrir
from fenrir.sessions import InMemorySessionInterface

app = Fenrir()
app.config["SECRET_KEY"] = "your-secret-key"
app.session_interface = InMemorySessionInterface(ttl=3600)
```

**Parameters:**

- `backend`: Custom `InMemorySessionBackend` instance
- `ttl`: Session time-to-live in seconds (default: `86400`)

---

### Redis Sessions

Server-side sessions backed by Redis. Supports both sync and async Redis clients:

```python
from fenrir import Fenrir
from fenrir.sessions import RedisSessionInterface

app = Fenrir()
app.config["SECRET_KEY"] = "your-secret-key"

# With fakeredis (for testing)
import fakeredis
redis_client = fakeredis.FakeRedis()
app.session_interface = RedisSessionInterface(redis_client=redis_client)

# With real Redis
import redis
redis_client = redis.Redis(host="localhost", port=6379, db=0)
app.session_interface = RedisSessionInterface(redis_client=redis_client, ttl=7200)
```

**Parameters:**

- `redis_client`: Redis client instance (required)
- `prefix`: Key prefix (default: `"session:"`)
- `ttl`: Session time-to-live in seconds (default: `86400`)

Install Redis support: `pip install fenrir-framework[redis]`

---

### Configuration Keys

| Key | Default | Description |
|-----|---------|-------------|
| `SECRET_KEY` | *(required for cookie sessions)* | Secret key for signing cookies via `itsdangerous` |
| `SESSION_COOKIE_NAME` | `"session"` | Cookie name |
| `SESSION_COOKIE_DOMAIN` | `None` | Cookie domain |
| `SESSION_COOKIE_PATH` | `"/"` | Cookie path |
| `SESSION_COOKIE_SECURE` | `True` | Only send cookie over HTTPS |
| `SESSION_COOKIE_HTTPONLY` | `True` | Prevent JavaScript access to cookie |
| `SESSION_COOKIE_SAMESITE` | `None` | SameSite cookie attribute (`"Strict"`, `"Lax"`, `"None"`) |
| `SESSION_TTL` | `86400` | Session TTL in seconds (server-side backends) |

---

### Session Classes Reference

| Class | Description |
|-------|-------------|
| `SessionMixin` | Base dict subclass with `modified`/`accessed` tracking |
| `SecureCookieSession` | Cookie-based session (default) |
| `ServerSideSession` | Server-side session with `sid` attribute |
| `SessionInterface` | Abstract base class for session backends |
| `SecureCookieSessionInterface` | Default cookie-based session interface |
| `InMemorySessionBackend` | In-memory storage backend |
| `InMemorySessionInterface` | In-memory session interface |
| `RedisSessionInterface` | Redis-backed session interface |

---

### Custom Session Backend

Implement `SessionInterface` for custom backends:

```python
from fenrir import Fenrir
from fenrir.sessions import SessionInterface, SessionMixin

class CustomSession(SessionMixin):
    pass

class CustomSessionInterface(SessionInterface):
    def open_session(self, app, request):
        session_id = request.cookies.get("session_id")
        if session_id:
            data = self.load_from_storage(session_id)
            session = CustomSession(data)
        else:
            session = CustomSession()
        return session

    def save_session(self, app, session, response):
        if session.modified:
            self.save_to_storage(session)
            response.set_cookie("session_id", session.sid)

    def load_from_storage(self, session_id):
        # Implement your storage lookup here
        pass

    def save_to_storage(self, session):
        # Implement your storage save here
        pass

app = Fenrir()
app.session_interface = CustomSessionInterface()
```

---

### Session Lifecycle

1. **Request arrives** — `SessionInterface.open_session()` reads the session from the cookie/storage and returns a session object.
2. **During request handling** — Handlers read/write `session["key"]`. The `modified` flag is set automatically.
3. **Response sent** — `SessionInterface.save_session()` checks if the session was modified, and if so, persists it and sets/updates the cookie.
