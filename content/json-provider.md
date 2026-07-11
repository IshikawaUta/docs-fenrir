# JSON Provider

Fenrir includes a pluggable JSON serialization system with two distinct approaches: **auto-serialization** for HTTP responses, and **tagged serialization** for round-trip encoding of complex Python types (e.g. sessions).

## `JSONProvider` Abstract Base Class

`JSONProvider` is the base class for all JSON providers. It receives the application instance and exposes two abstract methods that subclasses must implement.

| Method | Signature | Description |
|--------|-----------|-------------|
| `dumps(obj, **kwargs) -> str` | Serialize a Python object to a JSON string. | Must be overridden. |
| `loads(s, **kwargs) -> Any` | Deserialize a JSON string to a Python object. | Must be overridden. |

```python
from fenrir.json import JSONProvider

class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        kwargs.setdefault("ensure_ascii", False)
        kwargs.setdefault("indent", 2)
        return json.dumps(obj, **kwargs)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)
```

Register a custom provider on the application:

```python
app = Fenrir()
app.json = CustomJSONProvider(app)
```

---

## `DefaultJSONProvider`

The built-in provider. It sets `ensure_ascii=False` by default and provides a `default` handler for common types:

| Python Type | Serialized As |
|-------------|---------------|
| `datetime` | ISO 8601 string (`o.isoformat()`) |
| `date` | ISO 8601 string (`o.isoformat()`) |
| `uuid.UUID` | String representation (`str(o)`) |

Unrecognized types raise `TypeError`.

```python
from fenrir import Fenrir
from fenrir.json import DefaultJSONProvider

app = Fenrir()

@app.get("/info")
async def info():
    return {
        "created_at": datetime.now(),   # serialized as ISO string
        "user_id": uuid.uuid4(),        # serialized as string
    }
```

> **Note:** When orjson is installed (default in v4.1.2), `DefaultJSONProvider` uses `orjson.dumps` which natively handles `datetime`, `date`, `UUID`, and more. Falls back to stdlib `json.dumps` with a custom `default` handler when orjson is not available.

---

## Tagged Serialization System

For cases where you need to deserialize back to the original Python types (session storage, caching, etc.), use `TaggedJSONSerializer`. Every supported value is wrapped in a `{"__t__": "<tag>", "__v__": <value>}` envelope.

### `JSONTag` Abstract Base Class

Each tag type implements this interface:

| Method | Signature | Description |
|--------|-----------|-------------|
| `check(value) -> bool` | Return `True` if `value` should use this tag. | Must be overridden by subclasses. |
| `to_json(value) -> Any` | Convert a Python value to its tagged dict representation. | Must be overridden by subclasses. |
| `to_python(value) -> Any` | Convert the stored `__v__` back to a Python object. | Must be overridden by subclasses. |

### Concrete Tag Classes

| Class | Tag | Python Type | JSON Envelope | Serialization Detail |
|-------|-----|-------------|---------------|----------------------|
| `TagDateTime` | `dt` | `datetime` | `{"__t__": "dt", "__v__": "ISO string"}` | `isoformat()` / `fromisoformat()` |
| `TagDate` | `d` | `date` | `{"__t__": "d", "__v__": "ISO string"}` | `isoformat()` / `date.fromisoformat()` |
| `TagUUID` | `u` | `uuid.UUID` | `{"__t__": "u", "__v__": "hex string"}` | `.hex` / `UUID(hex)` |
| `TagBytes` | `b` | `bytes` | `{"__t__": "b", "__v__": "base64 string"}` | `base64.b64encode` / `b64decode` |
| `TagTuple` | `t` | `tuple` | `{"__t__": "t", "__v__": [items]}` | `list()` / `tuple()` |

> `TagDate.check()` explicitly excludes `datetime` instances (`isinstance(value, date) and not isinstance(value, datetime)`) so that datetime values are matched by `TagDateTime` first.

---

### `TaggedJSONSerializer`

A standalone serializer that registers the five built-in tags and recursively walks dicts/lists to apply tagging during dumps and untagging during loads.

#### Constructor

```python
TaggedJSONSerializer()
```

Creates a serializer with the default tag registry. The `tags` class attribute is a `dict[str, JSONTag]` mapping tag names to instances:

```python
tags = {
    "dt": TagDateTime(),
    "d":  TagDate(),
    "u":  TagUUID(),
    "b":  TagBytes(),
    "t":  TagTuple(),
}
```

#### Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `dumps(obj) -> str` | Recursively tag all supported values in `obj`, then `json.dumps` the result. | Walks dicts/lists and applies registered tags to convert Python types to JSON-safe envelopes. |
| `loads(s) -> Any` | `json.loads` the string, then recursively detect `{"__t__": …, "__v__": …}` envelopes and restore the original Python types. | Restores tagged values back to their original Python types using registered tags. |

#### Usage

```python
from fenrir.json import TaggedJSONSerializer
from datetime import datetime
import uuid

serializer = TaggedJSONSerializer()

data = {
    "created": datetime(2026, 1, 15, 10, 30),
    "user_id": uuid.uuid4(),
    "data": b"binary content",
    "coords": (1.5, 2.5),
}

json_str = serializer.dumps(data)
# {
#   "created": {"__t__": "dt", "__v__": "2026-01-15T10:30:00"},
#   "user_id": {"__t__": "u", "__v__": "a1b2c3d4e5f6..."},
#   "data": {"__t__": "b", "__v__": "YmluYXJ5IGNvbnRlbnQ="},
#   "coords": {"__t__": "t", "__v__": [1.5, 2.5]}
# }

restored = serializer.loads(json_str)
# restored["created"] → datetime(2026, 1, 15, 10, 30)
# restored["user_id"] → UUID("a1b2c3d4e5f6...")
# restored["data"]     → b"binary content"
# restored["coords"]  → (1.5, 2.5)
```

### Extending with Custom Tags

Subclass `JSONTag` and register the new tag:

```python
from fenrir.json import TaggedJSONSerializer, JSONTag

class TagSet(JSONTag):
    def check(self, value):
        return isinstance(value, set)

    def to_json(self, value):
        return {"__t__": "set", "__v__": list(value)}

    def to_python(self, value):
        return set(value)

serializer = TaggedJSONSerializer()
serializer.tags["set"] = TagSet()
```

---

## API Reference

### `JSONProvider`

| Member | Type | Description |
|--------|------|-------------|
| `__init__(app)` | method | Store a reference to the application. |
| `dumps(obj, **kwargs) -> str` | abstract | Serialize to JSON string. |
| `loads(s, **kwargs) -> Any` | abstract | Deserialize from JSON string. |

### `DefaultJSONProvider(JSONProvider)`

| Member | Type | Description |
|--------|------|-------------|
| `dumps(obj, **kwargs) -> str` | method | Uses orjson when available (7x faster), falls back to `json.dumps` with `ensure_ascii=False` and a `default` handler. |
| `loads(s, **kwargs) -> Any` | method | Delegates to `json.loads`. |

### `JSONTag`

| Member | Type | Description |
|--------|------|-------------|
| `check(value) -> bool` | abstract | Whether this tag handles `value`. |
| `to_json(value) -> Any` | abstract | Convert to tagged dict. |
| `to_python(value) -> Any` | abstract | Restore from `__v__` value. |

### Tag Classes

| Class | Tag | `check` | `to_json` | `to_python` |
|-------|-----|---------|-----------|-------------|
| `TagDateTime` | `dt` | `isinstance(value, datetime)` | `isoformat()` | `datetime.fromisoformat(v)` |
| `TagDate` | `d` | `isinstance(value, date) and not isinstance(value, datetime)` | `isoformat()` | `date.fromisoformat(v)` |
| `TagUUID` | `u` | `isinstance(value, uuid.UUID)` | `value.hex` | `uuid.UUID(v)` |
| `TagBytes` | `b` | `isinstance(value, bytes)` | `base64.b64encode(value).decode()` | `base64.b64decode(v.encode())` |
| `TagTuple` | `t` | `isinstance(value, tuple)` | `list(value)` | `tuple(value)` |

### `TaggedJSONSerializer`

| Member | Type | Description |
|--------|------|-------------|
| `tags` | `dict[str, JSONTag]` | Class-level registry of tag name → tag instance. |
| `dumps(obj) -> str` | method | Tag, then `json.dumps`. |
| `loads(s) -> str` | method | `json.loads`, then untag. |
