# Plugin Development

The `chaos` CLI is designed to be minimal and modular. Most functionality is provided through external plugins. This guide covers the basics of creating your own plugin.

A plugin is a standard Python package that uses entry points to register its functionality with `chaos`.

## Project Structure

A basic plugin has the following structure:

```
my-chaos-plugin/
├── pyproject.toml
└── src/
    └── my_chaos_plugin/
        ├── __init__.py
        ├── roles.py
        └── explain.py
```

## `pyproject.toml`

The `pyproject.toml` file is where you define your plugin's metadata and, most importantly, its entry points.

```toml
[project]
name = "my-chaos-plugin"
version = "0.1.0"
description = "A new plugin for Ch-aOS."
requires-python = ">=3.10"

[project.entry-points]
# Entry points are defined here
"chaos.roles" = { my-role = "my_chaos_plugin.roles:my_role_function" }
"chaos.explain" = { my-role = "my_chaos_plugin.explain:MyRoleExplain" }
"chaos.aliases" = { mr = "my-role" }
"chaos.keys" = { my-role = "my_chaos_plugin.roles:my_role_keys" }
"chaos.providers" = { myprovider = "my_chaos_plugin.providers:MyProviderClass" }
```

## Entry Points

Ch-aOS uses several entry point groups to discover plugin functionality.

### `chaos.roles`

This is the most important entry point. It registers a **role** that can be executed with `chaos apply`.

-   **Key:** The name of the role tag (e.g., `my-role`).
-   **Value:** A string pointing to a Python function in the format `path.to.module:function_name`.

This function will be called by `chaos` and should contain your `pyinfra` operations.

**Example `roles.py`:**
```python
from pyinfra.operations import server

def my_role_function(state, host, chobolo_path, skip_confirm):
    """
    A simple role that ensures a directory exists.
    """
    # In a real role, you would load data from the chobolo_path
    # from omegaconf import OmegaConf
    # config = OmegaConf.load(chobolo_path)
    # my_dirs = config.get('my_role_dirs', [])

    server.dir(
        name="Ensure /tmp/my-role-dir exists",
        path="/tmp/my-role-dir",
        present=True,
        user="root",
        mode="755",
    )
```

### `chaos.explain`

Registers a class that provides documentation for your role, accessible via `chaos explain`.

-   **Key:** The topic name, which should usually match your role's tag (e.g., `my-role`).

-   **Value:** A string pointing to a Python class in the format `path.to.module:ClassName`.

The class should contain methods named `explain_<subtopic>` that return a dictionary with the explanation content.

**Example `explain.py`:**
```python
class MyRoleExplain:
    _order = ['usage'] # Controls the order in `explain my-role.list`

    def explain_my_role(self, detail_level='basic'):
        return {
            'concept': 'My Custom Role',
            'what': 'This role ensures a specific directory exists.',
            'why': 'To demonstrate how to create a Ch-aOS plugin.',
            'how': 'It uses the `server.dir` operation from pyinfra.',
        }

    def explain_usage(self, detail_level='basic'):
        return {
            'concept': 'Usage Example',
            'examples': [{
                'yaml': '# Run the role\nchaos apply my-role'
            }]
        }
```

### `chaos.aliases`

Registers a shorter alias for a role tag.

-   **Key:** The alias (e.g., `mr`).

-   **Value:** The full role tag it points to (e.g., `my-role`).

Now you can run `chaos apply mr` instead of `chaos apply my-role`.

### `chaos.keys`

Registers the configuration keys that your role uses. This allows `chaos init chobolo` to automatically include them in the generated template.

-   **Key:** The name of the role tag (e.g., `my-role`).

-   **Value:** A string pointing to a Python object (usually a list of dictionaries) in the format `path.to.module:object_name`.

**Example `roles.py`:**
```python
# ... (imports and my_role_function)

# This is the object that will be exposed to `chaos init chobolo`
my_role_keys = [{
    'my_role_dirs': [
        '/tmp/dir1',
        '/tmp/dir2',
    ]
}]
```

### `chaos.providers`

Registers a new secret provider. This is a more advanced topic that requires implementing a class that inherits from the base `Provider` class. See **[Plugin Providers](./provider-plugins.md)** for examples.

