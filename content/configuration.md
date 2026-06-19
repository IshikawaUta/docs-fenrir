# Configuration

Fenrir provides a Flask-style configuration system with a dict-based `Config` class.

## Application Configuration

```python
from fenrir import Fenrir

app = Fenrir(
    title="My Application",
    version="3.1.3",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
```

## Environment-Based Configuration

```python
import os
from fenrir import Fenrir

debug = os.getenv("DEBUG", "False") == "True"
app = Fenrir()
app.debug = debug
```

## Config Class

`Config` is a `dict` subclass that provides methods for loading configuration from various sources.

```python
class Config(dict):
    def __init__(self, root_path: str, defaults: dict = None):
        ...
```

- **`root_path`**: Base directory for resolving relative file paths used by `from_pyfile()` and `from_envvar()`.
- **`defaults`**: Optional dict of initial config values.

## Loading Configuration

### `from_object(obj)`

Load uppercase attributes from an object or a module path string.

```python
class Config:
    DEBUG = True
    TESTING = False
    DATABASE_URL = "postgresql://localhost/mydb"
    SECRET_KEY = "your-secret-key"

app.config.from_object(Config)
```

String form imports the module dynamically:

```python
app.config.from_object("myapp.config.ProductionConfig")
```

### `from_mapping(mapping)`

Load uppercase keys from any `Mapping` or `dict`.

```python
app.config.from_mapping({
    "DEBUG": True,
    "SECRET_KEY": "your-secret-key",
    "DATABASE_URL": "postgresql://localhost/mydb",
})
```

### `from_pyfile(filename, silent=False)`

Execute a Python file and load its uppercase attributes. The file is evaluated in an isolated module namespace.

- **`filename`**: Path to the Python file, resolved relative to `root_path`.
- **`silent`**: If `True`, return `False` on failure instead of raising `OSError`.

```python
app.config.from_pyfile("config.py", silent=True)
```

Example `config.py`:

```python
DEBUG = True
SECRET_KEY = "dev-key"
DATABASE_URL = "sqlite:///app.db"
```

### `from_envvar(variable_name, silent=False)`

Read a file path from an environment variable and call `from_pyfile()` on it.

- **`variable_name`**: Name of the environment variable containing the config file path.
- **`silent`**: If `True`, return `False` on failure instead of raising `RuntimeError`.

```bash
export APP_CONFIG="/etc/myapp/config.py"
```

```python
app.config.from_envvar("APP_CONFIG", silent=True)
```

## Custom Configuration

```python
app = Fenrir()

# Set config values directly
app.config["DEBUG"] = True
app.config["TESTING"] = False
app.config["DATABASE_URL"] = "postgresql://localhost/mydb"
app.config["SECRET_KEY"] = "your-secret-key"

# Load from an object
class Config:
    DEBUG = True
    TESTING = False
    DATABASE_URL = "postgresql://localhost/mydb"
    SECRET_KEY = "your-secret-key"

app.config.from_object(Config)

# Load from a mapping
app.config.from_mapping({
    "DEBUG": True,
    "SECRET_KEY": "your-secret-key",
})

# Load from a Python file
app.config.from_pyfile("config.py", silent=True)

# Load from an environment variable pointing to a config file
app.config.from_envvar("APP_CONFIG_FILE", silent=True)
```

## Config API Reference

### Constructor

**`Config(root_path, defaults=None)`**

- `root_path` (`str`): Base path for resolving relative file paths.
- `defaults` (`dict`, optional): Initial config values.

### Methods

| Method | Description |
|--------|-------------|
| `from_object(obj)` | Load uppercase attributes from an object or module string. |
| `from_mapping(mapping)` | Load uppercase keys from a `Mapping` or `dict`. |
| `from_pyfile(filename, silent=False)` | Load config by executing a Python file. Returns `True` on success. |
| `from_envvar(variable_name, silent=False)` | Load config from the file path in an env var. Returns `True` on success. |
| `get(key, default=None)` | Get a config value (inherited from `dict`). |

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `root_path` | `str` | Base directory for file operations. |

## Default Configuration Values

These defaults are set when a `Fenrir` application is created:

| Key | Default | Description |
|-----|---------|-------------|
| `ENV` | `"production"` | Application environment name. |
| `DEBUG` | `False` | Enable debug mode. |
| `TESTING` | `False` | Enable testing mode. |
| `SECRET_KEY` | `None` | Secret key for signing sessions and tokens. |
| `SESSION_COOKIE_NAME` | `"session"` | Name of the session cookie. |
| `SESSION_COOKIE_DOMAIN` | `None` | Domain scope for the session cookie. |
| `SESSION_COOKIE_PATH` | `"/"` | Path scope for the session cookie. |
| `SESSION_COOKIE_HTTPONLY` | `True` | Restrict cookie to HTTP-only access. |
| `SESSION_COOKIE_SECURE` | `False` | Require HTTPS for the session cookie. |
| `SESSION_COOKIE_SAMESITE` | `None` | SameSite attribute for the session cookie. |

## App Attributes

```python
app.debug                    # bool — debug mode
app.strict_content_type      # bool — require JSON content-type
app.title                    # str — app title
app.version                  # str — app version
app.template_folder          # str — template directory
app.json                     # JSONProvider — JSON serializer
app.renderer                 # BaseTemplateRenderer — template renderer
app.session_interface        # SessionInterface — session backend
app.config                   # Config — configuration object
```
