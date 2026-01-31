# Ch-aOS Roles Plugin Documentation

In Ch-aOS, roles are basically just a bunch of pyinfra scripts that get executed on your servers. So why document this? Well, there are a lot of tips, tricks and best practices that can help you get the most out of roles. This documentation will cover everything you need to know about using roles in Ch-aOS.

## First of all

Ch-aOS utilizes Pyinfra's [API mode](https://docs.pyinfra.com/en/3.x/api/reference.html) to manage infrastructure. This means that roles have full access to all of Python's libraries and features, not relying solely on pyinfra's built-in functionality. This allows for more complex logic and operations within roles.

Be sure to use only `host.get_fact` or `add_op` to run commands directly on the host. This approach lets Ch-aOS use Pyinfra's internal Topological Sorter to determine the correct order of operations, ensuring that dependencies are handled properly. It also allows Ch-aOS to properly track changes, reports, commands and everything on the [Logbook](../advanced/logbook.md).

## How to declare a role

Just add it to your pyproject.toml like so:
```toml
[project.entry-points."chaos.roles"]
my-role = "my_chaos_plugin.roles:my_role_function"
```
Then, in your `roles.py` file, define the role function:
```py
my_role_functoin(state, host, chobolo_path, skip_confirm): # If you need secrets access, add the "secrets_dict" param
                                                           # It comes pre-loaded, so you can just use it (and this avoids you deleting it)
  ...
```

## Tips and Tricks

So, best practices out of the way, lets get into some... hacky stuff.

Want to run a command _immediately_ on the host, without using `add_op` in order to avoid the Topo Sort or even just avoid Race conditions? Use `host.get_fact(Command, 'your command here')` to run arbitrary commands on the host. This is useful for things like checking if a service is running before trying to start it, or getting the current state of a configuration file, or even cloning a git repo before trying to manage it (Trust me, I've experienced this pain first hand when trying to do a declarative dotfiles manager).

If you are making a trully declarative role, you can use `host.get_fact` to check the current state of the host, compare it to the desired state, and then use `add_op` with `server.shell` to make necessary changes. `server.shell` allows you to run arbitrary shell commands on the host, without needing to get the current state first, since you already have it from `host.get_fact`, you can just run the command to change the state, this is particularly useful for managing not only what to _add_, but also what to _remove_ from the host. This is called "declarative idempotency through delta calculation".

Want to manage files on the host? Use `host.get_fact(File)` to get the current state of a file, and then use `add_op` with `server.file` to manage the file. You can use this to ensure that a file has the correct permissions, ownership, and content. You can also use this to manage directories and symlinks.

Other use cases are mostly covered entirely by Pyinfra, so be sure to check them out. This place is where I'll keep most of the specific workarounds and tricks that I've found useful while working with Ch-aOS roles.
