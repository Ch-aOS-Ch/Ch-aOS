# Welcome to the Ch-aOS Project Suite

**Ch-aOS** is a suite of tools designed to declaratively manage your Unix system, from initial installation to post-install configuration. It provides a modular, safe, and didactic way to handle your entire setup.

## Core Principles

- **Declarative**: Define the desired state of your system using simple YAML files. The `chaos` CLI takes care of the rest, ensuring your system matches your declaration.
- **Modular**: Extend the functionality of Ch-aOS by creating or adding plugins. Whether you need to manage a different distribution, handle dotfiles, or integrate with a new secret provider, the plugin system makes it possible.
- **Safe**: Preview changes before they are applied with dry runs. Manage your secrets securely with integrated support for `sops` and various secret providers.
- **Didactic**: Learn as you go with a built-in documentation system. The `chaos explain` command provides detailed information on every feature, command, and concept.

## How It Works

The `chaos` CLI is the engine of the project, powered by Python, Pyinfra, and OmegaConf. It uses "Ch-obolos" (YAML files) to read data and executes "roles" (Python scripts) to apply the desired state to your system. This strict separation of data from logic makes your configurations readable, reusable, and version-controllable.

Ready to get started? Head over to the **[Getting Started](getting-started.md)** guide.

Want to learn more about advanced features? Check some of the **[Advanced Topics](advanced/providers.md)**!

Want to create your own plugins? Dive into the **[Plugin Development](plugins/development.md)** documentation!

Or you just want to follow the code's planned features? Check out our **[Chopping Board](./chopping-board.md)**!
