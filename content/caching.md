# Caching System

Fenrir v4.4.0 includes a flexible caching system with multiple backends and a unified `Cache` wrapper.

## Overview

The caching system provides:

- **Cache**: Unified interface with decorator support
- **MemoryCache**: In-memory LRU cache with TTL
- **RedisCache**: Redis-backed distributed cache (SCAN, not KEYS)
- **FileCache**: File-based cache with atomic writes and SHA-256 keys
- **Prefix Invalidation**: Invalidate cached entries by prefix via `@cache.invalidate(key_prefix=...)` decorator

## Cache Wrapper (Recommended)

The `Cache` class provides a unified interface with built-in decorator support:

```python
from fenrir.cache import Cache, MemoryCache

# Create cache with default MemoryCache backend
cache = Cache()

# Or with a specific backend
cache = Cache(MemoryCache(max_size=1000))

# Direct operations
await cache.set("key", "value", ttl=60)
value = await cache.get("key")
await cache.delete("key")
exists = await cache.exists("key")
await cache.clear()

# Batch operations
await cache.set_many({"key1": "val1", "key2": "val2"}, ttl=300)
values = await cache.get_many(["key1", "key2"])
```

### Cache Decorator

Automatically cache function results:

```python
from fenrir.cache import Cache, MemoryCache

cache = Cache(MemoryCache())

@cache.cached(ttl=300, key_prefix="users")
async def get_user(user_id: int):
    return await db.get_user(user_id)

# Custom key function
@cache.cached(ttl=60, key_func=lambda user_id: f"user:{user_id}")
async def get_user(user_id: int):
    return await db.get_user(user_id)
```

**Parameters:**

- `ttl`: Time-to-live in seconds (default: `300`)
- `key_prefix`: Prefix for cache keys (default: `""` — uses function qualified name)
- `key_func`: Custom function to generate cache key (default: `None`)

### Cache Invalidation Decorator

Invalidate cache entries after function execution:

```python
@cache.invalidate(key_prefix="users")
async def update_user(user_id: int, data: dict):
    await db.update_user(user_id, data)
    return {"status": "updated"}

# Custom key function
@cache.invalidate(key_func=lambda user_id: f"user:{user_id}")
async def delete_user(user_id: int):
    await db.delete_user(user_id)
```

**Parameters:**

- `key_prefix`: Prefix of keys to invalidate (default: `""`)
- `key_func`: Custom function to generate the key to invalidate (default: `None`)

### Async Context Manager

```python
async with Cache(MemoryCache()) as cache:
    await cache.set("key", "value")
    value = await cache.get("key")
# Backend is automatically closed
```

## MemoryCache

In-memory LRU cache with TTL expiration:

```python
from fenrir.cache import MemoryCache

cache = MemoryCache(max_size=1000)

await cache.set("user:1", {"name": "John"}, ttl=300)
user = await cache.get("user:1")
await cache.delete("user:1")
await cache.clear()
```

## RedisCache

Redis-backed distributed cache using SCAN (not KEYS) for prefix operations:

```python
from fenrir.cache import RedisCache

cache = RedisCache(
    redis_url="redis://localhost:6379",
    prefix="myapp:",
    serializer=None,    # optional custom serializer
    deserializer=None,  # optional custom deserializer
)

await cache.set("user:1", {"name": "John"}, ttl=300)
user = await cache.get("user:1")
```

## FileCache

File-based cache with atomic writes and SHA-256 hashed keys:

```python
from fenrir.cache import FileCache

cache = FileCache(
    cache_dir="/tmp/fenrir_cache",
    ttl=3600
)

await cache.set("user:1", {"name": "John"}, ttl=300)
user = await cache.get("user:1")
```

## Cache-Aside Pattern

```python
cache = Cache(MemoryCache())

async def get_user(user_id):
    cache_key = f"user:{user_id}"
    user = await cache.get(cache_key)
    if user is not None:
        return user

    # Cache miss - fetch from DB
    user = await db.get_user(user_id)
    if user:
        await cache.set(cache_key, user, ttl=300)

    return user
```
