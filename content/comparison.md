# Framework Comparison

This page provides a comprehensive comparison between Fenrir and other popular Python web frameworks: Flask, FastAPI, Sanic, Falcon, and Bottle.

---

## Overview

| Aspect | Fenrir | Flask | FastAPI | Sanic | Falcon | Bottle |
|--------|--------|-------|---------|-------|--------|--------|
| **Version** | 4.0.0 | 3.x | 0.115+ | 24.x | 4.x | 0.12.x |
| **Python** | ≥3.8 | ≥3.8 | ≥3.8 | ≥3.8 | ≥3.8 | ≥3.7 |
| **Async** | ✅ ASGI | ❌ | ✅ ASGI | ✅ ASGI | ❌ | ❌ |
| **RPS (est.)** | ~15,000 | ~4,500 | ~14,200 | ~18,000 | ~15,000 | ~3,900 |
| **Learning Curve** | Medium | Low | Low-Medium | Medium | Medium | Very Low |
| **GitHub Stars** | New | ~68k | ~92k | ~18k | ~9k | ~9k |
| **Dependencies** | 6 core | Minimal | Starlette+Pydantic | uvloop | Minimal | Zero |
| **License** | MIT | BSD-3 | MIT | MIT | Apache-2.0 | MIT |

---

## Built-in Features

| Feature | Fenrir | Flask | FastAPI | Sanic | Falcon | Bottle |
|---------|--------|-------|---------|-------|--------|--------|
| **Validation** | Pydantic | Manual | Pydantic | Manual | Manual | Manual |
| **DI System** | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Auto-docs** | Swagger+ReDoc | ❌ | Swagger+ReDoc | ❌ | ❌ | ❌ |
| **Auth Classes** | 10 built-in | Extension | OAuth2 | ❌ | ❌ | ❌ |
| **Middleware** | 6 built-in | Extension | Starlette | Built-in | Hooks | Plugin |
| **Sessions** | 3 backends | Extension | ❌ | Extension | ❌ | Plugin |
| **Connection Pool** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **HTTP/2 Push** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Pagination** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **WebSocket** | ✅ | Extension | ✅ | ✅ | ❌ | Plugin |
| **SSE** | ✅ | Extension | Extension | ✅ | ❌ | ❌ |
| **Signals** | ✅ | Blinker | ❌ | Signal | ❌ | ❌ |
| **WSGI Compat** | ✅ | Native | ❌ | ❌ | Native | Native |
| **CLI** | 6 commands | Flask CLI | ❌ | ✅ | ❌ | ❌ |
| **Class Views** | ✅ | MethodView | ❌ | ❌ | Res | ❌ |

---

## Hello World

### Fenrir

```python
from fenrir import Fenrir

app = Fenrir()

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

app.run(host="0.0.0.0", port=8000)
```

### Flask

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def hello():
    return jsonify({"message": "Hello, World!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

### FastAPI

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def hello():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Sanic

```python
from sanic import Sanic
from sanic.response import json

app = Sanic("MyApp")

@app.get("/")
async def hello(request):
    return json({"message": "Hello, World!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```

### Falcon

```python
import falcon
import falcon.asgi

app = falcon.asgi.App()

class HelloResource:
    async def on_get(self, req, resp):
        resp.media = {"message": "Hello, World!"}

app.add_route("/", HelloResource())
```

### Bottle

```python
from bottle import Bottle, response
import json

app = Bottle()

@app.route("/")
def hello():
    response.content_type = "application/json"
    return json.dumps({"message": "Hello, World!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

---

## Performance Benchmark

Estimated requests per second (higher is better):

```
Sanic:     ~18,000 req/s  ████████████████████
Falcon:    ~15,000 req/s  █████████████████
Fenrir:    ~15,000+ req/s █████████████████ (ASGI + Trie routing)
FastAPI:   ~14,200 req/s  ████████████████
Flask:     ~4,500 req/s   █████
Bottle:    ~3,900 req/s   ████
```

---

## Use Case Recommendations

| Use Case | Best Choice | Reason |
|----------|-------------|--------|
| API with strong validation | Fenrir/FastAPI | Pydantic + DI built-in |
| High-throughput API | Sanic/Falcon | Raw speed |
| Full-stack web app | Flask/Django | Mature ecosystem, templates |
| Multi-paradigm team | **Fenrir** | Hybrid approach |
| Legacy WSGI migration | **Fenrir** | WSGI mount compatibility |
| ML model serving | FastAPI/Fenrir | Pydantic synergy |
| Embedded/minimal | Bottle | Zero dependencies |
| Real-time apps | Fenrir/Sanic | WebSocket + SSE built-in |

---

## Fenrir Strengths

1. **Hybrid Philosophy** — One framework, five paradigms
2. **10 Auth Classes** — OAuth2, HTTP Basic, Bearer, Digest, API Key, OpenID Connect
3. **Connection Pool** — Built-in connection pooling (Flask/FastAPI require extensions)
4. **HTTP/2 Push** — Server push without additional configuration
5. **WSGI Compatibility** — Mount legacy Flask/Django/Bottle apps
6. **Built-in Pagination** — 2 methods: paginate(), paginate_dict()
7. **6 CLI Commands** — run, routes, shell, bench, new, info
8. **Signals System** — Event-driven architecture
9. **3 Session Backends** — Redis, in-memory, server-side

---

## Fenrir Limitations

1. **New Framework** — Not yet battle-tested at large production scale
2. **Small Community** — No large community like Flask/FastAPI yet
3. **More Dependencies** — More than Flask/Bottle minimal
4. **New Documentation** — Just updated (8,640 lines)
5. **Learning Curve** — Flask developers need to adapt to async paradigm

---

## Migration Guide

### Flask to Fenrir

```python
# Flask
from flask import Flask, jsonify
app = Flask(__name__)

@app.route("/users/<int:id>")
def get_user(id):
    return jsonify({"id": id})

# Fenrir
from fenrir import Fenrir
app = Fenrir()

@app.get("/users/<id:int>")
async def get_user(id: int):
    return {"id": id}
```

**Changes:**

- `Flask()` → `Fenrir()`
- `@app.route()` → `@app.get()` / `@app.post()`
- `<int:id>` → `<id:int>`
- `jsonify()` → return dict directly
- Add `async` to handler

### FastAPI to Fenrir

```python
# FastAPI
from fastapi import FastAPI, Depends
app = FastAPI()

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}

# Fenrir
from fenrir import Fenrir, Query
app = Fenrir()

@app.get("/items/<item_id:int>")
async def read_item(item_id: int, q: str = Query(None)):
    return {"item_id": item_id, "q": q}
```

**Changes:**

- `FastAPI()` → `Fenrir()`
- `Query(None)` imported from fenrir (same as FastAPI)
- Almost identical otherwise

### Bottle to Fenrir

```python
# Bottle
from bottle import Bottle
app = Bottle()

@app.route("/hello")
def hello():
    return {"message": "Hello"}

# Fenrir
from fenrir import Fenrir
app = Fenrir()

@app.get("/hello")
async def hello():
    return {"message": "Hello"}
```

**Changes:**

- `Bottle()` → `Fenrir()`
- `@app.route()` → `@app.get()`
- Add `async`

---

## Conclusion

Fenrir offers a **complete solution** for developers who need:

- **Flexibility** — Multi-paradigm (Flask-like, FastAPI-like, Falcon-like)
- **Performance** — ASGI async, trie-based routing O(k)
- **Productivity** — 96 built-in exports, 6 middleware, 10 auth classes
- **Migration** — WSGI compatibility for legacy apps

**Best for:** Modern APIs, real-time apps, microservices, and teams wanting one framework for multiple use cases.

**Not ideal for:** Projects requiring large ecosystems (Flask/Django) or minimal dependencies (Bottle).
