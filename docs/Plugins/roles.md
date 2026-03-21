# Ch-aOS Roles Plugin Documentation

In Ch-aOS, roles are Python classes that inherit from our base SDK `Role` class. They leverage Pyinfra's [API mode](https://docs.pyinfra.com/en/3.x/api/reference.html) to orchestrate infrastructure, giving you the full power of Python and OOP. 

So why document this? Well, there are a lot of tips, tricks, and best practices that can help you get the most out of our SDK's Role lifecycle (`get_context`, `delta`, and `plan`). This documentation will cover everything you need to know about developing robust roles in Ch-aOS.

## The SDK Approach

Since Ch-aOS is an SDK, roles are not just procedural scripts; they follow a strict lifecycle to ensure atomicity, clear diffs, and precise logging.

The base `Role` class requires you to implement specific methods to define behavior:

- `get_context()`: Gather data from the host.

- `delta()`: Compare context to desired state.

- `plan()`: Add `pyinfra` operations based on the delta.

By sticking to this lifecycle, you allow the Ch-aOS engine to accurately track changes, report dry-runs, and feed data into the [Logbook](../Advanced/logbook.md).

## How to declare a role

First, add it to your `pyproject.toml` like so:
```toml
[project.entry-points."chaos.roles"]
my-role = "my_chaos_plugin.roles:MyAwesomeRole"
```

Then, in your `roles.py` file, define the role class:
```python
from chaos.lib.roles.role import Role
from chaos.lib.args.dataclasses import Delta, ResultPayload
from pyinfra.operations import server

class MyAwesomeRole(Role):
    def __init__(self):
        # Define the role name and any needed keys or secrets
        super().__init__(
            name="my-role",
            needs_secrets=False,
            necessary_chobolo_keys=["my_role_dirs"]
        )

    def get_context(self, state, host, chobolo: dict = {}, secrets: dict = {}):
        # Fetch current state from the host
        # (e.g., using host.get_fact())
        return {"current_dirs": ["/tmp/existing_dir"]}

    def delta(self, context: dict = {}) -> Delta:
        # Compare current context to your desired Ch-obolo data
        # Return what needs to be added or removed
        return Delta(
            to_add={"dirs": ["/tmp/my-role-dir"]},
            to_remove={}
        )

    def plan(self, state, host, delta: Delta) -> ResultPayload:
        # Execute pyinfra operations based on the delta
        for d in delta.to_add.get("dirs", []):
            add_op(
                state,
                server.dir,
                name=f"Ensure {d} exists",
                path=d,
                present=True,
                user="root",
                mode="755"
            )
        return ResultPayload(success=True, message=["Plan built successfully"])
```

Oh, also, if you're thinking to yourself "damn, do I need to do ALLAT??", fret not my friend, for you can do all of these like so:
```py
from chaos.lib.roles.role import Role

class MySimpleRole(Role):
    def __init__(self):
        super().__init__(name="my-simple-role")

    def plan(self, state, host, delta):
        # Just do everything in the plan if you want!
        # The delta and get_context are optional*
        host.get_fact(...) # Get facts directly in the plan
        add_op(server.shell, ...) # Run operations directly in the plan
        return ResultPayload(success=True, message=["Done!"])
```

There are, however, issues with skipping the lifecycle (for my CLI). First of all, you lose the ability to have accurate diffs in your interface, which means you can't have a clear "this is what will change" report before you run the plan. Second, it makes it harder to debug and test your roles, since you cannot easily isolate the data gathering, diffing and execution phases. Most importantly, Ch-aOS has a way of parallelising operations across hosts, particularly in the `get_context` phase, which means that if you run operations directly in `plan` without using `delta`, you might end up with a poorer performance.

Then again, Ch-aOS is an SDK, everything the CLI does, you can do with your own code, you can do whatever you want! The lifecycle is there to help you, but all the tools are at your disposal if you want to learn how to use them effectively.

## Tips and Tricks

So, best practices out of the way, let's get into some... hacky stuff.

Want to run a command *immediately* on the host, without waiting for the Pyinfra Topological Sorter to run operations? Use `host.get_fact(Command, 'your command here')` inside of your `get_context` method. This is useful for checking if a service is running before trying to start it, getting the current state of a configuration file, or cloning a git repo before trying to manage it.

!!! warning
    be careful when using this, as it may break idempotency.

If you are making a truly declarative role, the `delta` method is your best friend. By calculating the exact differences (what to add, what to remove) before you ever reach `plan`, you enable true "declarative idempotency". Then, inside `plan`, you simply iterate over your `delta.to_add` and `delta.to_remove` dictionaries and map them to `server.shell` or `server.file` operations.

Want to manage files on the host? Use `host.get_fact(File)` inside `get_context` to read the current state of a file, calculate differences in `delta`, and use `server.file` in `plan` to ensure it has the correct permissions, ownership, and content.

Other use cases are mostly covered entirely by Pyinfra, so be sure to check them out. This place is where I'll keep most of the specific workarounds and tricks that I've found useful while working with Ch-aOS roles!
