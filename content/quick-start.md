# Quick Start

Create a simple `app.py` file:

```python
from fenrir import Fenrir

# Initialize the application
app = Fenrir(title="My First Application", version="4.1.0")

# FastAPI-style routing
@app.get("/")
async def home():
    # Return a simple JSON welcome message
    return {"message": "Welcome to Fenrir!"}

# With path parameters
@app.get("/users/<user_id:int>")
async def get_user(user_id: int):
    return {"user_id": user_id, "name": "John Doe"}

# Falcon-style class-based resource
class ItemResource:
    async def on_get(self, req, resp, item_id: int):
        resp.media = {"item_id": item_id, "status": "active"}

app.add_route("/items/<item_id:int>", ItemResource())

if __name__ == "__main__":
    # Run with: fenrir run app:app
    # Or: python app.py
    app.run()
```

Run the application:

```bash
fenrir run app:app
# or
python app.py
```

Access the application:

- **App**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
