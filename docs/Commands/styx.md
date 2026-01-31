# Command `chaos styx`

The `chaos styx` command is used to manage and interact with the Styx plugin registry.

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

If you have created a plugin in Ch-aOS, and would like to share it with the community via Styx, please open a PR on the [Styx GitHub repository](https://github.com/Ch-aOS-Ch/styx)

It is quite simply a dict of dicts in a yaml file with the following structure:
```yaml
styx: # global dict
  chaos-dots: # name of your plugin
    name: chaos-dots # name that you builded you plugin with
    repo: https://github.com/Ch-aOS-Ch/chaos-dots # the git repo where your plugin is hosted
    about: "A Ch-aotic dotfile manager, full with declarativity and statefulness" # a brief description about your plugin
    version: "v0.1.1" # the version of your plugin, cannot be "latest", be specific
```

!!! important
    Styx was _created_ to be simple, it is NOT a package manager. It was created from the start to be as simple as possible (either you have the plugin, or not), it is a _plugin registry_, managed and contributed by the community. There should NOT be a "chaos-utils" inside of styx, since plugins should be auto contained solutions. All of the tools for creating an auto contained solution for Ch-aOS are available and should be used. _PyPI managed utilities_ are not only recommended, they are the correct way to distribute an utils package for styx plugins. Plugins may use any PyPI package, but it is required to have undergone an "pip-audit" run before the styx installation.

## About security:

ATTENTION, THIS IS IMPORTANT.

ALL styx plugins NEED to be reviewed by a member of the "Reviewers Styx" team and be open source in order to be added to the styx registry.

ALL plugins should be submitted with a proper LICENSE file, and a proper SECURITY.md file.

ALL plugins should be added with a SIGNED COMMIT AND PR. No Plugins will be accepted without such.

All plugins are installed via the repo url provided in the styx registry only download a .whl file with the "this_name-version-py3-none-any.whl" format.

All plugins are installed in the user's home directory, and should have documentation about if they require elevated permissions OR if they require secrets access.

The main branch of the repo is always protected, and all PRs are reviewed before being merged (the repo is public, so anyone can review PRs) (ONLY exception are plugins created by the Ch-aOS team themselves).
