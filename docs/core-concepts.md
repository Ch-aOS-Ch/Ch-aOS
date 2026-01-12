# Core Concepts

Ch-aOS is built on a few core concepts that work together to provide a powerful and flexible system management experience.

## Ch-obolos: The Data

A "Ch-obolo" is a YAML file where you declare the desired state of your system. It serves as the single source of truth, containing the **data** that roles will use to configure the system.

**Key Idea:** Ch-obolos strictly separate data (what you want) from roles (logic) (how to achieve it).

This makes your configurations:
-   **Readable:** All your variables are in one place, not scattered around a massive file.
-   **Reusable:** Use the same roles with different Ch-obolo files for different systems.
-   **Version-Controllable:** Track changes to your system's desired state using Git.

You can specify a Ch-obolo file with the `-c` flag or set a default path using `chaos set chobolo`.

### Example Ch-obolo

```yaml
# ch-obolo.yml
hostname: "my-arch-box"

users:
  - name: "dex"
    shell: "zsh"
    sudo: True
    groups:
      - wheel
      - docker

packages:
  - git
  - neovim
aurPkgs:
  - google-chrome
```

## Roles: The Logic

A "Role" is a Python script that contains the **logic** for achieving a desired state. Roles read data from your Ch-obolo (and from your secrets) file and use the `pyinfra` library to execute operations.

When you run `chaos apply <role_tag>`, Ch-aOS finds the corresponding role from its installed plugins and executes it. The role first gathers "facts" about the system's current state, compares it to the desired state from the Ch-obolo, and then applies the necessary changes.

This modular approach allows you to apply specific parts of your configuration independently. For example, you can run `chaos apply users` to only manage users without affecting packages or services.

## Plugins: The Functionality

Ch-aOS is designed to be minimal and modular. Most of its functionality is provided through external plugins. The `chaos` CLI itself is just an engine; the plugins provide the REAL power.

There are several types of plugins:

-   **Cores**: A "core" is a plugin that provides the basic set of roles for managing a specific Linux distribution. For example, `Ch-aronte` is the core for Arch Linux, providing roles like `users`, `pkgs`, `services`, etc.
-   **Functionality Plugins**: These plugins add specialized tools. For example, `chaos-dots` is a plugin for managing dotfiles.
-   **Secret Providers**: These plugins integrate with external password managers like Bitwarden or 1Password to securely fetch encryption keys.
-   **Explanations**: These plugins add documentation and explanations for various roles, concepts, or anything really, accessible via the `chaos explain` command.
-   **Keys**: These plugins add boiler plate for `chaos init chobolo`, in order to help users get started faster with pre-defined configurations for specific use cases.
-   **Aliases**: These plugins add shortcuts to chaos roles (kinda basic ik).

??? quote "Hey, hey you there, I've got a secret to tell you"
    Ch-aOS will have more types of plugins in the futures, chec k the [Chopping Board](chopping-board.md) for planned features!

This plugin-based architecture means you only install the functionality you need, and it allows the community to extend Ch-aOS for different distributions or use cases without modifying the central CLI, also, since it's made using a pyproject structure, one plugin can easily implement 2 or more types of plugins!
