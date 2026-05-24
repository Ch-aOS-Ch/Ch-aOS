# Soul Development

Ch-aOS is designed to be a powerful SDK and an extensible CLI. Most functionality is provided through external Souls. This guide covers the basics of creating your own Soul.

A Soul is a standard Python package that uses `entry_points` to register its classes and functionality with the Ch-aOS engine.

## Project Structure

A basic Soul has the following structure:

```
my-chaos-soul/
├── pyproject.toml
└── src/
    └── my_chaos_soul/
        ├── __init__.py
        ├── roles.py
        └── explain.py
```

## `pyproject.toml`

The `pyproject.toml` file is where you define your Soul's metadata and, most importantly, its entry points.

```toml
[project]
name = "my-chaos-soul"
version = "0.1.0"
description = "A new Soul for Ch-aOS."
requires-python = ">=3.10"

[project.entry-points]
# Entry points are defined here
"chaos.roles" = { my-role = "my_chaos_soul.roles:MyRoleClass" }
"chaos.explain" = { my-role = "my_chaos_soul.explain:MyRoleExplain" }
"chaos.aliases" = { mr = "my-role" }
"chaos.keys" = { my-role = "my_chaos_soul.roles:my_role_keys" }
"chaos.providers" = { myprovider = "my_chaos_soul.providers:MyProviderClass" }
"chaos.boats" = { myboat = "my_chaos_soul.boats:MyBoatClass" }
"chaos.limanis" = { mylimani = "my_chaos_soul.limanis:MyLimaniClass" }
```

## Entry Points

Ch-aOS uses several entry point groups to discover Soul functionality.

### `chaos.roles`

This is the most important entry point. It registers a **Role** class that can be executed with `chaos apply`.

-   **Key:** The name of the role tag (e.g., `my-role`).

-   **Value:** A string pointing to a Python class in the format `path.to.module:ClassName`.

This class must inherit from `chaos.lib.roles.role.Role` and implement the SDK lifecycle methods.

**Example `roles.py`:**
```python
from chaos.lib.roles.role import Role
from chaos.lib.args.dataclasses import Delta, ResultPayload
from pyinfra.operations import server

class MyRoleClass(Role):
    def __init__(self):
        super().__init__(name="my-role", necessary_chobolo_keys=["my_role_dirs"])

    def plan(self, state, host, delta: Delta) -> ResultPayload:
        """
        A simple role that ensures directories exist based on delta.
        """
        for d in delta.to_add.get("dirs", []):
            server.dir(
                name=f"Ensure {d} exists",
                path=d,
                present=True,
                user="root",
                mode="755",
            )
        return ResultPayload(success=True)
```
*(For a more detailed explanation of `get_context` and `delta`, see [Roles Soul Documentation](./roles.md))*

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
            'why': 'To demonstrate how to create a Ch-aOS soul using the SDK.',
            'how': 'It utilizes the Role class lifecycle and pyinfra operations.',
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
# This is the object that will be exposed to `chaos init chobolo`
my_role_keys = [{
    'my_role_dirs': [
        '/tmp/dir1',
        '/tmp/dir2',
    ]
}]
```

### `chaos.providers`

Registers a new secret provider class. See **[Provider Souls](./provider-plugins.md)** for examples.

### `chaos.boats`

Registers a new boat for use with `chaos apply --fleet`. See **[Boat Souls](../Advanced/boats.md)** for more details.

### `chaos.limanis`

Enables a new database to use with `chaos apply --logbook --limani`. See **[Limani Souls](./limani.md)** for more information.
