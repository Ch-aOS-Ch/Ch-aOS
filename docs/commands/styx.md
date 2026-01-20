# Command `chaos styx`

The `chaos styx` command is used to manage and interact with the Styx service, which is a method in which you can interact with Ch-aOS' plugin registry.

This command allows you to install (`invoke`), list (`list`), and remove (`destroy`) plugins that extend the functionality of Ch-aOS.

## Usage
```bash
chaos styx <action> [plugin_name]
```

- `<action>`: The operation you want to perform. It can be one of the following:

  - `invoke`: Install a plugin.

  - `list`: List all installed plugins.

  - `destroy`: Remove an installed plugin.

## Sending a Plugin to Styx

Styx is NOT a end all be all plugin registry. It is simple by design and only meant to _install, uninstall and list_ plugins, it does not manage dependencies or versions.

If you have created a plugin that depends on another plugin, or a specific version of a plugin, you will need to rethink how your plugin is designed to avoid these issues.

Plugins in Ch-aOS should be as self contained as possible, in order to avoid dependency hell scenarios.

That being said, if you have created a plugin in Ch-aOS, and would like to share it with the community via Styx, please open a PR on the [Styx GitHub repository](https://github.com/Ch-aOS-Ch/styx)

It is quite simply a dict of dicts in a yaml file with the following structure:
```yaml
styx: # global dict
  chaos-dots: # name of your plugin
    name: chaos-dots # name that you builded you plugin with
    repo: https://github.com/Ch-aOS-Ch/chaos-dots # the git repo where your plugin is hosted
    about: "A Ch-aotic dotfile manager, full with declarativity and statefulness" # a brief description about your plugin
    version: "v0.1.1" # the version of your plugin, cannot be "latest", be specific
```

## About security:

ATTENTION, THIS IS IMPORTANT.

ALL styx plugins NEED to be reviewed by a member of the "Reviewers Styx" team and be open source in order to be added to the styx registry.

ALL plugins should be submitted with a proper LICENSE file, and a proper SECURITY.md file.

ALL plugins should be added with a SIGNED COMMIT AND PR. No Plugins will be accepted without such.

All plugins are installed via the repo url provided in the styx registry, only installed inside of a user's home directory and only downloades a .whl file with the "this_name-version-py3-none-any.whl" format.

All plugins are installed in the user's home directory, and should have documentation about if they require elevated permissions OR if they require secrets access.

The main branch of the repo is always protected, and all PRs are reviewed before being merged (the repo is public, so anyone can review PRs) (ONLY exception are plugins created by the Ch-aOS team themselves).
