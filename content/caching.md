# Caching System

Fenrir v4.1.2 includes a flexible caching system with multiple backends.

## Overview

The caching system provides:

- **MemoryCache**: In-memory LRU cache with TTL
- **RedisCache**: Redis-backed distributed cache
- **FileCache**: File-based cache with atomic writes
- **Prefix Invalidation**: Invalidate cached entries by prefix via `@cache.invalidate(key_prefix=...)` decorator
- **orjson Serialization**: Fast JSON serialization

## MemoryCache

```python
from fenrir.cache import MemoryCache

# Create cache with 1000 max entries
cache = MemoryCache(max_size=1000)

# Set with TTL (seconds)
await cache.set("user:1", {"name": "John"}, ttl=300)

# Get
user = await cache.get("user:1")

# Delete
await cache.delete("user:1")

# Clear all
await cache.clear()
```

## RedisCache

```python
from fenrir.cache import RedisCache

# Create Redis cache
cache = RedisCache(
    redis_url="redis://localhost:6379",
    prefix="myapp:"
)

# Set with TTL
await cache.set("user:1", {"name": "John"}, ttl=300)

# Get
user = await cache.get("user:1")
```

## FileCache

```python
from fenrir.cache import FileCache

# Create file cache
cache = FileCache(
    cache_dir="/tmp/fenrir_cache",
    ttl=3600
)

# Set with TTL
await cache.set("user:1", {"name": "John"}, ttl=300)

# Get
user = await cache.get("user:1")
```

## Usage Patterns

### Cache Decorator

```python
from functools import wraps

def cached(ttl=300, prefix=""):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            result = await cache.get(cache_key)
            if result is not None:
                return result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl=ttl)
            return result
        return wrapper
    return decorator

@cached(ttl=60, prefix="users")
async def get_user(user_id):
    return await User.get(id=user_id)
```

### Cache Invalidation

```python
# Invalidate specific key
await cache.delete("user:1")

# Invalidate all
await cache.clear()

# Invalidate all
await cache.clear()
```

### Cache-Aside Pattern

```python
async def get_user(user_id):
    # Try cache first
    cache_key = f"user:{user_id}"
    user = await cache.get(cache_key)
    if user:
        return user
    
    # Cache miss - fetch from DB
    user = await User.get(id=user_id)
    if user:
        await cache.set(cache_key, user, ttl=300)
    
    return user
```
