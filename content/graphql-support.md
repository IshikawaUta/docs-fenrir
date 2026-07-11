# GraphQL Support

Fenrir v4.1.2 includes built-in GraphQL support via strawberry-graphql.

## Overview

The GraphQL integration provides:

- **strawberry-graphql**: Modern Python GraphQL library
- **GraphiQL Playground**: Interactive GraphQL IDE
- **Type Safety**: Full Python type hints
- **Async Support**: Async resolvers

## Setup

### Installation

```bash
pip install fenrir-framework[graphql]
```

### Basic Setup

```python
from fenrir import Fenrir
from fenrir.graphql import GraphQLRouter
import strawberry

# Define types
@strawberry.type
class User:
    id: int
    name: str
    email: str

@strawberry.type
class Query:
    @strawberry.field
    def users(self) -> list[User]:
        return [
            User(id=1, name="John", email="john@example.com"),
            User(id=2, name="Jane", email="jane@example.com"),
        ]
    
    @strawberry.field
    def user(self, id: int) -> User | None:
        users = {
            1: User(id=1, name="John", email="john@example.com"),
            2: User(id=2, name="Jane", email="jane@example.com"),
        }
        return users.get(id)

# Create schema
schema = strawberry.Schema(query=Query)

# Create router
graphql_router = GraphQLRouter(schema)

# Mount to app
app = Fenrir()
graphql_router.mount(app, path="/graphql")
```

## Querying

### Basic Query

```graphql
query {
  users {
    id
    name
    email
  }
}
```

### Query with Arguments

```graphql
query {
  user(id: 1) {
    id
    name
    email
  }
}
```

## Mutations

```python
@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_user(self, name: str, email: str) -> User:
        # Create user logic
        return User(id=3, name=name, email=email)
    
    @strawberry.mutation
    def delete_user(self, id: int) -> bool:
        # Delete user logic
        return True

schema = strawberry.Schema(query=Query, mutation=Mutation)
```

### Mutation Example

```graphql
mutation {
  createUser(name: "Bob", email: "bob@example.com") {
    id
    name
    email
  }
}
```

## Subscriptions

```python
import strawberry
from typing import AsyncGenerator

@strawberry.type
class Subscription:
    @strawberry.subscription
    async def count(self, target: int = 10) -> AsyncGenerator[int, None]:
        for i in range(target):
            yield i
            await asyncio.sleep(1)

schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)
```

## GraphiQL Playground

Access the interactive GraphQL IDE at `/graphql`:

```
http://localhost:8000/graphql
```

The GraphiQL playground provides:

- Syntax highlighting
- Auto-completion
- Query history
- Documentation explorer

## Advanced Usage

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | `strawberry.Schema` | **required** | The Strawberry GraphQL schema |
| `path` | `str` | `"/graphql"` | URL path for the GraphQL endpoint |
| `graphiql` | `bool` | `True` | Enable GraphiQL playground |
| `introspection` | `bool` | `True` | Enable schema introspection |
| `max_depth` | `int` | `10` | Maximum query depth |
| `context_factory` | `Callable` | `None` | Custom context factory (sync/async callable) |

### Custom Scalar Types

```python
import strawberry
from datetime import datetime

@strawberry.scalar
class DateTime:
    @staticmethod
    def serialize(value: datetime) -> str:
        return value.isoformat()
    
    @staticmethod
    def parse_value(value: str) -> datetime:
        return datetime.fromisoformat(value)
```

### Context

```python
@strawberry.type
class Query:
    @strawberry.field
    def current_user(self, info) -> User:
        request = info.context["request"]
        # Access request context
        return get_current_user(request)
```
