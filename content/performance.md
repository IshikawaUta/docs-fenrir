# Performance & orjson

Fenrir v4.1.2 includes a performance optimization module and uses orjson for fast JSON serialization.

## Overview

Performance features include:

- **orjson**: 7x faster JSON serialization than stdlib json
- **ObjectPool**: Reusable object pooling
- **ResponseCache**: Cache responses to avoid recomputation
- **PerformanceMonitor**: Track request latencies
- **optimize_app()**: Apply optimizations to your app

## orjson Integration

Fenrir uses orjson for all JSON operations:

```python
from fenrir.json import json_dumps, json_loads, json_dumps_bytes

# Serialize to JSON string
data = {"name": "John", "age": 25}
json_str = json_dumps(data)  # '{"name":"John","age":25}'

# Deserialize from JSON
parsed = json_loads(json_str)  # {"name": "John", "age": 25}

# Serialize to JSON bytes (for responses)
json_bytes = json_dumps_bytes(data)  # b'{"name":"John","age":25}'
```

### Performance Comparison

| Operation | stdlib json | orjson | Speedup |
|-----------|-------------|--------|---------|
| 10000 dumps | 1652ms | 233ms | **7x** |
| 10000 loads | 1200ms | 180ms | **6.7x** |

## ObjectPool

Reuse expensive objects:

```python
from fenrir.performance import ObjectPool

# Create pool
pool = ObjectPool(
    create_func=lambda: expensive_object(),
    max_size=10,
    min_size=2
)

# Acquire object
obj = await pool.acquire()

# Use object
result = await obj.do_something()

# Release back to pool
await pool.release(obj)

# Or use context manager
async with pool.acquire() as obj:
    result = await obj.do_something()
```

## ResponseCache

Cache responses:

```python
from fenrir.performance import ResponseCache

# Create cache
cache = ResponseCache(max_size=1000, ttl=300)

# Cache response
await cache.set("/api/users", response)

# Get cached response
cached = await cache.get("/api/users")

# Clear cache
await cache.clear()
```

## PerformanceMonitor

Track request latencies (import from submodule):

```python
from fenrir.performance import PerformanceMonitor

# Create monitor
monitor = PerformanceMonitor(max_latencies=1000)

# Record latency
monitor.record("/api/users", 0.05)  # 50ms

# Get stats
stats = monitor.get_stats("/api/users")
print(stats)  # {"avg": 0.05, "min": 0.01, "max": 0.1, "count": 100}

# Get all stats
all_stats = monitor.get_all_stats()
```

## optimize_app()

Apply all optimizations:

```python
from fenrir import Fenrir
from fenrir.performance import optimize_app

app = Fenrir()

# Apply optimizations
optimize_app(app)
```

## Best Practices

### Use Connection Pooling

```python
from fenrir.pool import ConnectionPool

pool = ConnectionPool(
    create_func=lambda: create_connection(),
    close_func=lambda conn: conn.close(),
    min_size=2,
    max_size=10
)

async with pool.acquire() as conn:
    result = await conn.execute(query)
```

### Cache Expensive Operations

```python
from fenrir.cache import MemoryCache

cache = MemoryCache(max_size=1000)

async def get_expensive_data(key):
    # Try cache first
    cached = await cache.get(key)
    if cached:
        return cached
    
    # Compute expensive result
    result = await compute_expensive_data()
    
    # Cache result
    await cache.set(key, result, ttl=300)
    
    return result
```

### Use Streaming for Large Data

```python
from fenrir.response import StreamingResponse

async def generate_large_data():
    for i in range(1000000):
        yield f"Line {i}\n"

@app.get("/stream")
async def stream():
    return StreamingResponse(
        generate_large_data(),
        media_type="text/plain"
    )
```
