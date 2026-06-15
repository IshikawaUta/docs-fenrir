# CLI Tools

Fenrir ships with a built-in command-line interface for running servers, inspecting routes, scaffolding projects, and more.

## `fenrir run`

Start a Fenrir application using the Asteri ASGI production server.

```bash
fenrir run <target> [options]
```

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--host` | `-H` | `127.0.0.1` | Host address to bind to |
| `--port` | `-p` | `8000` | Port to serve on |
| `--workers` | `-w` | `1` | Number of worker processes |
| `--dev` | `-d` | `false` | Development mode with auto-reload on file changes |
| `--reload` | | `false` | Restart workers on code changes (same effect as `--dev`) |

The `target` argument specifies the application module and variable in `module:variable` format (e.g. `app:app`), or a direct `.py` file path (e.g. `app.py`).

### Examples

```bash
# Basic usage
fenrir run app:app

# Custom host and port
fenrir run app:app --host 0.0.0.0 --port 8080

# Multiple workers for production
fenrir run app:app -w 4

# Development mode with auto-reload
fenrir run app:app --dev

# Short flags
fenrir run app:app -H 0.0.0.0 -p 9000 -w 2 -d

# Reload on code changes
fenrir run app:app --reload

# Run a file directly
fenrir run app.py --dev
```

### Auto-detection of `app_path`

When calling `app.run()` from within your application code (without the CLI), Fenrir automatically detects the `app_path` by inspecting the caller's stack frame. It reads the caller's `__file__` and `__name__` to resolve the module path, then passes it to the Asteri worker. This means the following works without explicitly passing `app_path`:

```python
from fenrir import Fenrir

app = Fenrir(title="My App")

@app.get("/")
async def index():
    return {"hello": "world"}

if __name__ == "__main__":
    app.run()  # app_path auto-detected from caller frame
```

If auto-detection fails, pass it explicitly:

```python
app.run(app_path="myapp:app")
```

---

## `fenrir routes`

Display all registered HTTP and WebSocket routes for an application in a formatted table.

```bash
fenrir routes <target>
```

| Argument | Description |
|----------|-------------|
| `target` | The app path in `module:app` or `app.py` format |

The output includes the route path, HTTP methods, handler name, and associated blueprint (if any). WebSocket routes are shown with `WEBSOCKET` as the method.

### Examples

```bash
fenrir routes app:app
fenrir routes myapp:application
fenrir routes app.py
```

### Sample Output

```
---------------------------------------------------------------
Path                  Methods     Handler           Blueprint
---------------------------------------------------------------
/                     GET         index             -
/api/users            GET, POST   users_handler     api
/ws                   WEBSOCKET   ws_handler        -
---------------------------------------------------------------
```

---

## `fenrir shell`

Launch an interactive Python shell pre-loaded with your application context.

```bash
fenrir shell <target>
```

| Argument | Description |
|----------|-------------|
| `target` | The app path in `module:app` or `app.py` format |

The shell automatically imports and makes available:

| Name | Description |
|------|-------------|
| `app` | The loaded Fenrir application instance |
| `request` | The Fenrir request object |
| `g` | The Fenrir global context object |
| `Response` | Base response class |
| `JSONResponse` | JSON response class |
| `HTMLResponse` | HTML response class |
| `Blueprint` | Blueprint class |

### Examples

```bash
fenrir shell app:app
fenrir shell myapp.py
```

### Sample Session

```
Fenrir 3.1.2 Interactive Shell
App: My App [/docs]
Available in context: 'app', 'request', 'g', 'Response', 'JSONResponse', 'HTMLResponse', 'Blueprint'
>>> app.title
'My App'
>>> app.version
'3.1.2'
>>> list(app.router.routes)
[<Route GET / >, <Route GET /api/users >]
```

---

## `fenrir bench`

Run an in-memory HTTP benchmark against a route using HTTPX's ASGI transport. No network overhead — requests are processed entirely in-process.

```bash
fenrir bench <target> [options]
```

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--iterations` | `-i` | `1000` | Number of requests per trial |
| `--trials` | `-t` | `5` | Number of trials to run |
| `--path` | `-p` | `/` | The HTTP path to benchmark |
| `--method` | `-m` | `GET` | The HTTP method to use |

Requires `httpx` to be installed (`pip install httpx`).

### Examples

```bash
# Benchmark root path (defaults)
fenrir bench app:app

# 2000 iterations, 5 trials on /api/data with POST
fenrir bench app:app -i 2000 -t 5 -p /api/data -m POST

# Benchmark a specific endpoint
fenrir bench app:app --path /health --method GET --iterations 500 --trials 3
```

### Sample Output

```
Benchmarking GET / (1000 iterations x 5 trials)...
Warming up pipeline...
Running trials...
  Trial 1: 12543.21 rps (elapsed: 0.079712s)
  Trial 2: 12891.55 rps (elapsed: 0.077570s)
  Trial 3: 13012.87 rps (elapsed: 0.076847s)
  Trial 4: 12754.33 rps (elapsed: 0.078404s)
  Trial 5: 12987.44 rps (elapsed: 0.076997s)

========================================
FENRIR BENCHMARK RESULTS
========================================
Target:          GET /
Average RPS:     12837.88 req/sec
Min Latency:     0.074 ms
Max Latency:     0.091 ms
Avg Latency:     0.078 ms
========================================
```

---

## `fenrir new`

Scaffold a new Fenrir project with a complete directory structure and starter files.

```bash
fenrir new <name>
```

| Argument | Description |
|----------|-------------|
| `name` | Name of the new project directory |

The scaffolding creates:

```
<name>/
├── app.py              # Main application with example routes
├── requirements.txt    # fenrir dependency
├── logo.png            # Fenrir logo
├── favicon.ico         # Favicon
├── templates/
│   └── index.html      # Starter HTML template
└── static/
    └── style.css       # Starter CSS file
```

### Examples

```bash
# Create a new project
fenrir new myproject

# Scaffold then run
fenrir new myproject
cd myproject
fenrir run app.py --dev
```

The scaffolded `app.py` includes example routes for serving the homepage, logo, favicon, and a JSON API endpoint.

---

## `fenrir info`

Display system environment information and (optionally) application details.

```bash
fenrir info [target]
```

| Argument | Description |
|----------|-------------|
| `target` | Optional app path in `module:app` or `app.py` format |

When no target is provided, only system environment information is shown. When a target is provided, application details are included.

### Examples

```bash
# System info only
fenrir info

# System + app info
fenrir info app:app
fenrir info myapp.py
```

### Sample Output

```text
=============================================
SYSTEM ENVIRONMENT
=============================================
Fenrir version:      3.1.2
Python version:      3.11.0
Python executable:   /usr/bin/python3
OS Platform:         Linux 6.1.0
Pydantic installed:  Yes (v2.7.0)
Asteri installed:    Yes (v2.3.2)
=============================================
APPLICATION DETAILS
=============================================
App Title:           My App
App Version:         3.1.2
HTTP Routes:         10
WebSocket Routes:    2
Middlewares:         1
Compat Layers Active: None active in process
=============================================
```

The **Compat Layers Active** field shows which framework compatibility layers are loaded in the current process (Flask, FastAPI, Bottle, Falcon, Sanic).

---

## `fenrir monitoring`

Manage the built-in monitoring dashboard for health checks and traffic analysis.

```bash
fenrir monitoring <action>
```

| Action | Description |
|--------|-------------|
| `enable` | Enable the monitoring dashboard |
| `disable` | Disable the monitoring dashboard |
| `status` | Show monitoring configuration status |
| `set-password` | Set a new dashboard password |

### Examples

```bash
# Enable monitoring
fenrir monitoring enable

# Disable monitoring
fenrir monitoring disable

# Check monitoring status
fenrir monitoring status

# Set a new password (interactive prompt)
fenrir monitoring set-password
```

### Environment Variables

Configure monitoring via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MONITORING_ENABLED` | `false` | Enable/disable monitoring |
| `MONITORING_USER` | `admin` | Dashboard username |
| `MONITORING_PASSWORD` | `changeme` | Dashboard password |
| `MONITORING_SECRET_KEY` | (auto-generated) | Secret key for session signing |
| `MONITORING_SITES` | `http://localhost:8000` | Comma-separated list of sites to monitor |
| `MONITORING_CHECK_INTERVAL` | `60` | Health check interval in seconds |

### Default Credentials

- **Username:** `admin`
- **Password:** `changeme`

> **Warning:** Change the default password before deploying to production.

---

## General Notes

### App Target Format

All commands that accept a `target` argument support two formats:

- **Module notation**: `module:variable` — imports `variable` from `module` (e.g. `app:app`, `myapp:application`)
- **File path**: `app.py` — loads the file directly and looks for an `app` attribute (falls back to `application`)

### Version

Check the installed Fenrir version with:

```bash
fenrir --version
```
