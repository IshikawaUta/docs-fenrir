# Plugin System

Fenrir v4.0.0 introduces a production-ready plugin system for extending the framework with modular, reusable components.

## Overview

The plugin system provides:

- **Version Compatibility**: Plugins declare compatible Fenrir versions
- **Dependency Resolution**: Automatic ordering with circular dependency detection
- **Config Validation**: Schema-based configuration validation
- **Hot-Reload**: Enable/disable plugins at runtime
- **Auto-Discovery**: Find plugins via entry points
- **Health Monitoring**: Track plugin status and health
- **Namespace Isolation**: Prevent naming conflicts between plugins
- **Thread Safety**: Safe for concurrent access

## Creating a Plugin

```python
from fenrir.plugins import Plugin

class MyPlugin(Plugin):
    name = "my-plugin"
    version = "1.0.0"
    description = "My awesome Fenrir plugin"
    
    # Dependencies on other plugins
    requires = ["auth-plugin"]
    optional = ["cache-plugin"]
    
    # Version compatibility
    min_fenrir_version = "4.0.0"
    max_fenrir_version = "5.0.0"
    
    def setup(self, app, config):
        """Called when plugin is loaded."""
        self.app = app
        self.config = config
        # Register routes, middleware, etc.
        
    def teardown(self):
        """Called when plugin is unloaded."""
        pass
        
    def health_check(self):
        """Return health status."""
        return {"status": "healthy", "plugin": self.name}
```

## Registering Plugins

### Direct Registration

```python
from fenrir import Fenrir
from fenrir.plugins import PluginRegistry

app = Fenrir()
registry = PluginRegistry(app)

# Register a plugin
registry.register(MyPlugin())

# Register with config
registry.register(MyPlugin(), config={"api_key": "secret"})
```

### Auto-Discovery via Entry Points

```python
# In your plugin's pyproject.toml:
[project.entry-points."fenrir.plugins"]
my_plugin = "my_package:MyPlugin"

# In the app:
registry.discover()  # Finds all plugins via entry points
```

## Plugin Registry

```python
from fenrir.plugins import PluginRegistry

app = Fenrir()
registry = PluginRegistry(app)

# Register plugins
registry.register(PluginA())
registry.register(PluginB())

# Enable/disable
registry.enable("plugin-a")
registry.disable("plugin-b")

# Get plugin object
plugin = registry.get("plugin-a")

# List all plugins with status
for name, info in registry.list_plugins().items():
    print(f"{name}: enabled={info['enabled']}, version={info['version']}")
```

## Dependency Resolution

Plugins are loaded in dependency order:

```python
class AuthPlugin(Plugin):
    name = "auth"
    requires = []  # No dependencies

class AdminPlugin(Plugin):
    name = "admin"
    requires = ["auth"]  # Depends on auth plugin

class DashboardPlugin(Plugin):
    name = "dashboard"
    requires = ["auth", "admin"]  # Depends on both
```

Circular dependencies are detected and raise an error:

```python
class PluginA(Plugin):
    name = "a"
    requires = ["b"]  # Circular!

class PluginB(Plugin):
    name = "b"
    requires = ["a"]  # Circular!
```

## Config Validation

```python
from fenrir.plugins import Plugin

class MyPlugin(Plugin):
    name = "my-plugin"
    
    config_schema = {
        "api_key": {"type": "str", "required": True},
        "timeout": {"type": "int", "default": 30},
        "debug": {"type": "bool", "default": False},
    }
    
    def setup(self, app, config):
        # config is validated against schema
        self.api_key = config["api_key"]
        self.timeout = config["timeout"]
```

## Health Monitoring

```python
# Check plugin health
health = registry.get_plugin_health("my-plugin")
print(health.status)      # "healthy"
print(health.uptime)      # 3600

# Plugin also provides its own health_check method
plugin = registry.get("my-plugin")
status = plugin.health_check()
print(status)  # {"status": "healthy", "plugin": "my-plugin"}
```

## Thread Safety

The plugin registry uses `threading.RLock` for safe concurrent access:

```python
import threading

# Safe to call from multiple threads
registry.register(PluginA())  # Thread 1
registry.enable("plugin-a")   # Thread 2
registry.disable("plugin-a")  # Thread 3
```
