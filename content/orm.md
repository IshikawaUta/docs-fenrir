# Lightweight ORM

Fenrir v4.1.2 includes a lightweight async ORM for SQLite and PostgreSQL databases.

## Overview

The ORM provides:

- **SQLite & PostgreSQL**: Support for both databases
- **Model with Metaclass**: Declarative model definition
- **Field Types**: Integer, String, Float, Boolean, Datetime, JSON
- **QuerySet**: Chainable queries with filters, ordering, limit, offset
- **SQL Injection Prevention**: Parameterized queries throughout
- **Async Support**: Fully async database operations

## Database Setup

```python
from fenrir.orm import Database

# SQLite
db = Database("sqlite:///app.db")

# PostgreSQL
db = Database("postgresql://user:pass@localhost/dbname")

# Connect before using
await db.connect()
```

## Defining Models

```python
from fenrir.orm import Model, fields

class User(Model):
    __tablename__ = "users"
    
    id = fields.Integer(primary_key=True)
    username = fields.String(max_length=100, unique=True)
    email = fields.String(max_length=255)
    age = fields.Integer(default=0)
    is_active = fields.Boolean(default=True)
    created_at = fields.Datetime(auto_now_add=True)
    metadata = fields.JSONField(default=dict)

class Post(Model):
    __tablename__ = "posts"
    
    id = fields.Integer(primary_key=True)
    title = fields.String(max_length=200)
    content = fields.Text()
    author_id = fields.Integer(foreign_key="users.id")
    published = fields.Boolean(default=False)
```

## CRUD Operations

### Create

```python
# Create a new user
user = await User.create(
    username="john",
    email="john@example.com",
    age=25
)

# Bulk create
users = await User.bulk_create([
    {"username": "alice", "email": "alice@example.com"},
    {"username": "bob", "email": "bob@example.com"},
])
```

### Read

```python
# Get by ID
user = await User.get(id=1)

# Filter
active_users = await User.filter(is_active=True)

# Complex queries
users = await User.filter(
    age__gte=18,
    is_active=True
).order_by("username").limit(10).offset(0)

# Get or create
user, created = await User.get_or_create(
    username="john",
    defaults={"email": "john@example.com"}
)
```

### Update

```python
# Update single user
await User.filter(id=1).update(email="new@example.com")

# Bulk update
await User.filter(is_active=False).update(is_active=True)
```

### Delete

```python
# Delete by ID
await User.delete(id=1)

# Bulk delete
await User.filter(is_active=False).delete()
```

## QuerySet Methods

```python
# Chaining
queryset = User.filter(is_active=True)
queryset = queryset.order_by("-created_at")
queryset = queryset.limit(10)
queryset = queryset.offset(20)

# Aggregation
count = await User.filter(is_active=True).count()
exists = await User.filter(username="john").exists()
```

## Field Types

```python
fields.Integer(primary_key=True)      # Auto-increment integer
fields.Integer(default=0)             # Integer with default
fields.String(max_length=100)         # VARCHAR(100)
fields.Text()                         # TEXT
fields.Float(default=0.0)            # FLOAT
fields.Boolean(default=False)        # BOOLEAN
fields.Datetime(auto_now_add=True)   # Auto-set on create
fields.Datetime(auto_now=True)       # Auto-set on update
fields.JSONField(default=dict)       # JSON object
```

## Database Operations

```python
# Execute raw SQL
result = await db.execute("SELECT * FROM users WHERE id = ?", [1])

# Fetch all
rows = await db.fetch_all("SELECT * FROM users")

# Fetch one
row = await db.fetch_one("SELECT * FROM users WHERE id = ?", [1])

# Disconnect
await db.disconnect()
```
