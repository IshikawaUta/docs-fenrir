# gRPC Support

Fenrir v4.1.2 includes built-in gRPC support for building high-performance RPC services.

## Overview

The gRPC integration provides:

- **GRPCServer**: Thread-based gRPC server
- **GRPCService**: Service definition with handlers
- **GRPCClient**: Client for calling gRPC services
- **Interceptors**: Request/response interceptors
- **Health Checking**: Built-in health check service

## Setup

### Installation

```bash
pip install fenrir-framework[grpc]
```

### Basic Setup

```python
from fenrir import Fenrir
from fenrir.grpc import GRPCServer, GRPCService

# Define a service
class UserService(GRPCService):
    service_name = "user"
    
    async def get_user(self, request, context):
        return {"id": 1, "name": "John"}
    
    async def create_user(self, request, context):
        return {"id": 2, "name": request.get("name")}

# Create server
grpc_server = GRPCServer()

# Add service
grpc_server.add_service(UserService())

# Mount to Fenrir app
app = Fenrir()
grpc_server.mount(app, port=50051)
```

## Defining Services

```python
from fenrir.grpc import GRPCService

class OrderService(GRPCService):
    service_name = "order"
    
    async def get_order(self, request, context):
        order_id = request.get("id")
        # Fetch order logic
        return {"id": order_id, "status": "pending"}
    
    async def create_order(self, request, context):
        # Create order logic
        return {"id": 1, "status": "created"}
    
    async def list_orders(self, request, context):
        # List orders logic
        return {"orders": [{"id": 1}, {"id": 2}]}
```

## GRPCContext

```python
class MyService(GRPCService):
    service_name = "my"
    
    async def my_handler(self, request, context):
        # Access metadata
        metadata = context.metadata
        
        # Set status
        context.set_code(OK)
        
        # Set details
        context.set_details("Success")
        
        return {"result": "ok"}
```

## Interceptors

```python
from fenrir.grpc import GRPCInterceptor

class LoggingInterceptor(GRPCInterceptor):
    async def intercept(self, method: str, request, context):
        print(f"Method: {method}, Request: {request}")
        response = await method(request, context)
        print(f"Response: {response}")
        return response

# Add interceptor
grpc_server = GRPCServer(interceptors=[LoggingInterceptor()])
```

## Health Checking

```python
from fenrir.grpc import GRPCServer

server = GRPCServer()

# Health check is automatically available
# Check health: grpc_health_probe -addr=localhost:50051
```

## Client Usage

```python
from fenrir.grpc import GRPCClient

# Create client
async with GRPCClient("localhost:50051") as client:
    # Connection established
    pass
```

## Server Lifecycle

```python
# Start server
grpc_server.start(host="0.0.0.0", port=50051)

# Stop server gracefully
grpc_server.stop(grace=5.0)

# Check if running
print(grpc_server.is_running)  # True/False
```
